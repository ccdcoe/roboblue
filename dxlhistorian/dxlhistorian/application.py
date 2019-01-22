import os.path as path
import logging

from dxlclient.client_config import DxlClientConfig

from robobluekit import Application
from robobluekit.dxl import MonitorableDxlClient, DxlClientMonitor
from robobluekit.kit import InvalidConfigException
from robobluekit.monitor import MonitoringContext

from .config import HistorianConfig
from .historian import Historian
from .recorder import initialize_recorder, RecorderMonitor

logger = logging.getLogger(__name__)


class HistorianApplication(Application):
    """
    Implementation of the Application as defined in the Roboblue kit for the Historian application

    """

    def __init__(self):
        Application.__init__(self)
        self.__dxl_config = None
        self.__historian_config = None
        self.__historian = None

    def register_arguments(self):
        logger.debug('registering CLI arguments')
        self.add_argument(
            '--dxl-config',
            help='Location of the dxl client configuration file',
            metavar='PATH_TO_FILE',
            default='./config/dxlclient.config'
        )

        self.add_argument(
            '--service-config',
            help='Location of the service specific configuration file',
            metavar='PATH_TO_FILE',
            default='./config/dxlhistorian.config'
        )

    @staticmethod
    def initialize_historian(dxl_config, historian_config, register_monitor):
        """
        Static helper function to initialize a new Historian instance

        :param dxl_config: Configuration of the OpenDXL Client
        :param historian_config: Service specific configuration
        :param register_monitor: function for registering monitors with the monitoring context
        :return: The prepared Historian instance
        """

        logger.debug('initializing new dxlhistorian instance')

        # Client's responsible for connecting to the mesh
        dxl_client = MonitorableDxlClient(dxl_config, register_monitor(DxlClientMonitor('connection')))

        # The recorder performs actions on the received Events
        recorder_type, recorder_conf = historian_config.recorder_config
        recorder = initialize_recorder(recorder_type, recorder_conf,
                                       register_monitor(RecorderMonitor('recorder.{}'.format(recorder_type))))

        return Historian(historian_config, dxl_client, recorder, register_monitor)

    def load_configuration(self):
        logger.debug('loading dxl client configuration from %s', path.abspath(self.args.dxl_config))
        self.__dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)
        logger.debug('loading historian configuration from %s', path.abspath(self.args.service_config))
        self.__historian_config = HistorianConfig(self.args.service_config)

    def initialize(self):
        self.__historian = HistorianApplication.initialize_historian(
            self.__dxl_config, self.__historian_config, self.monitoring_context.register
        )
        self.__historian.start()

    def reload(self):

        logger.info('dxlclient configuration loading from: {}'.format(path.abspath(self.args.dxl_config)))
        logger.info('dxlhistorian configuration loading from: {}'.format(path.abspath(self.args.service_config)))

        try:
            new_dxl_config = DxlClientConfig.create_dxl_config_from_file(self.args.dxl_config)
            new_svc_config = HistorianConfig(self.args.service_config)
        except InvalidConfigException as e:
            logger.error('failed config reload: invalid service configuration')
            logger.error('service configuration error: {}'.format(e.message))
        except BaseException as e:
            logger.error('failed config reload: invalid DXL client configuration')
            logger.error('dxlclient configuration error: {}'.format(e.message))
        else:
            try:
                logger.info('began swapping out the running dxlhistorian')
                new_monitoring_context = MonitoringContext()
                new_historian = HistorianApplication.initialize_historian(
                    new_dxl_config, new_svc_config, new_monitoring_context.register
                )

                new_historian.start()
                self.__historian.stop()

                self.__historian = new_historian
                self.__dxl_config = new_dxl_config
                self.__historian_config = new_svc_config
                self.monitoring_context = new_monitoring_context

            except BaseException as e:
                logger.error('failed to swap out dxlhistorian with reloaded configuration: {}'.format(e.message))
            else:
                logger.info('reloaded dxlhistorian with new configuration')

    def destroy(self):
        self.__historian.stop()
