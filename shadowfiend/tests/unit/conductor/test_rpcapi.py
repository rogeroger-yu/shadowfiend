#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Unit Tests for :py:class:`shadowfiend.conductor.rpcapi.API`.
"""

import mock

from shadowfiend.conductor import api as conductor_rpcapi
from shadowfiend.tests.unit.db import base
from shadowfiend.tests.unit.db import utils as dbutils


class RPCAPITestCase(base.DbTestCase):

    def setUp(self):
        super(RPCAPITestCase, self).setUp()
        self.fake_account = dbutils.get_test_account(driver='fake-driver')
        self.fake_project = dbutils.get_test_project(driver='fake-driver')

    def _test_rpcapi(self, method, rpc_method, **kwargs):
        rpcapi_cls = kwargs.pop('rpcapi_cls', conductor_rpcapi.API)
        rpcapi = rpcapi_cls(topic='fake-topic')

        expected_retval = 'hello world' if rpc_method == '_call' else None

        expected_topic = 'fake-topic'
        if 'host' in kwargs:
            expected_topic += ".%s" % kwargs['host']

        target = {
            "topic": expected_topic,
            "version": kwargs.pop('version', 1.0)
        }

        self.fake_args = None
        self.fake_kwargs = None

        def _fake_prepare_method(*args, **kwargs):
            for kwd in kwargs:
                self.assertEqual(target[kwd], kwargs[kwd])
            return rpcapi._client

        def _fake_rpc_method(*args, **kwargs):
            self.fake_args = args
            self.fake_kwargs = kwargs
            if expected_retval:
                return expected_retval

        with mock.patch.object(rpcapi._client, "prepare") as mock_prepared:
            mock_prepared.side_effect = _fake_prepare_method

            with mock.patch.object(rpcapi, rpc_method) as mock_method:
                mock_method.side_effect = _fake_rpc_method
                retval = getattr(rpcapi, method)(**kwargs)
                self.assertEqual(expected_retval, retval)

    def test_account_create(self):
        self._test_rpcapi('create_account',
                          '_call',
                          version='1.0',
                          context=self.context,
                          account=self.fake_account)

    def test_account_delete(self):
        self._test_rpcapi('delete_account',
                          '_call',
                          version='1.0',
                          context=self.context,
                          user_id=self.fake_account['user_id'])

    def test_account_update(self):
        self._test_rpcapi('update_account',
                          '_call',
                          version='1.1',
                          context=self.context,
                          consumption=10,
                          user_id=self.fake_account['user_id'],
                          project_id=self.fake_project['project_id'])
