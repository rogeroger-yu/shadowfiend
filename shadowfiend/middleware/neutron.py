import json
import re
import uuid
from stevedore import extension

import logging
from oslo_config import cfg

from shadowfiend.common import constants as const
from shadowfiend.middleware import base
from shadowfiend.services import neutron


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

UUID_RE = r'([0-9a-f]{32}' \
    r'|[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})'
RESOURCE_RE = r'(routers|floatingips|lbaas/listeners)'
DEFAULT_RATE_LIMIT = 5 * 1024


class RateLimitItem(base.ProductItem):
    service = const.SERVICE_NETWORK

    def get_product_name(self, body):
        return const.PRODUCT_FLOATINGIP

    def get_resource_volume(self, env, body):
        rate_limit = int(body['floatingip'].get(
            'rate_limit', DEFAULT_RATE_LIMIT))
        if rate_limit == 0:
            raise exception.InvalidParameterValue(
                'rate limit should greater than 0')
        if rate_limit < 1024:
            return 1
        else:
            return int(rate_limit / 1024)


class RouterItem(base.ProductItem):
    service = const.SERVICE_NETWORK

    def get_product_name(self, body):
        return const.PRODUCT_ROUTER


class ConnectionLimitItem(base.ProductItem):
    service = const.SERVICE_NETWORK

    def get_product_name(self, body):
        return const.PRODUCT_LISTENER

    def get_resource_volume(self, env, body):
        return int(body['listener'].get('connection_limit')) / 1000


