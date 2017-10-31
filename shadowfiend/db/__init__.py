from oslo_config import cfg
from oslo_db import options

from shadowfiend.common import paths


sql_opts = [
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help='MySQL engine to use.')
]

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('shadowfiend.sqlite')


cfg.CONF.register_opts(sql_opts, 'database')
options.set_defaults(cfg.CONF, _DEFAULT_SQL_CONNECTION, 'shadowfiend.sqlite')
