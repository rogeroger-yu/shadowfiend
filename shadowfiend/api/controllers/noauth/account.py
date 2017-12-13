import pecan 
import wsme 
from pecan import rest 
from wsmeext.pecan import wsexpose
from wsme import types as wtypes
from oslo_config import cfg
from oslo_log import log

from shadowfiend.api.controllers.v1 import models
from shadowfiend.common import exception


LOG = log.getLogger(__name__)

HOOK = pecan.request


class AccountController(rest.RestController):
    """Manages operations on the accounts collection."""

    @wsexpose(None, body=models.AdminAccount)
    def post(self, data):
        """Create a new account."""
        import pdb;pdb.set_trace()
        try:
            account = data.as_dict()
            return HOOK.conductor_rpcapi.create_account(HOOK.context,
                                                        account)
        except Exception:
            LOG.ERROR('Fail to create account: %s' % data.as_dict())
            raise exception.AccountCreateFailed(user_id=data.user_id,
                                                domain_id=data.domain_id)

