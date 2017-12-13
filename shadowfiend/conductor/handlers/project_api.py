from oslo_log import log
import oslo_messaging as messaging
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models

LOG = log.getLogger(__name__)

class Handler(object):

    dbapi = dbapi.get_instance()

    def get_billing_owner(cls, context, **kwargs):
        LOG.debug('Conductor Function: get_billing_owner.')
        billing_owner = cls.dbapi.get_billing_owner(context, kwargs['project_id'])
        
        return billing_owner

    def create_project(cls, context, **kwargs):
        LOG.debug('Conductor Function: create_project.')
        project = db_models.Project(**kwargs)
        return cls.dbapi.create_project(context, project)

    def get_project(cls, context, **kwargs):
        LOG.debug('Conductor Function: get_project.')
        project = cls.dbapi.get_project(context, kwargs['project_id'])
        
        return project
