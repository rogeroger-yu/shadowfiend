import pecan
import datetime
import itertools

from pecan import rest
from pecan import request
from wsmeext.pecan import wsexpose
from wsme import types as wtypes

from oslo_config import cfg

from shadowfiend.common import exception
from shadowfiend.api.controllers.v1 import models
from oslo_log import log as logging


LOG = logging.getLogger(__name__)
HOOK = pecan.request


class BillingOwnerController(rest.RestController):

    _custom_actions = {
        'freeze': ['PUT'],
        'unfreeze': ['PUT'],
    }

    def __init__(self, project_id, external_client):
        self.project_id = project_id
        self.external_client = external_client

    @wsexpose(None, wtypes.text)
    def put(self, user_id):
        """Change billing_owner of this project."""
        HOOK.conductor_rpcapi.change_billing_owner(request.context,
                                                   project_id=self.project_id,
                                                   user_id=user_id)

    @wsexpose(models.UserAccount)
    def get(self):
        pass

    @wsexpose(models.BalanceFrozenResult, body=models.BalanceFrozenBody)
    def freeze(self, data):
        pass

    @wsexpose(models.BalanceFrozenResult, body=models.BalanceFrozenBody)
    def unfreeze(self, data):
        pass


class ExistProjectController(rest.RestController):
    """Manages operations on project."""

    _custom_actions = {
        'estimate': ['GET'],
    }

    def __init__(self, project_id, external_client):
        pass

    @pecan.expose()
    def _lookup(self, subpath, *remainder):
        pass

    @wsexpose(models.Project)
    def get(self):
        """Return this project."""
        pass

    @wsexpose(models.Summaries, wtypes.text)
    def estimate(self, region_id=None):
        """Get estimation of specified project and region."""
        pass


class ProjectController(rest.RestController):
    """Manages operations on the projects collection."""

    def __init__(self):
        pass

    @pecan.expose()
    def _lookup(self, project_id, *remainder):
        pass

    @wsexpose([models.UserProject], wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, user_id=None, type=None, duration=None):
        """Get all projects."""
        pass

    @wsexpose(None, body=models.Project)
    def post(self, data):
        """Create a new project."""
        pass
