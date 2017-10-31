from pecan import rest
from wsme import types as wtypes

from shadowfiend.api.controllers import v1
from shadowfiend.api import expose

#from shadowfiend.api.controllers import base


class RootController(rest.RestController):

    _versions = ['v1']

    _default_version = 'v1'

    v1 = v1.V1Controller()

    @expose.expose(wtypes.text)
    def get(self):
#        return Root.convert()
        return "test"
