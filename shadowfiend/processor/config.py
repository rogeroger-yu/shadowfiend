from oslo_config import cfg

SERVICE_OPTS = [
    cfg.StrOpt('topic',
               default='shadowfiend-processor',
               help=('The queue to add processor tasks to.')),
    cfg.IntOpt('workers',
               default=1,
               help=('Number of workers for OpenStack Processor service.'
                     'The default will be the number of CPUs available.')),
    cfg.IntOpt('processor_life_check_timeout',
               default=4,
               help=('RPC timeout for the Processor liveness check that is '
                     'used for bay locking.')),
    cfg.IntOpt('process_period',
               default=3600,
               help=('process period in seconds.')),
]

opt_group = cfg.OptGroup(
    name='processor',
    title='Options for the shadowfiend-processor service')
cfg.CONF.register_group(opt_group)
cfg.CONF.register_opts(SERVICE_OPTS, opt_group)
