"""API for interfacing with shadowfiend Backend."""
from oslo_config import cfg

from shadowfiend.common import service as rpc_service


# The Backend API class serves as a AMQP client for communicating
# on a topic exchange specific to the conductors.  This allows the ReST
# API to trigger operations on the conductors

class API(rpc_service.API):
    def __init__(self, transport=None, context=None, topic=None):
        if topic is None:
            cfg.CONF.import_opt('topic', 'shadowfiend.conductor.config',
                                group='conductor')
        super(API, self).__init__(transport, context,
                                  topic=cfg.CONF.conductor.topic)

    def test(self):
        #return 'test RPC'
        #return self._client.cast({}, 'test')
        return self._call('test', arg='test_arg')

#    def cluster_create_async(self, cluster, create_timeout):
#        self._cast('cluster_create', cluster=cluster,
#                   create_timeout=create_timeout)

