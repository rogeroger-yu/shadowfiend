import datetime

from oslo_config import cfg
from oslo_log import log
import pecan
from pecan import request
from pecan import rest
from wsme import types as wtypes
from wsmeext.pecan import wsexpose

from shadowfiend.api import acl
from shadowfiend.api.controllers.v1 import models
from shadowfiend.common import constants as const
from shadowfiend.common import exception
from shadowfiend.common import utils
from shadowfiend.common import timeutils
from shadowfiend.common import utils as utils
from shadowfiend.services import keystone

LOG = log.getLogger(__name__)
HOOK = pecan.request


class ExistOrderController(rest.RestController):
    """For one single order, getting its detail consumptions."""

    _custom_actions = {
        'order': ['GET'],
        'close': ['PUT'],
        'activate_auto_renew': ['PUT'],
        'switch_auto_renew': ['PUT'],
        'renew': ['PUT'],
        'resize_resource': ['POST'],
        'delete_resource': ['POST'],
        'stop_resource': ['POST'],
        'start_resource': ['POST'],
        'restore_resource': ['POST'],
    }

    def __init__(self, order_id):
        self._id = order_id

    def _order(self, start_time=None, end_time=None,
               limit=None, offset=None):

        self.conn = pecan.request.db_conn
        try:
            bills = self.conn.get_bills_by_order_id(HOOK.context,
                                                    order_id=self._id,
                                                    start_time=start_time,
                                                    end_time=end_time,
                                                    limit=limit,
                                                    offset=offset)
        except Exception:
            LOG.error('Order(%s)\'s bills not found' % self._id)
            raise exception.OrderBillsNotFound(order_id=self._id)
        return bills

    @wsexpose(None, datetime.datetime, datetime.datetime, int, int)
    def get(self, start_time=None, end_time=None, limit=None, offset=None):
        """Get this order's detail."""

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        bills = self._order(start_time=start_time, end_time=end_time,
                            limit=limit, offset=offset)
        bills_list = []
        for bill in bills:
            bills_list.append(models.Bill.from_db_model(bill))

        total_count = self.conn.get_bills_count(HOOK.context,
                                                order_id=self._id,
                                                start_time=start_time,
                                                end_time=end_time)

        return None.transform(total_count=total_count,
                                      bills=bills_list)

    @wsexpose(models.Order)
    def order(self):
        conn = pecan.request.db_conn
        order = conn.get_order(HOOK.context, self._id)
        return models.Order.from_db_model(order)

    def _validate_resize(self, resize):
        err = None
        if 'resource_type' not in resize:
            err = 'Must specify resource_type'

        resource_type = resize['resource_type']
        if resource_type == 'instance':
            params = ['new_flavor', 'old_flavor',
                      'service', 'region_id']
            for param in params:
                if param not in resize:
                    err = 'Must specify %s' % param
        else:
            if 'quantity' not in resize:
                err = 'Must specify quantity'

        if err:
            LOG.warn(err)
            raise exception.InvalidParameterValue(err=err)


    @wsexpose(models.Order)
    def close(self):
        """Close this order

        Close means set order's status to deleted in database, then stop
        the cron job in apscheduler.
        """
        try:
            order = HOOK.conductor_rpcapi.close_order(HOOK.context, self._id)
        except Exception:
            msg = "Fail to close the order %s" % self._id
            LOG.exception(msg)
            raise exception.DBError(reason=msg)
        return models.Order.from_db_model(order)

    def _validate_renew(self, renew):
        err = None
        if 'method' not in renew or 'period' not in renew:
            err = 'Must specify method and period'
        elif renew['method'] not in ['month', 'year']:
            err = 'Wrong method, should be month or year'
        elif not isinstance(renew['period'], int) or renew['period'] <= 0:
            err = 'Wrong period, should be an integer greater than 0'

        if err:
            LOG.warn(err)
            raise exception.InvalidParameterValue(err=err)


class OrderController(rest.RestController):
    """The controller of resources."""

    #summary = SummaryController()
    #resource = ResourceController()
    #count = CountController()
    #active = ActiveController()
    #stopped = StoppedOrderCountController()
    #reset = ResetOrderController()


    @pecan.expose()
    def _lookup(self, order_id, *remainder):
        if remainder and not remainder[-1]:
            remainder = remainder[:-1]
        if utils.is_uuid_like(order_id):
            return ExistOrderController(order_id), remainder

    @wsexpose(models.Orders, wtypes.text, wtypes.text,
              datetime.datetime, datetime.datetime, int, int, wtypes.text,
              wtypes.text, wtypes.text, wtypes.text, bool, [wtypes.text])
    def get_all(self, type=None, status=None, start_time=None, end_time=None,
                limit=None, offset=None, resource_id=None, region_id=None,
                project_id=None, user_id=None, owed=None, bill_methods=None):
        """Get queried orders
        If start_time and end_time is not None, will get orders that have bills
        during start_time and end_time, or return all orders directly.
        """
        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        limit_user_id = acl.get_limited_to_user(
            request.headers, 'orders_get')

        if limit_user_id:  # normal user
            user_id = None
            projects = keystone.get_project_list(user=limit_user_id)
            _project_ids = [project.id for project in projects]
            if project_id:
                project_ids = ([project_id]
                               if project_id in _project_ids
                               else _project_ids)
            else:
                project_ids = _project_ids
        else:  # accountant
            if project_id:  # look up specified project
                project_ids = [project_id]
            else:  # look up all projects
                project_ids = None

        if project_ids:
            project_ids = list(set(project_ids) - set(cfg.CONF.ignore_tenants))

        conn = pecan.request.db_conn
        orders_db, total_count = conn.get_orders(HOOK.context,
                                                 type=type,
                                                 status=status,
                                                 start_time=start_time,
                                                 end_time=end_time,
                                                 owed=owed,
                                                 limit=limit,
                                                 offset=offset,
                                                 with_count=True,
                                                 resource_id=resource_id,
                                                 bill_methods=bill_methods,
                                                 region_id=region_id,
                                                 user_id=user_id,
                                                 project_ids=project_ids)
        orders = []
        for order in orders_db:
            price = self._get_order_price(order,
                                          start_time=start_time,
                                          end_time=end_time)
            order.total_price = utils._quantize_decimal(price)
            orders.append(models.Order.from_db_model(order))

        return models.Orders.transform(total_count=total_count,
                                       orders=orders)

    def _get_order_price(self, order, start_time=None, end_time=None):
        if not all([start_time, end_time]):
            return order.total_price

        conn = pecan.request.db_conn
        total_price = conn.get_bills_sum(HOOK.context,
                                         start_time=start_time,
                                         end_time=end_time,
                                         order_id=order.order_id)
        return total_price

    @wsexpose(None, body=models.OrderPostBody)
    def post(self, data):
        try:
            order = data.as_dict()
            response = HOOK.conductor_rpcapi.create_order(HOOK.context,
                                                          order)
            LOG.debug('%s Has Been Created' % response['order_id'])

        except Exception as e:
            LOG.error('Fail to create order: %s, for reason %s' %
                      (data.as_dict(), e))

    @wsexpose(None, body=models.OrderPutBody)
    def put(self, data):
        """Change the unit price of the order."""
        conn = pecan.request.db_conn
        try:
            conn.update_order(HOOK.context, **data.as_dict())
        except Exception as e:
            LOG.exception('Fail to update order: %s, for reason %s' %
                          (data.as_dict(), e))
