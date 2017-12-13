from oslo_log import log
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models


LOG = log.getLogger(__name__)

class Handler(object):
        
    dbapi = dbapi.get_instance()

    def __init__(self):
        super(Handler, self).__init__()

    def create_account(cls, context, **kwargs):
        LOG.debug('create account:Received message from RPC.')
        account = db_models.Account(**kwargs)
        return cls.dbapi.create_account(context, account)
