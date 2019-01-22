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
