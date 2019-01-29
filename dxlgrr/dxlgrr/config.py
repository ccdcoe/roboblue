from configobj import ConfigObj

from robobluekit.kit import require, run_validators, require_and_enforce_type


class GRRConfig:
    """
    Configuration options for the DXL GRR service
    """

    def __init__(self, config_file):
        self.__cfg = ConfigObj(config_file)
        self.__validate()

    def __validate(self):
        # Validate existence of required config blocks
        run_validators([
            ('GRR', None, require),
            ('Service', None, require)
        ], self.__cfg)

        run_validators([
            ('Type', str, require_and_enforce_type)
        ], self.__cfg['Service'])

        run_validators([
            ('Endpoint', str, require_and_enforce_type),
            ('Username', str, require_and_enforce_type),
            ('Password', str, require_and_enforce_type)
        ], self.__cfg['GRR'])

    @property
    def http_endpoint(self):
        return self.__cfg['GRR']['Endpoint']

    @property
    def auth(self):
        return self.__cfg['GRR']['Username'], self.__cfg['GRR']['Password']

    @property
    def service_type(self):
        return self.__cfg['Service']['Type']
