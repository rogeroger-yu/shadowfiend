from oslo_policy import policy
from oslo_config import cfg

CONF = cfg.CONF

_ENFORCER = None

def get_enforcer():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)
    return _ENFORCER


def get_limited_to(headers, action):
    """Return the user and project the request should be limited to.

    :param headers: HTTP headers dictionary
    :return: A tuple of (user, project), set to None if there's no limit on
    one of these.
    """
    _ENFORCER = get_enforcer()
    if not _ENFORCER.enforce(action,
                             {},
                             {'roles': headers.get('X-Roles', "").split(",")}):
        return headers.get('X-User-Id'), headers.get('X-Project-Id')
    return None, None


def get_limited_to_user(headers, action):
    return get_limited_to(headers, action)[0]


def get_limited_to_project(headers, action):
    return get_limited_to(headers, action)[1]


def context_is_admin(headers):
    """Check whether the context is admin or not."""
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)
    if not _ENFORCER.enforce('context_is_admin',
                             {},
                             {'roles': headers.get('X-Roles', "").split(",")}):
        return False
    else:
        return True


def context_is_domain_owner(headers):
    """Check whether the context is domain owner or not."""
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)
    if not _ENFORCER.enforce('context_is_domain_owner',
                             {},
                             {'roles': headers.get('X-Roles', "").split(",")}):
        return False
    else:
        return True
