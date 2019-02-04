from configobj import ConfigObj

from robobluekit.kit import run_validators, require, require_and_enforce_type, require_and_enforce_values


class EndpointConfig:
    """
    Configuration necessary to enable pass through of requests for a single endpoint
    """
    def __init__(self, type, name, url, parent):
        # type: (str, str, list, ServiceConfig) -> None
        self.name = name
        self.type = type
        self.parent = parent
        self.__url = url

    def clone(self, parent):
        """
        Create a new instance of itself, but with a new parent
        :param parent: Parent service configuration
        :return: new EndpointConfig instance
        """
        return EndpointConfig(self.type, self.name, self.__url, parent)

    @property
    def auth(self):
        return self.parent.auth

    @property
    def url(self):
        return [self.parent.http_endpoint] + self.__url

    @property
    def verify_ssl(self):
        return self.parent.verify_ssl


class ServiceConfig:
    """
    Configuration that applies service wide
    """
    def __init__(self, config_file):
        self.__parsed = ConfigObj(config_file)
        self.endpoints = []
        self.__validate()

    @property
    def type(self):
        return self.__parsed['Service']['Type']

    @property
    def auth(self):
        return self.__parsed['Wazuh']['Username'], self.__parsed['Wazuh']['Password']

    @property
    def http_endpoint(self):
        return self.__parsed['Wazuh']['Endpoint']

    @property
    def verify_ssl(self):
        return self.__parsed['Wazuh']['VerifySSL'] != 'False'

    def __validate(self):
        run_validators([
            ('Service', None, require),
            ('Wazuh', None, require),
        ], self.__parsed)

        run_validators([
            ('Type', str, require_and_enforce_type)
        ], self.__parsed['Service'])

        run_validators([
            ('Username', str, require_and_enforce_type),
            ('Password', str, require_and_enforce_type),
            ('Endpoint', str, require_and_enforce_type),
            ('VerifySSL', ['True', 'False'], require_and_enforce_values)
        ], self.__parsed['Wazuh'])
