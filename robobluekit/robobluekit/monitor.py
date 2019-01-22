from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import threading

logger = logging.getLogger(__name__)


class Monitor:
    """
    A monitor reports information about some aspect of an running system.
    """

    def __init__(self, name):
        self.name = name

    @property
    def healthy(self):
        """
        Report whether or not the system monitored by this Monitor is considered to be in an healthy state
        :return: Boolean indicating health status
        """
        raise NotImplementedError('Requires implementation')

    def report_status(self):
        """
        Put together a JSON serializable status report for the system under monitoring
        :return:
        """
        raise NotImplementedError('Requires implementation')


class MonitoringContext:
    """
    MonitoringContext manages the registration of Monitors and acts as a registry
    """

    def __init__(self):
        self.__monitors = {}

    def register(self, monitor, preserve=True):
        """
        Make a monitor known in the context
        :param monitor: Monitor implementation
        :param preserve: Whether or not to preserve previously registered monitors in case of name clashes
        :return: Returns a registered monitor instance
        """
        # type: (Monitor, bool) -> Monitor
        if preserve and monitor.name in self.__monitors:
            if type(self.__monitors[monitor.name]) == type(monitor):
                # Just give them a pointer at the already existent monitor
                monitor = self.__monitors[monitor.name]
            else:
                raise ValueError('mismatch in monitor types blocks registration in preservation mode')
        else:
            self.__monitors[monitor.name] = monitor
        return monitor

    def unregister(self, name):
        """
        Remove the previously registered monitor from the context
        :param name: String identifying the monitor
        :return: None
        """
        # type: (str) -> None
        if name in self.__monitors:
            del self.__monitors[name]

    def report_status(self):
        """
        Reports the aggregate status retrieved from all registered monitors
        :return: object
        """
        status = {'monitors': {}}
        healthy = True
        for key in self.__monitors:
            target = status['monitors']
            splits = key.split('.')
            if len(splits) > 1:
                for v in splits[:-1]:
                    if v not in target:
                        target[v] = {}
                    target = target[v]
            monitor = self.__monitors[key]
            if healthy:
                # See if the monitor affects aggregate
                healthy = healthy if monitor.healthy is None else monitor.healthy
            mon_status = monitor.report_status()
            if monitor.healthy is not None:
                mon_status['healthy'] = monitor.healthy
            target[splits[-1]] = mon_status

        status['healthy'] = healthy
        return status


class HealthServer:
    """
    HealthServer is a Python HTTP server reporting Health information about the monitored service on the configured
    host and port
    """

    class HTTPD(HTTPServer):
        """
        HTTPD is a custom HTTPServer implementation needed so that the monitoring context can be provided to the
        HTTP request handler responsible for the Health endpoint

        """

        def __init__(self, server_address, request_handler_class, bind_and_activate=True, monitorable=None):
            self.monitorable = monitorable
            HTTPServer.__init__(self, server_address, request_handler_class, bind_and_activate)

        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address, self, self.monitorable.monitoring_context)

    class HealthEndpoint(BaseHTTPRequestHandler):
        """
        HealthEndpoint is a custom HTTP request handler implementation responsible for reporting on the health of the
        application based on the status report provided by the Monitoring context
        """

        def __init__(self, request, client_address, server, monitors):
            self.monitors = monitors
            self.log_message = logger.debug
            self.log_error = logger.error
            BaseHTTPRequestHandler.__init__(self, request, client_address, server)

        def do_GET(self):
            try:
                status = self.monitors.report_status()
                healthy = status.get('healthy')
                content = json.dumps(status)
                self.send_response(200 if healthy else 503)  # indicate unhealthy state
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(content)
            except BaseException as e:
                self.send_response(500)
                logger.error('failed to provide health information: %s', e.message)
                self.wfile.write('Something went wrong')

    def __init__(self, config, monitorable):
        if not hasattr(monitorable, 'monitoring_context') or \
                not isinstance(monitorable.monitoring_context, MonitoringContext):
            raise ValueError('invalid monitoring_context attribute for monitorable')
        self.__httpd = HealthServer.HTTPD(config.httpd_address, HealthServer.HealthEndpoint, True, monitorable)

    def serve(self):
        logger.debug("starting httpd to serve health information")
        httpd_thread = threading.Thread(name="HealthServer", target=lambda: self.__httpd.serve_forever())
        httpd_thread.daemon = True
        httpd_thread.start()
