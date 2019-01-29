import logging
import os.path as path

from dxlclient.client_config import DxlClientConfig

from robobluekit import Application
from robobluekit.monitor import MonitoringContext
from robobluekit.kit import InvalidConfigException
from robobluekit.dxl import MonitorableDxlClient, DxlClientMonitor

from .config import GRRConfig
from .switchboard import SwitchBoard

logger = logging.getLogger(__name__)


class GRRApplication(Application):
    """
    Implementation of the Robobluekit Application interface
    """

    def __init__(self):
        self.switch = None
        self.dxl_config = None
        self.svc_config = None
        Application.__init__(self)

    @staticmethod
    def make_switchboard(dxl_config, svc_config, register_monitor):
        """
        Helper function to construct a monitored Switchboard instance
        :param dxl_config: OpenDXL client configuration
        :param svc_config: GRR service configuration
        :param register_monitor: function to register monitors with the larger monitoring context
        :return: A Switchboard instance
        """
        dxl_client = MonitorableDxlClient(dxl_config, register_monitor(DxlClientMonitor('connection')))
        return SwitchBoard(svc_config, dxl_client, register_monitor)

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
            default='./config/dxlgrr.config'
        )

    def load_configuration(self):
        logger.debug('loading dxl client configuration from %s', path.abspath(self.args.dxl_config))
        self.dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)

        logger.debug('loading service configuration from %s', path.abspath(self.args.service_config))
        self.svc_config = GRRConfig(self.args.service_config)

    def initialize(self):
        self.switch = GRRApplication.make_switchboard(self.dxl_config, self.svc_config,
                                                      self.monitoring_context.register)
        self.switch.initialize()

    def reload(self):
        logger.info('dxlclient configuration loading from: {}'.format(path.abspath(self.args.dxl_config)))
        logger.info('dxlgrr configuration loading from: {}'.format(path.abspath(self.args.service_config)))

        try:
            new_dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)
            new_svc_config = GRRConfig(self.args.service_config)
        except InvalidConfigException as e:
            logger.error('failed config reload: invalid service configuration')
            logger.error('service configuration error: ' + str(e))
        except BaseException as e:
            logger.error('failed config reload: invalid DXL client configuration')
            logger.error('dxlclient configuration error: ' + str(e))
        else:
            try:
                logger.info('began swapping out the running dxlgrr service')
                new_monitoring_context = MonitoringContext()

                new_svc = GRRApplication.make_switchboard(new_dxl_config, new_svc_config,
                                                          new_monitoring_context.register)

                new_svc.initialize()
                self.switch.destroy()

                self.switch = new_svc
                self.dxl_config = new_dxl_config
                self.svc_config = new_svc_config
                self.monitoring_context = new_monitoring_context

            except BaseException as e:
                logger.error('failed to swap out dxlgrr with reloaded configuration: {}'.format(e.message))
            else:
                logger.info('reloaded dxlgrr with new configuration')

    def destroy(self):
        self.switch.destroy()
