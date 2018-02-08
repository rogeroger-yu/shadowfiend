# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import mock

from shadowfiend.conductor.api import API as conductor_api
from shadowfiend.db.sqlalchemy import api as sql_dbapi
from shadowfiend.services import keystone as ks_client
from shadowfiend.tests.unit.api import base as api_base
from shadowfiend.tests.unit.api import utils as api_utils
from shadowfiend.tests.unit.conductor import utils as conductor_utils


class TestGetAccount(api_base.FunctionalTest):
    def setUp(self):
        super(TestGetAccount, self).setUp()

    def test_get_one(self):
        account = conductor_utils.create_test_account(self.context)
        with mock.patch.object(conductor_api, 'get_account',
                               conductor_utils.get_test_account):
            response = self.get_json('/accounts/%s' % account.user_id)
            self.assertEqual(response['user_id'], account.user_id)

    def test_get_all(self):
        num = 0
        account_list = []
        while num < 3:
            account = conductor_utils.create_test_account(self.context)
            account_list.append(account)
            num += 1

        with mock.patch.object(
            conductor_api, 'get_accounts', conductor_utils.get_test_accounts):
            response = self.get_json('/accounts?limit=2')
            self.assertEqual(2, len(response['accounts']))

    def test_get_one_charge(self):
        num = 0
        account = conductor_utils.create_test_account(self)
        charge_list = []
        while num < 3:
            charge = conductor_utils.create_test_charge(self.context,
                                                        account.user_id)
            charge_list.append(charge)
            num += 1

        with mock.patch.object(
            conductor_api, 'get_charges', conductor_utils.get_test_charges):
            with mock.patch.object(
                conductor_api, 'get_charges_price_and_count',
                conductor_utils.get_test_charges_price_and_count):
                    response = self.get_json('/accounts/%s/charges' %
                                             account['user_id'])
                    self.assertEqual(3, len(response['charges']))

    def test_get_all_charge(self):
        num_1, num_2 = 0, 0
        charge_list = []
        while num_1 < 3:
            account = conductor_utils.create_test_account(self)
            while num_2 < 4:
                charge = conductor_utils.create_test_charge(
                    self.context, account['user_id'])
                charge_list.append(charge)
                num_2 += 1
            num_1 += 1

        def mock_ks_client(*args):
            return {}

        with mock.patch.object(
            conductor_api, 'get_charges', conductor_utils.get_test_charges):
            with mock.patch.object(conductor_api,
                                   'get_charges_price_and_count',
                                   (conductor_utils.
                                    get_test_charges_price_and_count)):
                with mock.patch.object(ks_client, 'get_user',
                                       mock_ks_client):
                    response = self.get_json('/accounts/charges')
                    self.assertEqual(response['total_count'],
                                     len(response['charges']))


class TestPostAccount(api_base.FunctionalTest):
    def setUp(self):
        super(TestPostAccount, self).setUp()

    def test_create_account(self):
        body = api_utils.account_post_data()
        with mock.patch.object(conductor_api, 'create_account',
                               conductor_utils.create_test_account):
            response = self.post_json('/accounts', body)
            self.assertEqual(202, response.status_int)


class TestPutAccount(api_base.FunctionalTest):
    def setUp(self):
        super(TestPutAccount, self).setUp()

    def test_put_account_charge(self):
        body = api_utils.account_put_charge_data()
        account = conductor_utils.create_test_account(self)
        with mock.patch.object(conductor_api, 'charge_account',
                               conductor_utils.charge_test_account):
            response = self.put_json('/accounts/%s' % account.user_id, body)
            self.assertEqual(200, response.status_int)

    def test_put_account_level(self):
        body = api_utils.account_put_level_data()
        account = conductor_utils.create_test_account(self)
        with mock.patch.object(conductor_api, 'change_account_level',
                               conductor_utils.change_test_account_level):
            def _mock_inside(*args, **kwargs):
                pass
            with mock.patch.object(sql_dbapi.Connection,
                                   '_update_params', _mock_inside):
                response = self.put_json('/accounts/%s/level' %
                                         account.user_id, body)
                self.assertEqual(200, response.status_int)


class TestDeleteAccount(api_base.FunctionalTest):
    def setUp(self):
        super(TestDeleteAccount, self).setUp()

    def test_delete_account(self):
        account = conductor_utils.create_test_account(self)

        with mock.patch.object(conductor_api, 'delete_account',
                               conductor_utils.delete_test_account):
            self.delete('/accounts/%s' % account.user_id)
            with mock.patch.object(conductor_api, 'get_account',
                                   conductor_utils.get_test_account):
                response = self.get_json('/accounts/%s' % account.user_id,
                                         expect_errors=True)
                self.assertEqual(404, response.status_int)
                self.assertEqual('application/json', response.content_type)
