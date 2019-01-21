import ConfigParser
import argparse
import logging
import logging.config
import os.path as path
import signal
import threading

from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig

from .config import HistorianConfig, InvalidConfigException
from .historian import Historian
from .recorder import initialize_recorder

logger = logging.getLogger('dxlhistorian')

# Command line arguments
arg_parser = argparse.ArgumentParser(add_help=True)

arg_parser.add_argument(
    '--dxl-config',
    help='Location of the dxl client configuration file',
    metavar='PATH_TO_FILE',
    default='./config/dxlclient.config'
)

arg_parser.add_argument(
    '--service-config',
    help='Location of the service specific configuration file',
    metavar='PATH_TO_FILE',
    default='./config/dxlhistorian.config'
)

arg_parser.add_argument(
    '--logging-config',
    help='Location of the Python logging module configuration file',
    metavar='PATH_TO_FILE',
    default='./config/logging.config'
)

args = arg_parser.parse_args()

# Enable file based logger configuration if such a file exists
if path.isfile(args.logging_config):
    logging.config.fileConfig(args.logging_config)

shutting_down = threading.Lock()


def interrupt_handler(sig, frame):
    global running_condition
    if shutting_down.acquire(False):  # Ignore rest of the interrupts
        logger.info('received interrupt, shutting down')

        historian.stop()
        running_condition = False


reloading_configuration = threading.Lock()


def reload_configuration(sig, frame):
    global historian

    if not reloading_configuration.acquire(False):
        logger.info('ignoring SIGHUP - reload in progress')
        return None

    logger.info('received SIGHUP - will reload configuration')
    logger.info('dxlclient configuration loading from: {}'.format(path.abspath(args.dxl_config)))
    logger.info('dxlhistorian configuration loading from: {}'.format(path.abspath(args.service_config)))

    try:
        new_dxl_config = DxlClientConfig.create_dxl_config_from_file(args.dxl_config)
        new_svc_config = HistorianConfig(args.service_config)
        if path.isfile(args.logging_config):
            logger.info('logging configuration loading from: {}'.format(path.abspath(args.logging_config)))
            logging.config.fileConfig(args.logging_config)
    except InvalidConfigException as e:
        logger.error('failed config reload: invalid service configuration')
        logger.error('service configuration error: {}'.format(e.message))
    except ConfigParser.Error as e:
        logger.error('failed config reload: invalid logger configuration')
        logger.error('logging configuration error: {}'.format(e.message))
    except BaseException as e:
        logger.error('failed config reload: invalid DXL client configuration')
        logger.error('dxlclient configuration error: {}'.format(e.message))
    else:
        try:
            logger.info('began swapping out the running dxlhistorian')
            new_historian = initialize_historian(new_dxl_config, new_svc_config)
            new_historian.start()
            historian.stop()
            historian = new_historian
        except BaseException as e:
            logger.error('failed to swap out dxlhistorian with reloaded configuration: {}'.format(e.message))
        else:
            logger.info('reloaded dxlhistorian with new configuration')

    reloading_configuration.release()


def initialize_historian(dxl_config, historian_config):
    logger.debug('initializing new dxlhistorian instance')

    # Client's responsible for connecting to the mesh
    dxl_client = DxlClient(dxl_config)

    # The recorder performs actions on the received Events
    recorder_type, recorder_conf = historian_config.recorder_config
    recorder = initialize_recorder(recorder_type, recorder_conf)

    return Historian(historian_config, dxl_client, recorder)


# OpenDXL client configuration
client_config = DxlClientConfig.create_dxl_config_from_file(args.dxl_config)

# Service specific configuration
hist_config = HistorianConfig(args.service_config)

historian = initialize_historian(client_config, hist_config)

# Signals to be handled
SIGNALS = {
    signal.SIGINT: interrupt_handler,
    signal.SIGHUP: reload_configuration,
}
for sig in SIGNALS:
    signal.signal(sig, SIGNALS[sig])

historian.start()
running_condition = True
while running_condition:
    signal.pause()
