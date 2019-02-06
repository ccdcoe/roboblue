import logging
import os.path as path

from dxlclient.client_config import DxlClientConfig
from dxlclient.service import ServiceRegistrationInfo
from redis import Redis

from robobluekit import Application
from robobluekit.monitor import MonitoringContext
from robobluekit.dxl import MonitorableDxlClient, DxlClientMonitor
from robobluekit.kit import ServiceEndpointMonitor, InvalidConfigException

from .config import ServiceConfig
from .endpoint import SERVICE_ENDPOINTS

logger = logging.getLogger(__name__)


class ReputationService:
    """
    The service instance itself, encapsulates the endpoint receivers and connections
    """
    def __init__(self, dxl_config, config, monitoring_context):
        self.dxl_conn = MonitorableDxlClient(dxl_config, monitoring_context.register(DxlClientMonitor('connection')))
        self.__config = config
        self.__monitoring_ctx = monitoring_context
        self.redis_conn = None

    def __register_service(self):
        registration = ServiceRegistrationInfo(self.dxl_conn, self.__config.type)
        for name, constructor in SERVICE_ENDPOINTS:
            topic = '{}/{}'.format(self.__config.type, name)
            registration.add_topic(topic,
                                   constructor(
                                       self.__monitoring_ctx.register(ServiceEndpointMonitor('endpoint.' + topic)),
                                       self))
        self.dxl_conn.register_service_sync(registration, 2)

    def initialize(self):
        self.dxl_conn.connect()
        redis_cfg = self.__config.redis_config
        self.redis_conn = Redis(
            host=redis_cfg.hostname, port=redis_cfg.port, db=redis_cfg.db, ssl=redis_cfg.use_ssl, socket_timeout=1)
        self.__register_service()

    def destroy(self):
        self.dxl_conn.disconnect()
        # Redis takes care of itself


class ReputationApplication(Application):
    """
    Application for the Roboblue reputation service
    """

    def __init__(self):
        self.service_config = None
        self.dxl_config = None
        self.__svc = None
        Application.__init__(self)

    def register_arguments(self):
        logger.debug('registering arguments')

        self.add_argument(
            '--dxl-config',
            help='location of the DXL client configuration file',
            metavar='PATH_TO_FILE',
            default='./config/dxlclient.config'
        )

        self.add_argument(
            '--service-config',
            help='location of the service specific configuration file',
            metavar='PATH_TO_FILE',
            default='./config/dxlreputation.config'
        )

    def load_configuration(self):
        logger.debug('loading configuration')

        logger.debug('loading dxl client configuration from %s', path.abspath(self.args.dxl_config))
        self.dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)

        logger.debug('loading service specific configuration from %s', path.abspath(self.args.service_config))
        self.service_config = ServiceConfig(self.args.service_config)

    def initialize(self):
        self.__svc = ReputationService(self.dxl_config, self.service_config, self.monitoring_context)
        self.__svc.initialize()

    def reload(self):
        logger.info('dxlclient configuration loading from: {}'.format(path.abspath(self.args.dxl_config)))
        logger.info('dxlreputation configuration loading from: {}'.format(path.abspath(self.args.service_config)))

        try:
            new_dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)
            new_svc_config = ServiceConfig(self.args.service_config)
        except InvalidConfigException as e:
            logger.error('failed config reload: invalid service configuration')
            logger.error('service configuration error: ' + str(e))
        except BaseException as e:
            logger.error('failed config reload: invalid DXL client configuration')
            logger.error('dxlclient configuration error: ' + str(e))
        else:
            try:
                logger.info('began swapping out the running dxlreputation service')
                new_monitoring_context = MonitoringContext()

                new_svc = ReputationService(new_dxl_config, new_svc_config, new_monitoring_context)

                new_svc.initialize()
                self.__svc.destroy()

                self.__svc = new_svc
                self.dxl_config = new_dxl_config
                self.service_config = new_svc_config
                self.monitoring_context = new_monitoring_context

            except BaseException as e:
                logger.error('failed to swap out dxlreputation with reloaded configuration: {}'.format(e.message))
            else:
                logger.info('reloaded dxlreputation with new configuration')

    def destroy(self):
        self.__svc.destroy()
