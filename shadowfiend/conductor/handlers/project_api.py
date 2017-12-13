from oslo_log import log
import oslo_messaging as messaging
from shadowfiend.db import api as dbapi

LOG = log.getLogger(__name__)

class Handler(object):

    dbapi = dbapi.get_instance()

    def get_billing_owner(cls, context, args):
        LOG.debug('Received message from RPC.')
        billing_owner = cls.dbapi.get_billing_owner(context, args['project_id'])
        
        return billing_owner
