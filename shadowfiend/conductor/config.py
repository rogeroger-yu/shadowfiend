from oslo_config import cfg

SERVICE_OPTS = [
    cfg.StrOpt('topic',
               default='shadowfiend-conductor',
               help='The queue to add conductor tasks to.'),
    cfg.IntOpt(
        'workers',
        help='Number of workers for OpenStack Conductor service. The default will be the number of CPUs available.'),
    cfg.IntOpt('conductor_life_check_timeout',
               default=4,
               help=('RPC timeout for the conductor liveness check that is '
                     'used for bay locking.')),
]

opt_group = cfg.OptGroup(
    name='conductor',
    title='Options for the shadowfiend-conductor service')
cfg.CONF.register_group(opt_group)
cfg.CONF.register_opts(SERVICE_OPTS, opt_group)
