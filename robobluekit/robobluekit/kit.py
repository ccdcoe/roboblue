import threading
import time

from .monitor import Monitor


class ServiceEndpointMonitor(Monitor):
    """
    Service endpoint monitor is included with the roboblue kit to create an unified way to monitor OpenDXL service
    endpoints
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


def format_timestamp(stamp):
    """
    Consistent way to format a floating point UNIX timestamp to a long ms resolution one
    :param stamp: floating point unix timestamp
    :return: Long, ms resolution timestamp
    """
    return None if stamp is None else int(stamp * 10e3)


class InvalidConfigException(Exception):
    pass


"""
The following are various helper functions useful to perform configuration validation actions
"""


def require(keyword, container):
    if keyword not in container:
        raise InvalidConfigException('Missing required keyword {} in configuration'.format(keyword))


def require_and_enforce_type(keyword, t, container):
    require(keyword, container)
    if not isinstance(container[keyword], t):
        raise InvalidConfigException('Invalid value type for configuration keyword {}'.format(keyword))


def optional_and_enforce_type(keyword, t, container):
    if keyword in container and not isinstance(container[keyword], t):
        raise InvalidConfigException('Invalid value type for configuration keyword {}'.format(keyword))


def require_and_try_coercion(keyword, t, container):
    require(keyword, container)
    try:
        t(container[keyword])
    except ValueError:
        raise InvalidConfigException('{} must be coercible to {}'.format(keyword, t))


def require_and_enforce_values(keyword, possible_values, container):
    require(keyword, container)
    if container[keyword] not in possible_values:
        raise InvalidConfigException('Value for keyword {} is not allowed')


def run_validators(spec, container):
    for triple in spec:
        keyword, t, validator = triple
        validator(keyword, t, container) if t is not None else validator(keyword, container)
