from oslo_log import log
from keystoneauth1 import loading as ks_loading
from keystoneclient import client as kclient
from keystoneclient import discover
from keystoneclient import exceptions
from oslo_config import cfg
import six

LOG = log.getLogger(__name__)
CONF = cfg.CONF

KEYSTONE_FETCHER_OPTS = 'keystone_fetcher'
keystone_fetcher_opts = [
    cfg.StrOpt('keystone_version',
               default='3',
               help='Keystone version to use.'), ]
CONF.register_opts(keystone_fetcher_opts, KEYSTONE_FETCHER_OPTS)
ks_loading.register_session_conf_options(
    CONF,
    KEYSTONE_FETCHER_OPTS)
ks_loading.register_auth_conf_options(
    CONF,
    KEYSTONE_FETCHER_OPTS)



class Fetcher(object):
    def __init__():
        pass


class KeystoneFetcher(Fetcher):
    def __init__(self):
        self.auth = ks_loading.load_auth_from_conf_options(
            CONF,
            KEYSTONE_FETCHER_OPTS)
        self.session = ks_loading.load_session_from_conf_options(
            CONF,
            KEYSTONE_FETCHER_OPTS,
            auth=self.auth)
        self.admin_ks = kclient.Client(
            version=CONF.keystone_fetcher.keystone_version,
            session=self.session,
            auth_url=self.auth.auth_url)
    
    def get_tenants(self):
        keystone_version = discover.normalize_version_number(
            CONF.keystone_fetcher.keystone_version)
        auth_dispatch = {(3,): ('project', 'projects', 'list'),
                         (2,): ('tenant', 'tenants', 'roles_for_user')}
        for auth_version, auth_version_mapping in six.iteritems(auth_dispatch):
            if discover.version_match(auth_version, keystone_version):
                return self._do_get_tenants(auth_version_mapping)
        msg = "Keystone version you've specified is not supported"
        raise exceptions.VersionNotAvailable(msg)

    def _do_get_tenants(self, auth_version_mapping):
        #tenant_attr: project,tenant_attrs: projects,role_func: list
        tenant_attr, tenants_attr, role_func = auth_version_mapping
        tenant_list = getattr(self.admin_ks, tenants_attr).list()
        my_user_id = self.session.get_user_id()
        for tenant in tenant_list[:]:
            roles = getattr(self.admin_ks.roles, role_func)(
                **{'user': my_user_id,
                   tenant_attr: tenant})
            if 'rating' not in [role.name for role in roles]:
                tenant_list.remove(tenant)
        return [tenant.id for tenant in tenant_list]

    def get_users(self):
        user_list = getattr(self.admin_ks, 'users').list() 
        return [user.id for user in user_list]

class TimestampFetcher(Fetcher):
    def __init__():
        pass


class TenantBillFetcher(Fetcher):
    def __init__():
        pass
