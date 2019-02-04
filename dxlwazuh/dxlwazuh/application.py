import logging
import json
import os.path as path

from dxlclient.client_config import DxlClientConfig

from robobluekit import Application
from robobluekit.kit import InvalidConfigException
from robobluekit.monitor import MonitoringContext
from robobluekit.dxl import MonitorableDxlClient, DxlClientMonitor

from .config import ServiceConfig, EndpointConfig
from .switchboard import Switchboard

logger = logging.getLogger(__name__)

# Location of the Apidoc generated api_data.json file
API_DOC_DATA_FILE = path.join(path.dirname(__file__), 'api_data.json')


class WazuhApplication(Application):

    def __init__(self):
        Application.__init__(self)
        self.dxl_config = None
        self.service_config = None
        self.__sb = None

    @staticmethod
    def __provision_switchboard(dxl_config, svc_config, monitoring_context):
        # type: (DxlClientConfig, ServiceConfig, MonitoringContext) -> Switchboard
        dxl_client = MonitorableDxlClient(dxl_config, monitoring_context.register(DxlClientMonitor('connection')))
        return Switchboard(dxl_client, svc_config, monitoring_context)

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
            default='./config/dxlwazuh.config'
        )

    def load_configuration(self):
        logger.debug('loading dxl client configuration from %s', path.abspath(self.args.dxl_config))
        self.dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)

        logger.debug('loading service configuration from %s', path.abspath(self.args.service_config))
        self.service_config = ServiceConfig(self.args.service_config)

        # Load the available endpoints and make them part of the service configuration
        logger.debug('loading endpoint configuration from %s', path.abspath(API_DOC_DATA_FILE))
        endpoints = json.load(open(API_DOC_DATA_FILE, 'r'))
        for endpoint in endpoints:
            self.service_config.endpoints.append(
                EndpointConfig(endpoint['type'], endpoint['name'], endpoint['url'].split('/')[1:], self.service_config)
            )

    def initialize(self):
        self.__sb = WazuhApplication.__provision_switchboard(self.dxl_config, self.service_config,
                                                             self.monitoring_context)
        self.__sb.initialize()

    def reload(self):
        logger.info('dxlclient configuration loading from: {}'.format(path.abspath(self.args.dxl_config)))
        logger.info('dxlwazuh configuration loading from: {}'.format(path.abspath(self.args.service_config)))

        try:
            new_dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)
            new_svc_config = ServiceConfig(self.args.service_config)
            # Clone the endpoint list, but replace their parent
            new_svc_config.endpoints = map(lambda x: x.clone(new_svc_config), self.service_config.endpoints)
        except InvalidConfigException as e:
            logger.error('failed config reload: invalid service configuration')
            logger.error('service configuration error: ' + str(e))
        except BaseException as e:
            logger.error('failed config reload: invalid DXL client configuration')
            logger.error('dxlclient configuration error: ' + str(e))
        else:
            try:
                logger.info('began swapping out the running dxlwazuh service')
                new_monitoring_context = MonitoringContext()

                new_svc = WazuhApplication.__provision_switchboard(new_dxl_config, new_svc_config,
                                                                   new_monitoring_context)

                new_svc.initialize()
                self.__sb.destroy()

                self.__sb = new_svc
                self.dxl_config = new_dxl_config
                self.service_config = new_svc_config
                self.monitoring_context = new_monitoring_context

            except BaseException as e:
                logger.error('failed to swap out dxlwazuh with reloaded configuration: {}'.format(e.message))
            else:
                logger.info('reloaded dxlwazuh with new configuration')

    def destroy(self):
        self.__sb.destroy()
