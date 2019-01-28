import logging
import os
import json
from typing import Any, Optional

try:
    from alerta.plugins import app  # alerta >= 5.0
except ImportError:
    from alerta.app import app  # alerta < 5.0

from alerta.plugins import PluginBase

from dxlclient import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.message import Event

LOG = logging.getLogger('alerta.plugins.opendxl')

DXL_CLIENT_CONFIG_FILE = os.environ.get('DXL_CLIENT_CONFIG_FILE') or app.config.get('DXL_CLIENT_CONFIG_FILE')
DXL_PUB_TOPIC = os.environ.get('DXL_PUB_TOPIC') or app.config.get('DXL_PUB_TOPIC')


class OpenDxlPublisher(PluginBase):

    def __init__(self, name=None):
        try:
            LOG.info('loading opendxl configuration')
            client_config = DxlClientConfig.create_dxl_config_from_file(DXL_CLIENT_CONFIG_FILE)
            self.dxl_client = DxlClient(client_config)
            LOG.info('connecting to OpenDXL broker')
            self.dxl_client.connect()
        except Exception as e:
            LOG.error('failed to connect to OpenDXL broker: %s', str(e))
            raise

        PluginBase.__init__(self, name)
        LOG.info('opendxl publisher connected and ready')

    def pre_receive(self, alert: 'Alert') -> 'Alert':
        return alert

    def post_receive(self, alert: 'Alert') -> Optional['Alert']:
        try:
            event = Event(DXL_PUB_TOPIC)
            event.payload = json.dumps(alert.get_body(history=False))
            LOG.info('broadcasting alert %s', alert.id)
            self.dxl_client.send_event(event)
        except BaseException as e:
            LOG.exception('failed to broadcast alert: %s', str(e))
            raise RuntimeError('failed to broadcast alert: ' + str(e))

    def status_change(self, alert: 'Alert', status: str, text: str) -> Any:
        return
