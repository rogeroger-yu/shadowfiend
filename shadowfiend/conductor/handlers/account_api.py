from oslo_log import log
import oslo_messaging as messaging

LOG = log.getLogger(__name__)

class Handler(object):
    def test(self, ctxt, arg):
        LOG.debug('Received message from RPC.')
        return 'test rpc'
