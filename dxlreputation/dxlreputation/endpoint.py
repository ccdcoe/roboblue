import json
import logging

from dxlclient.callbacks import RequestCallback
from dxlclient.message import Request, Response, ErrorResponse

from robobluekit.kit import run_validators, require_and_enforce_type, optional_and_enforce_type, InvalidConfigException

logger = logging.getLogger(__name__)


class ReputationServiceEndpoint(RequestCallback):
    """
    A generic wrapping endpoint that lets us focus on the happy path and the happy path alone when actually
    implementing endpoints
    """

    def __init__(self, monitor, parent):
        self.__monitor = monitor
        self.service = parent
        RequestCallback.__init__(self)

    def on_request(self, request):
        self.__monitor.register_request()
        response = Response(request)
        try:
            response = self.handle_request(request, response)
        except BadRequest as e:
            response = ErrorResponse(request, 400, str(e))
        except ValueError:
            response = ErrorResponse(request, 400, 'invalid request payload')
        except Exception as e:
            logger.exception('unknown exception %s of type %s', str(e), type(e).__name__)
            response = ErrorResponse(request, 500, 'unknown internal error occurred')
        finally:
            if isinstance(response, ErrorResponse) and response.error_code >= 500:
                # Error count doesn't include client errors
                self.__monitor.register_error()
            else:
                self.__monitor.register_success()
            self.service.dxl_conn.send_response(response)

    def handle_request(self, request, response):
        # type: (Request, Response) -> Response
        raise NotImplementedError('requires implementation')


class BadRequest(Exception):
    """
    Exception indicating that the user's at fault for providing invalid input
    """
    pass


def validate_request(payload, spec):
    """
    Validate the incoming request by re using the configuration validators from roboblue kit
    :param payload: dictionary representing the incoming JSON object
    :return: None
    """
    try:
        run_validators(spec, payload)
    except InvalidConfigException as e:
        raise BadRequest('bad request, check the payload for missing values / invalid types')


class UpdateReputation(ReputationServiceEndpoint):
    """
    Service endpoint implementation responsible for handling reputation updates
    """

    def handle_request(self, request, response):
        payload = json.loads(request.payload)
        validate_request(payload, [
            ('type', unicode, require_and_enforce_type),
            ('key', unicode, require_and_enforce_type),
            ('reputation', int, optional_and_enforce_type),
        ])
        payload['reputation'] = self.service.redis_conn.hincrby(payload['type'], payload['key'],
                                                                payload.get('reputation', 0))
        response.payload = json.dumps({
            'type': payload['type'],
            'key': payload['key'],
            'reputation': payload['reputation']
        })
        return response


class GetReputation(ReputationServiceEndpoint):
    """
    Service endpoint responsible for handling queries for reputation of items
    """

    def handle_request(self, request, response):
        payload = json.loads(request.payload)
        validate_request(payload, [
            ('type', unicode, require_and_enforce_type),
            ('key', unicode, require_and_enforce_type)
        ])
        rep = self.service.redis_conn.hget(payload['type'], payload['key'])
        response.payload = json.dumps({
            'type': payload['type'],
            'key': payload['key'],
            'reputation': 0 if rep is None else int(rep)
        })
        return response


# Listing of endpoints provided by the service for use in the service
SERVICE_ENDPOINTS = [
    ('GetReputation', GetReputation),
    ('UpdateReputation', UpdateReputation)
]
