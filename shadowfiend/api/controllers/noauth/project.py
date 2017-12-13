import pecan
import wsme

from pecan import rest
from pecan import request
from wsmeext.pecan import wsexpose
from wsme import types as wtypes

from oslo_config import cfg
from oslo_log import log

from shadowfiend.api.controllers.v1 import models
from shadowfiend.db import models as db_models
from shadowfiend.common import exception


LOG = log.getLogger(__name__)
HOOK = pecan.request


class BillingOwnerController(rest.RestController):

    def __init__(self, project_id):
        self.project_id = project_id

    @wsexpose(None, wtypes.text)
    def put(self, user_id):
        """Change billing_owner of this project."""
        HOOK.conductor_rpcapi.change_billing_owner(HOOK.context,
                                                   project_id=self.project_id,
                                                   user_id=user_id)


class ExistProjectController(rest.RestController):
    """Manages operations on project."""

    def __init__(self, project_id):
        self._id = project_id

    def _project(self):
        try:
            project = HOOK.conductor_rpcapi.get_project(HOOK.context,
                                                        project_id=self._id)
        except Exception as e:
            LOG.error('project %s no found' % self._id)
            raise exception.ProjectNotFound(project_id=self._id)
        return project

    @pecan.expose()
    def _lookup(self, subpath, *remainder):
        if subpath == 'billing_owner':
            return (BillingOwnerController(self._id),
                    remainder)

    @wsexpose(models.Project)
    def get(self):
        """Return this project."""
        return db_models.Project(**self._project())


class ProjectController(rest.RestController):
    """Manages operations on the accounts collection."""

    def __init__(self):
        pass

    @pecan.expose()
    def _lookup(self, project_id, *remainder):
        if remainder and not remainder[-1]:
            remainder = remainder[:-1]
        return ExistProjectController(project_id), remainder

    @wsexpose(None, body=models.Project)
    def post(self, data):                 
        """Create a new project."""
        try:                           
            project = data.as_dict()
            return HOOK.conductor_rpcapi.create_project(HOOK.context, project)
        except Exception:
            LOG.exception('Fail to create project: %s' % data.as_dict())
            raise exception.ProjectCreateFailed(project_id=data.project_id,
                                                user_id=data.user_id)
