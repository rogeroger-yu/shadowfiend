from shadowfiend.common import policy
from oslo_config import cfg


def get_limited_to(headers, action):
    """Return the user and project the request should be limited to.

    :param headers: HTTP headers dictionary
    :return: A tuple of (user, project), set to None if there's no limit on
    one of these.
    """
    context = {'roles': headers.get('X-Roles', "").split(",")}
    if not policy.enforce(context, action, {}):
        return headers.get('X-User-Id'), headers.get('X-Project-Id')
    return None, None


def get_limited_to_user(headers, action):
    return get_limited_to(headers, action)[0]


def get_limited_to_project(headers, action):
    return get_limited_to(headers, action)[1]


def limit_to_sales(context, user_id):
    """Limit permission via sales related roles.

    If roles of context matched rule uos_sales_admin, return True.
    If roles of context matched rule uos_sales but not uos_sales_admin,
    return True if context.user_id matched user_id, or False.
    Otherwise, return False.
    """

    if policy.enforce(context, 'uos_sales_admin', {}):
        return True

    return False


def context_is_admin(headers):
    """Check whether the context is admin or not."""
    context = {'roles': headers.get('X-Roles', "").split(",")}
    if not policy.enforce(context, 'context_is_admin', {}):
        return False
    else:
        return True


def context_is_domain_owner(headers):
    """Check whether the context is domain owner or not."""
    context = {'roles': headers.get('X-Roles', "").split(",")}
    if not policy.enforce(context, 'context_is_domain_owner', {}):
        return False
    else:
        return True
