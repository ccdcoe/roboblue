import base64
import logging
import time
import json

from dxlclient.message import Event
from elasticsearch import Elasticsearch

from .config import RECORDER_STDOUT, RECORDER_ELASTICSEARCH, RecorderConfig

logger = logging.getLogger(__name__)


class Recorder:
    """
        Recorder is the interface used to recording incoming events
    """

    def __init__(self, _):
        pass

    @property
    def requires_initialization(self):
        init_func = getattr(self, "initialize", None)
        return callable(init_func)

    def record(self, event):
        raise NotImplementedError


class STDOUTRecorder(Recorder):
    """
        Basic example recorder implementation that outputs information about the received event to STDOUT
    """

    def record(self, event):
        print 'Received message with id {} on {} (payload: {})'.format(
            event.message_id, event.destination_topic, event.payload.decode()
        )


class ESRecorder(Recorder):
    """
        Recorder implementation that records any received events to the configured Elasticsearch index
    """

    # ES document type name
    __DOCUMENT_TYPE = 'event'

    # The ES index where incoming events will be recorded to
    __idx = ''

    def __init__(self, config):
        Recorder.__init__(self, config)
        self.__esc = Elasticsearch(config.hosts)
        self.__idx = config.index

    def initialize(self):
        # Ensure index exists
        if not self.__esc.indices.exists(self.__idx):
            index_config = {
                'mappings': {
                    'event': {
                        'properties': {
                            'destination_topic': {'type': 'text'},
                            'payload': {'type': 'text'},
                            'deserialized_payload': {'type': 'nested'},
                            'received': {'type': 'date'}
                        }
                    }
                }
            }
            self.__esc.indices.create(self.__idx, body=index_config)

    def record(self, event):
        # type: (Event) -> None
        logger.debug('recording event %s', event.message_id)

        # Try unmarshalling the event before sticking it into storage, might derive additional value from
        # being able to inspect the event in storage
        payload = None
        try:
            payload = json.loads(event.payload)
        except ValueError:
            pass

        doc = {
            'destination_topic': event.destination_topic,
            'payload': base64.b64encode(event.payload),
            'deserialized_payload': payload,
            'received': int(time.time() * 10e3)  # ES takes long ms level epoch timestamps
        }
        self.__esc.index(self.__idx, self.__DOCUMENT_TYPE, doc, id=event.message_id)
        logger.debug('recorded event %s', event.message_id)


def initialize_recorder(name, config):
    # type: (str, RecorderConfig) -> Recorder
    """
    Initializes a new instance of a recorder ready for use

    :param name: Name of the requested recorder
    :param config: Configuration object to be passed
    :return: Recorder implementation instance
    """
    recorder = {RECORDER_ELASTICSEARCH: ESRecorder, RECORDER_STDOUT: STDOUTRecorder}[name](config)
    if recorder.requires_initialization:
        recorder.initialize()
    return recorder
