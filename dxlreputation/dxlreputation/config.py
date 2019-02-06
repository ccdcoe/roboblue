from configobj import ConfigObj

from robobluekit.kit import run_validators, require, require_and_enforce_type, require_and_enforce_values, \
    require_and_try_coercion


class RedisConfig:
    """
    Configuration settings applicable to the Redis connection
    """

    def __init__(self, container):
        self.__config = container
        self.__validate()

    @property
    def hostname(self):
        return self.__config['Hostname']

    @property
    def use_ssl(self):
        return self.__config['UseSSL'] != 'False'

    @property
    def port(self):
        return int(self.__config['Port'])

    @property
    def db(self):
        return int(self.__config['DB'])

    def __validate(self):
        run_validators([
            ('Hostname', str, require_and_enforce_type),
            ('UseSSL', ['True', 'False'], require_and_enforce_values),
            ('Port', int, require_and_try_coercion),
            ('DB', int, require_and_try_coercion)
        ], self.__config)


class ServiceConfig:
    """
    Representation of the whole configuration
    """

    def __init__(self, config_file):
        self.__parsed = ConfigObj(config_file)
        self.__validate()
        self.redis_config = RedisConfig(self.__parsed['Redis'])

    def __validate(self):
        run_validators([
            ('Service', None, require),
            ('Redis', None, require)
        ], self.__parsed)

        run_validators([
            ('Type', str, require_and_enforce_type)
        ], self.__parsed['Service'])

    @property
    def type(self):
        return self.__parsed['Service']['Type']
