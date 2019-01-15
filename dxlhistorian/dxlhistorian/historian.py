import logging

from dxlclient.client import DxlClient
from dxlclient.message import Event
from dxlclient.callbacks import EventCallback

from .config import HistorianConfig
from .recorder import Recorder

logger = logging.getLogger(__name__)


class RecordingCallback(EventCallback):
    """
        The recording callback receives the incoming event and records it to a more permanent storage for future
        use
    """

    def __init__(self, recorder):
        # type: (Recorder) -> None
        EventCallback.__init__(self)
        self.__recorder = recorder

    def on_event(self, event):
        # type: (Event) -> None
        logger.debug('received event %s from the service fabric', event.message_id)
        try:
            self.__recorder.record(event)
        except BaseException as e:
            logger.error('failed logging event %s due to error: %s', event.message_id, e.message)


class Historian:
    """
        Historian is the class encapsulating a single instance of the Historian listening for events being sent
        on the OpenDXL fabric
    """

    # DXLClient for communicating with the service fabric
    __dxl = None

    # Instance responsible for handling messages it has received
    __recorder = None

    def __init__(self, config, dxl, recorder):
        # type: (HistorianConfig, DxlClient, Recorder) -> None
        self.__config = config
        self.__dxl = dxl
        self.__recorder = recorder

    def start(self):
        self.__dxl.connect()
        logger.info('connected dxlhistorian to service fabric')
        callback = RecordingCallback(self.__recorder)
        for topic in self.__config.subscribe_to:
            self.__dxl.add_event_callback(topic, callback)
            logger.info("subscribed dxlhistorian to topic %s", topic)

    def stop(self):
        logger.info("disconnecting dxlhistorian from service fabric")
        self.__dxl.disconnect()
