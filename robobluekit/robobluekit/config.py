from configobj import ConfigObj

from .kit import require, optional_and_enforce_type, require_and_try_coercion, run_validators


class HealthServerConfig:
    """
    Configuration of the monitoring status reporting HTTP endpoint
    """
    def __init__(self, config_file):
        self.__parsed = ConfigObj(config_file)
        self.__validate()

    def __validate(self):
        require('Server', self.__parsed)
        run_validators([
            ('Host', str, optional_and_enforce_type),
            ('Port', int, require_and_try_coercion),
        ], self.__parsed['Server'])

    @property
    def httpd_address(self):
        container = self.__parsed['Server']
        return container.get('Host', ''), int(container['Port'])
