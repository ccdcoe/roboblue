from configobj import ConfigObj

from robobluekit.kit import run_validators, require, require_and_enforce_type, require_and_enforce_values, \
    require_and_try_coercion

# String representations of available recorder types
RECORDER_STDOUT = 'STDOUT'
RECORDER_ELASTICSEARCH = 'Elasticsearch'


class RecorderConfig:
    def __init__(self, _):
        pass


class STDOUTConfig(RecorderConfig):
    """
    Dummy class to unify the styling of recorders
    """
    pass


class ElasticsearchConfig(RecorderConfig):
    """
    Configuration options for the Elasticsearch backed recorder
    """

    def __init__(self, config):
        RecorderConfig.__init__(self, config)
        self.__parsed = config
        self.__validate()

    def __validate(self):
        run_validators([
            ('Host', str, require_and_enforce_type),
            ('Index', str, require_and_enforce_type),
            ('Port', int, require_and_try_coercion)
        ], self.__parsed)

    @property
    def hosts(self):
        return [{
            'host': self.__parsed['Host'],
            'port': int(self.__parsed['Port'])
        }]

    @property
    def index(self):
        return self.__parsed['Index']


class HistorianConfig:
    """
    HistorianConfig encapsulates the configuration of the Historian application
    """

    __RECORDER_CONFIG_MAPPING = {RECORDER_ELASTICSEARCH: ElasticsearchConfig, RECORDER_STDOUT: STDOUTConfig}

    def __init__(self, config_file):
        self.__parsed = ConfigObj(config_file)
        self.__validate()

    def __validate(self):
        require('Application', self.__parsed)
        run_validators([
            ('SubscribeTo', (list, str), require_and_enforce_type),
            ('Recorder', self.__RECORDER_CONFIG_MAPPING, require_and_enforce_values)
        ], self.__parsed['Application'])

    @property
    def subscribe_to(self):
        sub_to = self.__parsed['Application']['SubscribeTo']
        return [sub_to] if isinstance(sub_to, str) else sub_to

    @property
    def recorder_config(self):
        recorder = self.__parsed['Application']['Recorder']
        return recorder, self.__RECORDER_CONFIG_MAPPING[recorder](
            self.__parsed[recorder] if recorder in self.__parsed else {}
        )
