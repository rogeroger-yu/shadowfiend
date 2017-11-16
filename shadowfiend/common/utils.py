from shadowfiend.common import constants as const



STATE_MAPPING = {
    'ACTIVE': const.STATE_RUNNING,
    'active': const.STATE_RUNNING,
    'available': const.STATE_RUNNING,
    'in-use': const.STATE_RUNNING,
    'deprecated': const.STATE_RUNNING,
    'DOWN': const.STATE_RUNNING,
    'SHUTOFF': const.STATE_STOPPED,
    'SUSPENDED': const.STATE_SUSPEND,
    'PAUSED': const.STATE_SUSPEND,
    'True': const.STATE_RUNNING,
    'False': const.STATE_STOPPED,
    'true': const.STATE_RUNNING,
    'false': const.STATE_STOPPED,
}


def transform_status(status):
    try:
        return STATE_MAPPING[status]
    except KeyError:
        return const.STATE_ERROR


def format_datetime(dt):
    return '%s %s.000000' % (dt[:10], dt[11:19])

