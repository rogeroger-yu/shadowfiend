from oslo_log import log
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models


LOG = log.getLogger(__name__)

class Handler(object):
 
    dbapi = dbapi.get_instance()

    def __init__(self):
        super(Handler, self).__init__()

    def create_account(cls, context, **kwargs):
        LOG.debug('create account: Received message from RPC.')
        account = db_models.Account(**kwargs)
        return cls.dbapi.create_account(context, account)

    def get_account(cls, context, **kwargs):
        LOG.debug('get account: Received message from RPC.')
        account = cls.dbapi.get_account(context, **kwargs)
        return account

    def delete_account(cls, context, **kwargs):
        LOG.debug('delete account: Received message from RPC.')
        cls.dbapi.delete_account(context, **kwargs)

    def change_account_level(cls, context, **kwargs):
        LOG.debug('change account level: Received message from RPC.')
        return cls.dbapi.change_account_level(**kwargs)

    def update_account(cls, context, **kwargs):
        LOG.debug('update account: Received message from RPC.')
        return cls.dbapi.update_account(context,
                                        kwargs.pop('user_id'),
                                        kwargs.pop('operator'),
                                        **kwargs)

    def get_charges(cls, context, **kwargs):
        LOG.debug('get charges: Received message from RPC.')
        return cls.dbapi.get_charges(context, **kwargs)

    def get_charges_price_and_count(cls, context, **kwargs):
        LOG.debug('get_charges_price_and_count: Received message from RPC.')
        return cls.dbapi.get_charges_price_and_count(context, **kwargs)
