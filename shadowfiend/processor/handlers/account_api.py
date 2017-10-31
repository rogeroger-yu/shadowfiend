from oslo_log import log
from shadowfiend.processor.service import fetcher
import oslo_messaging as messaging

LOG = log.getLogger(__name__)

class Handler(object):
    def test(self, ctxt, arg):
        LOG.debug('Received message from RPC.')
        self.keystone_fetcher = fetcher.KeystoneFetcher()
        #tenants = self.keystone_fetcher.get_tenants()
        accounts = self.keystone_fetcher.get_users()
        LOG.debug('tenants are: %s' % str(accounts))
        return 'this is processor'
