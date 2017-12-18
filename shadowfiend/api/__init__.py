from oslo_config import cfg

# Register options for the service
CONF = cfg.CONF

OPTS = [
    cfg.BoolOpt('notify_account_charged',
                default=False,
                help="Notify user when he/she charges"),
    cfg.StrOpt('precharge_limit_rule',
               default='5/quarter',
               help='Frequency of do precharge limitation'),
    cfg.ListOpt('regions',
                default=['RegionOne'],
                help="A list of regions that is avaliable"),
    cfg.BoolOpt('enable_invitation',
                default=False,
                help="Enable invitation or not"),
    cfg.StrOpt('min_charge_value',
                default='0',
                help="The minimum charge value if meet the reward condition"),
    cfg.StrOpt('limited_accountant_charge_value',
                default=100000,
                help="The minimum charge value the accountant can operate"),
    cfg.StrOpt('limited_support_charge_value',
                default=200,
                help="The minimum charge value the support staff can operate"),
    cfg.StrOpt('reward_value',
               default='0',
               help="The reward value if meet the reward condition"),
]

CONF = cfg.CONF
CONF.register_opts(OPTS)
