import logging
import threading
import time

from dxlclient.message import Event
from dxlclient.callbacks import EventCallback

from robobluekit import Monitor
from robobluekit.kit import format_timestamp

from .recorder import Recorder

logger = logging.getLogger(__name__)


class RecordingMonitor(Monitor):

    def __init__(self, name):
        self.__first_receipt = None
        self.__last_receipt = None
        self.__last_size = None
        self.__message_count = 0
        self.__lock = threading.Lock()
        Monitor.__init__(self, name)

    def record_event_receipt(self, event):
        # type: (Event) -> None
        with self.__lock:
            now = time.time()
            if self.__first_receipt is None:
                self.__first_receipt = now
            self.__last_receipt = now
            self.__last_size = len(event.payload)
            self.__message_count += 1

    @property
    def healthy(self):
        return None

    def report_status(self):
        return {
            'first_event_received': format_timestamp(self.__first_receipt),
            'latest_event_received': format_timestamp(self.__last_receipt),
            'latest_event_size': self.__last_size,
            'event_count': self.__message_count,
        }


class RecordingCallback(EventCallback):
    """
        The recording callback receives the incoming event and records it to a more permanent storage for future
        use
    """

    def __init__(self, recorder, monitor):
        # type: (Recorder, RecordingMonitor) -> None
        EventCallback.__init__(self)
        self.__recorder = recorder
        self.__monitor = monitor

    def on_event(self, event):
        # type: (Event) -> None
        logger.debug('received event %s from the service fabric', event.message_id)
        try:
            self.__recorder.record(event)
            self.__monitor.record_event_receipt(event)
        except BaseException as e:
            logger.error('failed recording event %s due to error: %s', event.message_id, e.message)


class Historian:
    """
        Historian is the class encapsulating a single instance of the Historian listening for events being sent
        on the OpenDXL fabric
    """

    def __init__(self, config, dxl, recorder, register_monitor):
        self.__config = config
        self.__dxl = dxl
        self.__recorder = recorder
        self.__register_monitor = register_monitor

    def start(self):
        self.__dxl.connect()
        logger.info('connected dxlhistorian to service fabric')
        for topic in self.__config.subscribe_to:
            callback = RecordingCallback(self.__recorder,
                                         self.__register_monitor(RecordingMonitor('recording.{}'.format(topic))))
            self.__dxl.add_event_callback(topic, callback)
            logger.info("subscribed dxlhistorian to topic %s", topic)

    def stop(self):
        logger.info("disconnecting dxlhistorian from service fabric")
        self.__dxl.disconnect()
