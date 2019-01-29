import logging
import threading
import time

from dxlclient.service import ServiceRegistrationInfo
from dxlclient.callbacks import RequestCallback
from dxlclient.message import Request, Response, ErrorResponse

import google.protobuf.json_format as json_format
from grr_api_client.connectors.http_connector import HttpConnector, Error
from grr_api_client.utils import TypeUrlToMessage
import grr_api_client.errors as grr_errors
from grr_response_proto.api.reflection_pb2 import ApiMethod
from werkzeug.routing import BuildError

from robobluekit.monitor import Monitor
from robobluekit.kit import format_timestamp

logger = logging.getLogger(__name__)


class DispatcherMonitor(Monitor):
    """
    Monitor implementation to monitor request dispatchers
    """

    def __init__(self, name):
        self.__lock = threading.Lock()
        self.__first_request = None
        self.__latest_request = None
        self.__request_count = 0
        self.__error_count = 0  # Internal errors
        self.__in_error = False
        Monitor.__init__(self, name)

    def register_request(self):
        """
        Register the receipt of a new DXL request message
        :return: None
        """
        with self.__lock:
            now = time.time()
            if self.__first_request is None:
                self.__first_request = now
            self.__latest_request = now
            self.__request_count += 1

    def register_success(self):
        """
        Register the successful processing of a DXL request
        :return: None
        """
        with self.__lock:
            self.__in_error = False

    def register_error(self):
        """
        Register an internal error that occurred within the service
        :return: None
        """
        with self.__lock:
            self.__in_error = True
            self.__error_count += 1

    @property
    def healthy(self):
        return not self.__in_error

    def report_status(self):
        return {
            'first_request_received': format_timestamp(self.__first_request),
            'latest_request_received': format_timestamp(self.__latest_request),
            'request_count': self.__request_count,
            'error_count': self.__error_count
        }


class Dispatcher(RequestCallback):
    """
    Dispatcher takes an incoming OpenDXL service fabric service request, makes a request to the GRR API and responds
    with the response it received
    """

    def __init__(self, endpoint, board, monitor):
        # type: (ApiMethod, SwitchBoard, DispatcherMonitor) -> None
        self.__endpoint = endpoint
        self.__args = None
        # If the endpoint excepts input, create a constructor function to return an empty PB message type
        if endpoint.args_type_descriptor.default.type_url != '':
            self.__args = lambda: TypeUrlToMessage(endpoint.args_type_descriptor.default.type_url)
        self.__board = board
        self.__monitor = monitor
        RequestCallback.__init__(self)

    def on_request(self, request):
        # type: (Request) -> None
        self.__monitor.register_request()
        response = Response(request)
        try:
            args = None
            if self.__args is not None:  # If input's expected, try parsing the incoming JSON
                args = json_format.Parse(request.payload, self.__args())
            grrr = self.__board.grr.SendRequest(self.__endpoint.name, args=args)
            if grrr is not None:
                response.payload = json_format.MessageToJson(grrr)
        except (json_format.ParseError, BuildError, grr_errors.Error) as e:
            # Failed to compose request or otherwise bad request
            response = ErrorResponse(request, 400, 'invalid request: {}'.format(str(e)))
        except Error as e:  # Connector error
            logger.error('error reaching the GRR instance: {}'.format(str(e)))
            response = ErrorResponse(request, 503, 'failed processing request: {}'.format(str(e)))
        except Exception as e:  # Generic internal error
            logger.exception('%s: %s', type(e).__name__, str(e))
            response = ErrorResponse(request, 500, 'failed processing request: {}'.format(str(e)))
        finally:
            if isinstance(response, ErrorResponse) and response.error_code >= 500:
                # Error count doesn't include client errors
                self.__monitor.register_error()
            else:
                self.__monitor.register_success()
            self.__board.dxlc.send_response(response)


class SwitchBoard:
    """
    Switchboard handles the Dispatchers responsible for wrapping the various HTTP endpoints
    """

    def __init__(self, config, dxl_conn, register_monitor):
        self.dxlc = dxl_conn
        self.__config = config
        self.grr = HttpConnector(api_endpoint=config.http_endpoint, auth=config.auth)
        self.__endpoints = None
        self.__register_monitor = register_monitor

    def __register_service(self):
        """
        Create dispatchers for each endpoint provided by the GRR API and register the service with the OpenDXL service
        fabric
        :return: None
        """
        svc = ServiceRegistrationInfo(self.dxlc, self.__config.service_type)
        for endpoint in self.__endpoints:
            topic = self.__config.service_type + '/' + endpoint.name
            svc.add_topic(topic,
                          Dispatcher(endpoint, self, self.__register_monitor(DispatcherMonitor('endpoints.' + topic))))
        self.dxlc.register_service_sync(svc, 5)

    def __load_endpoints(self):
        """
        Retrieve the list of available endpoints from the GRR instance
        :return: None
        """
        # Load all endpoints that aren't binary streams
        self.__endpoints = filter(
            # The number 2 there indicates bit streams
            lambda x: x.result_kind != 2,  # Bit of magic, but that Enum doesn't seem to be available
            self.grr.SendRequest('ListApiMethods', args=None).items
        )

    def initialize(self):
        self.dxlc.connect()
        self.__load_endpoints()
        self.__register_service()

    def destroy(self):
        self.dxlc.disconnect()
