from oslo_config import cfg
from oslo_middleware import cors

from shadowfiend.common import rpc
#from shadowfiend.db.sqlalchemy import api as sqlalchemy_api
from shadowfiend.common import version


def parse_args(argv, default_config_files=None, configure_db=True,
               init_rpc=True):
    rpc.set_defaults(control_exchange='shadowfiend')
    cfg.CONF(argv[1:],
             project='shadowfiend',
             validate_default_values=True,
             version=version.version_info.release_string(),
             default_config_files=default_config_files)

    rpc.init(cfg.CONF)

    #if configure_db:
    #    sqlalchemy_api.configure(CONF)


def set_middleware_defaults():
    cfg.set_defaults(cors.CORS_OPTS,
                     allow_headers=['X-Auth-Token',
                                    'X-Openstack-Request-Id',
                                    'X-Identity-Status',
                                    'X-Roles',
                                    'X-Service-Catalog',
                                    'X-User-Id',
                                    'X-Tenant-Id'],
                     expose_headers=['X-Auth-Token',
                                     'X-Openstack-Request-Id',
                                     'X-Subject-Token',
                                     'X-Service-Token'],
                     allow_methods=['GET',
                                    'PUT',
                                    'POST',
                                    'DELETE',
                                    'PATCH']
                     )
