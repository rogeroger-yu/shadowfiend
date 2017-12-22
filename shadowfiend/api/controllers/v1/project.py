import pecan
import datetime
import itertools

from pecan import rest
from wsmeext.pecan import wsexpose
from wsme import types as wtypes

from oslo_config import cfg
from oslo_log import log

from shadowfiend.api import acl
from shadowfiend.api.controllers.v1 import models
from shadowfiend.common import exception
from shadowfiend.common import timeutils
from shadowfiend.db import models as db_models
from shadowfiend.services import keystone as ks_client


LOG = log.getLogger(__name__)
HOOK = pecan.request


class BillingOwnerController(rest.RestController):

    _custom_actions = {
        'freeze': ['PUT'],
        'unfreeze': ['PUT'],
    }

    def __init__(self, project_id):
        self.project_id = project_id

    @wsexpose(None, wtypes.text)
    def put(self, user_id):
        """Change billing_owner of this project."""
        HOOK.conductor_rpcapi.change_billing_owner(HOOK.context,
                                                   project_id=self.project_id,
                                                   user_id=user_id)

    @wsexpose(models.UserAccount)
    def get(self):
        LOG.info("get_billing_owner")
        user_account = HOOK.conductor_rpcapi.get_billing_owner(HOOK.context,
                                                               self.project_id)
        return db_models.Account(**user_account)

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

    def __init__(self, project_id):
        self._id = project_id

    @pecan.expose()
    def _lookup(self, subpath, *remainder):
        if subpath == 'billing_owner':
            return (BillingOwnerController(self._id),
                    remainder)

    def _project(self):
        try:
            project = HOOK.conductor_rpcapi.get_project(HOOK.context,
                                                        project_id=self._id)
        except Exception as e:
            LOG.error('project %s no found' % self._id)
            raise exception.ProjectNotFound(project_id=self._id)
        return project

    @wsexpose(models.Project)
    def get(self):
        """Return this project."""
        return db_models.Project(**self._project())

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
        if remainder and not remainder[-1]:
            remainder = remainder[:-1]
        return ExistProjectController(project_id), remainder

    @wsexpose([models.UserProject], wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, user_id=None, type=None, duration=None):
        """Get all projects."""
        user_id = acl.get_limited_to_user(HOOK.headers,
                                          'projects_get') or user_id
        result = []

        if not type or type.lower() == 'pay':
            # if admin call this api, limit to admin's user_id
            if not user_id:
                user_id = HOOK.context.user_id

            try:
                user_projects = HOOK.conductor_rpcapi.get_user_projects(
                    HOOK.context,
                    user_id=user_id)
            except Exception as e:
                LOG.exception('Fail to get all projects')
                raise exception.DBError(reason=e)

            if not user_projects:
                LOG.warn('User %s has no payed projects' % user_id)
                return []

            project_ids = [up['project_id'] for up in user_projects]

            projects = self._list_keystone_projects()

            for u, p in itertools.product(user_projects, projects):
                if u['project_id'] == p.id:
                    up = models.UserProject(
                        user_id=user_id,
                        project_id=u['project_id'],
                        project_name=p.name,
                        user_consumption=u['user_consumption'],
                        project_consumption=u['project_consumption'],
                        billing_owner=None,
                        project_owner=None,
                        project_creator=None,
                        is_historical=u['is_historical'],
                        created_at=u['created_at'])
                    result.append(up)
        elif type.lower() == 'all':
            # if admin call this api, limit to admin's user_id
            if not user_id:
                user_id = HOOK.context.user_id

            k_projects = ks_client.get_project_list(name=user_id)
            LOG.debug('Projects: %s' % k_projects)
            project_ids = [p.id for p in k_projects]

            if not project_ids:
                LOG.warning('User %s has no projects' % user_id)
                return []

            try:
                sf_projects = (HOOK.conductor_rpcapi.
                               get_projects_by_project_ids(
                                   HOOK.context, project_ids))
            except Exception as e:
                LOG.exception('Fail to get all projects')
                raise exception.DBError(reason=e)
            for k, sf in itertools.product(k_projects, sf_projects):
                k = k.__dict__
                if k['id'] == sf['project_id']:
                    up = models.UserProject(
                        user_id=user_id,
                        project_id=sf['project_id'],
                        project_name=k['name'],
                        project_consumption=sf['consumption'],
                        billing_owner=None,
                        project_owner=None,
                        project_creator=None,
                        is_historical=False,
                        created_at=(
                            sf['created_at'] if sf['created_at'] else None))
                    result.append(up)

        elif type.lower() == 'simple':
            duration = gringutils.normalize_timedelta(duration)
            if duration:
                active_from = datetime.datetime.utcnow() - duration
            else:
                active_from = None
            sf_projects = list(HOOK.conductor_rpcapi.get_projects(
                HOOK.context,
                user_id=user_id,
                active_from=active_from))
            project_ids = [p.project_id for p in sf_projects]

            if not project_ids:
                LOG.warn('User %s has no payed projects' % user_id)
                return []

            k_projects = self._list_keystone_projects()

            for k, sf in itertools.product(k_projects, sf_projects):
                if k.id == sf['project_id']:
                    up = models.UserProject(
                        project_id=sf['project_id'],
                        project_name=k.name,
                        domain_id=sf['domain_id'],
                        billing_owner=dict(user_id=sf['user_id']))
                    result.append(up)

        return result

    def _list_keystone_projects(self):
        projects = []
        domain_ids = \
            [domain.id for domain in ks_client.get_domain_list()]
        for domain_id in domain_ids:
            projects.extend(ks_client.get_project_list(domain_id))
        return projects

    @wsexpose(None, body=models.Project)
    def post(self, data):
        """Create a new project."""
        try:
            project = data.as_dict()
            return HOOK.conductor_rpcapi.create_project(HOOK.context, project)
        except Exception:
            LOG.exception('Fail to create project: %s' % project)
            raise exception.ProjectCreateFailed(project_id=data.project_id,
                                                user_id=data.user_id)
