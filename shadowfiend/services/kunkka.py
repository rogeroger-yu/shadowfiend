#!/usr/bin/env python
# encoding: utf-8


import logging as log
import requests

from oslo_config import cfg

from shadowfiend.common import exception
from shadowfiend.services import wrap_exception
from shadowfiend.services import keystone


LOG = log.getLogger(__name__)


@wrap_exception(exc_type='get', with_raise=False)
def get_uos_user(user_id):
    # NOTE(chengkun): Now The user's detail info is stored in kunkka,
    # so we should use kunkka api to get user info.
    ks_client = keystone.KeystoneClient()
    ks_cfg = cfg.CONF.keystone_authtoken
    auth_url = '%s://%s' % (ks_cfg.auth_protocol, ks_cfg.auth_host)
    url = auth_url + '/api/v1/user/%s' % user_id
    r = requests.get(url,
                     headers={'Content-Type': 'application/json',
                              'X-Auth-Token': ks_client.get_token()})
    if r.status_code == 404:
        LOG.warn("can't not find user %s from kunkka" % user_id)
        raise exception.NotFound()
    return r.json()
