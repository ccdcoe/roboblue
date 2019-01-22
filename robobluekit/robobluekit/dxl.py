from dxlclient import DxlClient
from dxlclient import _on_connect, _on_disconnect
import threading
import time

from .monitor import Monitor
from .kit import format_timestamp


class DxlClientMonitor(Monitor):
    """
    Monitor implementation responsible for keeping an eye on the DXL client
    """

    def __init__(self, name):
        self.__initial_conn = None
        self.__latest_conn = None
        self.__latest_dc = None
        self.__lock = threading.Lock()
        self.client = None
        Monitor.__init__(self, name)

    @property
    def healthy(self):
        return self.client.connected if self.client is not None else None

    def record_connection(self):
        with self.__lock:
            now = time.time()
            if self.__initial_conn is None:
                self.__initial_conn = now
            self.__latest_conn = now

    def record_disconnection(self):
        with self.__lock:
            self.__latest_dc = time.time()

    def report_status(self):
        return {
            'initial_connection': format_timestamp(self.__initial_conn),
            'latest_connection': format_timestamp(self.__latest_conn),
            'latest_disconnection': format_timestamp(self.__latest_dc)
        }


class MonitorableDxlClient(DxlClient):
    """
    A DxlClient that can have a monitor attached to itself and report on some events by rudely overriding some
    of the callbacks given to the underlying MQTT client.
    """

    def __init__(self, config, monitor):
        DxlClient.__init__(self, config)
        self.__monitor = monitor
        monitor.client = self

        # Not a nice thing to do, but for monitoring purposes we need to tinker with some internal callbacks in order
        # to wrap them with calls to the monitor
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        self.__monitor.record_connection()
        _on_connect(client, userdata, flags, rc)

    def on_disconnect(self, client, userdata, rc):
        self.__monitor.record_disconnection()
        _on_disconnect(client, userdata, rc)
