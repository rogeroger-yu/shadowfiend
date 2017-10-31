from pecan import rest

from shadowfiend.api import expose

from shadowfiend.api.controllers.v1 import account
#from shadowfiend.api.controllers.v1 import project
#from shadowfiend.api.controllers.v1 import relation
#from shadowfiend.api.controllers.v1 import charge
#from shadowfiend.api.controllers.v1 import order

from shadowfiend.api.controllers.v1 import models


class V1Controller(rest.RestController):
    accounts = account.AccountController()
#    projects = project.ProjectController()
#    relations = relation.RelationController()
#    charges = charge.ChargeController()
#    orders = order.OrderController()

    @expose.expose(models.Version)
    def get(self):
        return models.Version(version='1.0.0')
