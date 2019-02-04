import json
import logging

import requests
from dxlclient.callbacks import RequestCallback
from dxlclient.message import Response, ErrorResponse
from dxlclient.service import ServiceRegistrationInfo

from robobluekit.dxl import MonitorableDxlClient
from robobluekit.kit import ServiceEndpointMonitor
from robobluekit.monitor import MonitoringContext

from .config import ServiceConfig, EndpointConfig

logger = logging.getLogger(__name__)


class Dispatcher(RequestCallback):
    """
    Dispatcher takes the incoming request, makes the upstream HTTP request and passes the result back without
    inspecting the upstream response thoroughly. Do note that due to how Wazuh indicates errors, the response
    is inspected to determine whether an error has occurred
    """

    def __init__(self, config, monitor, switch):
        # type: (EndpointConfig, ServiceEndpointMonitor, Switchboard) -> None
        self.__monitor = monitor
        self.__config = config
        self.__switch = switch
        self.__sess = requests.Session()
        self.__sess.auth = config.auth
        self.__sess.verify = config.verify_ssl
        RequestCallback.__init__(self)

    def __construct_url(self, incoming):
        """
        Put together the URL from its parts and replace any variables
        :param incoming: url fragments
        :return: URL string
        """
        def mapper(s):
            if s[0] == ':':  # indicates named variable
                tmp = incoming[s[1:]]
                del incoming[s[1:]]
                return str(tmp)
            return s

        return '/'.join(map(mapper, self.__config.url))

    def on_request(self, request):
        self.__monitor.register_request()
        response = Response(request)
        try:
            req = json.loads(request.payload)
            args = {
                'method': self.__config.type,
                'url': self.__construct_url(req)
            }

            # Determine how to treat the rest of the parameters based on the request type
            if self.__config.type == 'get':
                args['params'] = req
            else:
                args['json'] = req

            # Forward on the request and pass the response back
            upstream = self.__sess.request(**args)

            if upstream.status_code >= 400:
                response = ErrorResponse(request, upstream.status_code, upstream.text)
            else:
                try:
                    # Errors aren't always indicated with the proper HTTP status code, may need to inspect
                    res = upstream.json()
                    if res['error'] != 0:
                        response = ErrorResponse(request, res['error'], upstream.text)
                    else:
                        response.payload = upstream.text
                except (ValueError, KeyError):
                    response = ErrorResponse(request, 504, 'Invalid upstream response')
        except ValueError:
            response = ErrorResponse(request, 400, 'request payload must be a well formed JSON string')
        except KeyError as e:
            response = ErrorResponse(request, 400, 'missing required parameter {} from payload'.format(str(e)))
        except Exception as e:
            logger.exception('unknown exception of type %s: ' + str(e), type(e).__name__)
            response = ErrorResponse(request, 500, 'unknown internal error: ' + str(e))
        finally:
            if isinstance(response, ErrorResponse) and 500 <= response.error_code < 600:
                # Error count doesn't include client errors
                self.__monitor.register_error()
            else:
                self.__monitor.register_success()
            self.__switch.dxl.send_response(response)


class Switchboard:
    """
    The switchboard's responsible for managing a set of dispatchers to ensure proper data flow
    """

    def __init__(self, dxl_client, config, monitoring_context):
        # type: (MonitorableDxlClient, ServiceConfig, MonitoringContext) -> None
        self.dxl = dxl_client
        self.__config = config
        self.__monitoring_ctx = monitoring_context

    def initialize(self):
        self.dxl.connect()

        service_reg = ServiceRegistrationInfo(self.dxl, self.__config.type)
        # Register the endpoints that the service provides
        for endpoint in self.__config.endpoints:
            topic = '{}/{}'.format(self.__config.type, endpoint.name)
            monitor = self.__monitoring_ctx.register(ServiceEndpointMonitor('endpoints.{}'.format(topic)))
            service_reg.add_topic(topic, Dispatcher(endpoint, monitor, self))

        self.dxl.register_service_sync(service_reg, 2)

    def destroy(self):
        self.dxl.disconnect()
