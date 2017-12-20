from oslo_log import log
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models


LOG = log.getLogger(__name__)

class Handler(object):

    dbapi = dbapi.get_instance()

    def __init__(self):
        super(Handler, self).__init__()

    def create_order(cls, context, **kwargs):
        LOG.debug('create order: Received message from RPC.')
        order = db_models.Order(**kwargs)
        return cls.dbapi.create_order(context, order)

    def close_order(cls, context, **kwargs):
        LOG.debug('close order: Received message from RPC.')
        return cls.dbapi.close_order(context, kwargs['order_id'])
