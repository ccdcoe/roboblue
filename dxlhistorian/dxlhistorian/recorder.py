import base64
import logging
import time
import json
import threading

from dxlclient.message import Event
from elasticsearch import Elasticsearch, TransportError, ElasticsearchException

from robobluekit import Monitor
from robobluekit.kit import format_timestamp

from .config import RECORDER_STDOUT, RECORDER_ELASTICSEARCH, RecorderConfig

logger = logging.getLogger(__name__)


class RecorderMonitor(Monitor):

    def __init__(self, name):
        self.__lock = threading.Lock()
        self.__in_error = False
        self.__last_error = None
        self.__last_error_ts = None
        self.__started = None
        Monitor.__init__(self, name)

    @property
    def healthy(self):
        return not self.__in_error

    def report_status(self):
        return {
            'started': format_timestamp(self.__started),
            'latest_error': {
                'timestamp': format_timestamp(self.__last_error_ts),
                'message': self.__last_error
            }
        }

    def record_start(self):
        self.__started = time.time()

    def record_success(self):
        with self.__lock:
            self.__in_error = False

    def record_error(self, message):
        with self.__lock:
            self.__in_error = True
            self.__last_error = message
            self.__last_error_ts = time.time()


class Recorder:
    """
        Recorder is the interface used to recording incoming events
    """

    def __init__(self, _, monitor):
        monitor.record_start()

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

    def __init__(self, config, monitor):
        self.__esc = Elasticsearch(config.hosts)
        self.__idx = config.index
        self.__monitor = monitor
        Recorder.__init__(self, config, monitor)

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

        try:
            doc = {
                'destination_topic': event.destination_topic,
                'payload': base64.b64encode(event.payload),
                'deserialized_payload': payload,
                'received': format_timestamp(time.time())  # ES takes long ms level epoch timestamps
            }

            self.__esc.index(self.__idx, self.__DOCUMENT_TYPE, doc, id=event.message_id)
            logger.debug('recorded event %s', event.message_id)
            self.__monitor.record_success()
        except TransportError as e:
            self.__monitor.record_error(e.error)
            raise ElasticsearchException(e.error)
        except ElasticsearchException as e:
            self.__monitor.record_error(e.message)
            raise


def initialize_recorder(name, config, monitor):
    # type: (str, RecorderConfig, RecorderMonitor) -> Recorder
    """
    Initializes a new instance of a recorder ready for use

    :param name: Name of the requested recorder
    :param config: Configuration object to be passed
    :param monitor: Recorder monitor to monitor the recorder
    :return: Recorder implementation instance
    """
    recorder = {RECORDER_ELASTICSEARCH: ESRecorder, RECORDER_STDOUT: STDOUTRecorder}[name](config, monitor)
    if recorder.requires_initialization:
        recorder.initialize()
    return recorder
