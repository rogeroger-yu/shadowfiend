import datetime

import pecan
from pecan import rest
from pecan import request
import wsme
from wsme import types as wtypes
from wsmeext.pecan import wsexpose
from oslo_config import cfg
from oslo_log import log as logging

#from shadowfiend.policy import check_policy
#from shadowfiend import exception
#from shadowfiend import utils as gringutils
from shadowfiend.api.controllers.v1 import models
#from shadowfiend.db import models as db_models
#from shadowfiend.services import keystone
#from shadowfiend.checker import notifier
#from shadowfiend.openstack.common.gettextutils import _
from shadowfiend.conductor import api as conductor_api


LOG = logging.getLogger(__name__)


class AccountController(rest.RestController):
    """Manages operations on account."""

    _custom_actions = {
        'level': ['PUT'],
        'charges': ['GET'],
        'estimate': ['GET'],
        'estimate_per_day': ['GET'],
    }

    #def __init__(self, user_id):
    #    self._id = user_id

    #@wsexpose(models.UserAccount, int)
    @wsexpose(None, int)
    def level(self, level):
        """Update the account's level."""
        account = pecan.request.processor_rpcapi.update_level()
        return "test level"

    #@wsexpose(models.Charges, wtypes.text, datetime.datetime,
    @wsexpose(models.Test)
    def charges(self, type=None, start_time=None,
                end_time=None, limit=None, offset=None):
        """Get this account's charge records."""
        #test_text = pecan.request.conductor_rpcapi.test()
        test_text = pecan.request.processor_rpcapi.test()
        return models.Test(test_text=test_text)

    @wsexpose(int)
    def estimate(self):
        """Estimate the hourly billing resources how many days to owed.
        """

    #@wsexpose(models.Estimate)
    @wsexpose(None)
    def estimate_per_day(self):
        """Get the price per day and the remaining days that the
        balance can support.
        """

    @wsexpose(None)
    def delete(self):
        """Delete the account including the projects that belong to it."""

    #@wsexpose(None, body=models.AdminAccount)
    @wsexpose(None, body=None)
    def post(self, data):
        """Create a new account."""

    #@wsexpose(models.Charge, wtypes.text, body=models.Charge)
    @wsexpose(None, wtypes.text, body=None)
    def put(self, data):
        """Charge the account."""

    #@wsexpose(models.UserAccount)
    @wsexpose(None)
    def get_one(self):
        """Get this account."""

    #@wsexpose(models.UserAccount)
    @wsexpose(None)
    def get_all(self):
        """Get this account."""