class NeutronBillingProtocol(base.BillingProtocol):

    def __init__(self, app, conf):
        super(NeutronBillingProtocol, self).__init__(app, conf)
        self.resource_regex = re.compile(
            r'^/%s/%s([.][^.]+)?$' % (RESOURCE_RE, UUID_RE), re.UNICODE)
        self.create_resource_regex = re.compile(
            r'^/%s([.][^.]+)?$' % RESOURCE_RE, re.UNICODE)

        self.change_fip_ratelimit_regex = re.compile(
            r'^/(floatingips)/%s/'
            r'update_floatingip_ratelimit([.][^.]+)?$' % (UUID_RE))
        self.update_listener_regex = re.compile(
            r'^/(lbaas/listeners)/%s([.][^.]+)?$' % (UUID_RE))

        self.delete_loadbalancer_regex = re.compile(
            r'^/(lbaas/loadbalancers)/%s([.][^.]+)?$' % (UUID_RE))

        self.position = 1
        self.black_list += [
            self.change_fip_ratelimit_action,
            self.update_listener,
            self.switch_listener,
        ]
        self.resource_regexs = [
            self.resource_regex,
            self.change_fip_ratelimit_regex,
            self.update_listener_regex,
        ]
        self.no_billing_resource_regexs = [
            self.delete_loadbalancer_regex,
        ]
        self.resize_resource_actions = [
            self.change_fip_ratelimit_action,
            self.update_listener,
        ]
        self.stop_resource_actions = [
            self.stop_listener_action,
        ]
        self.start_resource_actions = [
            self.start_listener_action,
        ]
        self.no_billing_resource_actions = [
            self.delete_loadbalancer_action,
        ]

        self.no_billing_resource_method = {
            'delete_lbaas/loadbalancers': self.delete_loadbalancer,
        }

        self.product_items = {}
        self._setup_product_extensions(self.product_items)

    def _setup_product_extensions(self, product_items):
        names = ['floatingip', 'router', 'listener']
        for name in names:
            product_items[name] = extension.ExtensionManager(
                namespace='shadowfiend.%s.product_items' % name,
                invoke_on_load=True,
                invoke_args=(self.gclient,))

    def check_if_resize_action_success(self, resource_type, result):
        if resource_type == const.RESOURCE_LISTENER:
            return 'listener' in result[0]
        elif resource_type == const.RESOURCE_FLOATINGIP:
            return 'rate_limit' in result[0]

    def check_if_stop_action_success(self, resource_type, result):
        if resource_type == const.RESOURCE_LISTENER:
            return 'listener' in result[0]

    def check_if_start_action_success(self, resource_type, result):
        if resource_type == const.RESOURCE_LISTENER:
            return 'listener' in result[0]

    def change_fip_ratelimit_action(self, method, path_info, body):
        if method == ('PUT' and
                      self.change_fip_ratelimit_regex.search(path_info)):
            return True
        return False

    def switch_listener(self, method, path_info, body):
        if method == ('PUT' and
                      self.update_listener_regex.search(path_info) and
                      'admin_state_up' in body['listener']):
            return True
        return False

    def stop_listener_action(self, method, path_info, body):
        if (self.switch_listener(method, path_info, body) and not
                body['listener']['admin_state_up']):
            return True
        return False

    def start_listener_action(self, method, path_info, body):
        if (self.switch_listener(method, path_info, body) and
                body['listener']['admin_state_up']):
            return True
        return False

    def delete_loadbalancer_action(self, method, path_info, body):
        if (method == 'PUT' and
                self.delete_loadbalancer_regex.search(path_info)):
            return True
        return False

    def delete_loadbalancer(self, env, start_response,
                            method, path_info, body):
        lb_id = self.get_resource_id(path_info, self.position)
        lb = neutron.loadbalancer_get(lb_id, CONF.billing.region_name)
        listeners = lb['listeners']
        app_result = self.app(env, start_response)
        if not app_result[0]:
            for listener in listeners:
                success, result = self.get_order_by_resource_id(
                    env, start_response, listener)
                if not success:
                    continue

                order = result
                success, result = self.delete_resource_order(
                    env, start_response, order['order_id'], order['type'])
                if not success:
                    continue

        return app_result

    def update_listener(self, method, path_info, body):
        if method == ('PUT' and
                      self.update_listener_regex.search(path_info) and
                      'connection_limit' in body['listener']):
            return True
        return False

    def parse_app_result(self, body, result, user_id, project_id):
        resources = []
        try:
            result = json.loads(result[0])
            if 'floatingip' in result:
                fip = result['floatingip']
                resources.append(base.Resource(
                    resource_id=fip['id'],
                    resource_name=fip.get('name'),
                    type=const.RESOURCE_FLOATINGIP,
                    status=const.STATE_RUNNING,
                    user_id=user_id,
                    project_id=project_id
                ))
            elif 'router' in result:
                router = result['router']
                resources.append(base.Resource(
                    resource_id=router['id'],
                    resource_name=router.get('name'),
                    type=const.RESOURCE_ROUTER,
                    status=const.STATE_RUNNING,
                    user_id=user_id,
                    project_id=project_id
                ))
            elif 'listener' in result:
                listener = result['listener']
                resources.append(base.Resource(
                    resource_id=listener['id'],
                    resource_name=listener.get('name'),
                    type=const.RESOURCE_LISTENER,
                    status=const.STATE_RUNNING,
                    user_id=user_id,
                    project_id=project_id
                ))
        except Exception:
            return []
        return resources

    def create_order(self, env, start_response, body,
                     unit_price, unit, period, renew, resource):
        order_id = str(uuid.uuid4())

        for ext in self.product_items[resource.type].extensions:
            state = ext.name.split('_')[0]
            ext.obj.create_subscription(env, body, order_id, type=state)
        self.gclient.create_order(order_id,
                                  CONF.billing.region_name,
                                  unit_price,
                                  unit,
                                  period=period,
                                  renew=renew,
                                  **resource.as_dict())

    def get_order_unit_price(self, env, body, method):
        unit_price = 0
        name = body.keys()[0]
        for ext in self.product_items[name].extensions:
            if ext.name.startswith('running'):
                price = ext.obj.get_unit_price(env, body, method)
                unit_price += price
        return unit_price


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def bill_filter(app):
        import pdb;pdb.set_trace()
        return NeutronBillingProtocol(app, conf)
    return bill_filter
