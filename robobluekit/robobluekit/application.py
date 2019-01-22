import argparse
import ConfigParser
import logging.config
import os.path as path
import signal
import threading

from .config import HealthServerConfig
from .monitor import MonitoringContext, HealthServer

logger = logging.getLogger(__name__)


class Application:

    def __init__(self):
        self.__arg_parser = argparse.ArgumentParser(add_help=True)
        self.__reloading_configuration = threading.Lock()
        self.__keep_running = True
        self.__keep_running_lock = threading.Lock()
        self.monitoring_context = MonitoringContext()
        self.__monitoring_config = None
        self.__monitoring_server = None

        self.add_argument = self.__arg_parser.add_argument
        self.args = None

    def __register_arguments(self):
        logger.debug('registering CLI arguments')

        self.add_argument(
            '--logging-config',
            help='location of the Python logging module configuration file',
            metavar='PATH_TO_FILE',
            default='./config/logging.config'
        )

        self.add_argument(
            '--monitoring-config',
            help='location of the Roboblue kit monitoring configuration file. When no such file exists,\
                  the monitoring endpoint will not be available',
            metavar='PATH_TO_FILE',
            default='./config/monitoring.config'
        )

        self.register_arguments()

    def __load_configuration(self):
        # Enable file based logger configuration if such a file exists
        if hasattr(self.args, 'logging_config') and path.isfile(self.args.logging_config):
            logger.debug('loading logging configuration from: {}'.format(path.abspath(self.args.logging_config)))
            logging.config.fileConfig(self.args.logging_config)

        if hasattr(self.args, 'monitoring_config') and path.isfile(self.args.monitoring_config):
            logger.debug('loading monitoring configuration from: {}'.format(path.abspath(self.args.monitoring_config)))
            self.__monitoring_config = HealthServerConfig(self.args.monitoring_config)
        else:
            logger.warn('health endpoint not configured')

        self.load_configuration()

    def __register_signal_handlers(self):
        logger.debug('registering signal handlers')
        # Signals to be handled
        signals = {
            signal.SIGINT: self.__interrupt_handler,
            signal.SIGHUP: self.__reload_configuration,
        }
        for sig in signals:
            signal.signal(sig, signals[sig])

    def __reload_configuration(self, sig, frame):
        if not self.__reloading_configuration.acquire(False):
            logger.info('ignoring SIGHUP - reload in progress')
            return None

        logger.info('received SIGHUP - will reload configuration')
        try:
            if hasattr(self.args, 'logging_config') and path.isfile(self.args.logging_config):
                logger.info('logging configuration loading from: {}'.format(path.abspath(self.args.logging_config)))
                logging.config.fileConfig(self.args.logging_config)
        except ConfigParser.Error as e:
            logger.error('failed config reload: invalid logger configuration')
            logger.error('logging configuration error: {}'.format(e.message))

        self.reload()  # Application specific actions

        self.__reloading_configuration.release()

    def __initialize(self):
        if self.__monitoring_config is not None:
            self.__monitoring_server = HealthServer(self.__monitoring_config, self)
            self.__monitoring_server.serve()

        self.initialize()

    def __interrupt_handler(self, sig, frame):
        if self.__keep_running_lock.acquire(False):
            logger.debug('received interrupt, shutting down')
            self.__keep_running = False

    def register_arguments(self):
        """
        Convenient hook to register CLI arguments with the argument parser
        :return: None
        """
        raise NotImplementedError('requires implementation')

    def load_configuration(self):
        """
        Hook to load application specific configuration
        :return: None
        """
        raise NotImplementedError('requires implementation')

    def initialize(self):
        """
        Application specific initialization hook
        :return: None
        """
        raise NotImplementedError('requires implementation')

    def reload(self):
        """
        Application specific configuration reload hook
        :return: None
        """
        raise NotImplementedError('requires implementation')

    def bootstrap(self):
        """
        Generic bootstrap activities so that we end up with a working application
        :return:
        """
        self.__register_arguments()
        self.args = self.__arg_parser.parse_args()

        self.__load_configuration()

        self.__register_signal_handlers()

        self.__initialize()

    def destroy(self):
        """
        Application specific tear-down activities
        :return: None
        """
        raise NotImplementedError('requires implementation')

    def run(self):
        while self.__keep_running:
            signal.pause()
