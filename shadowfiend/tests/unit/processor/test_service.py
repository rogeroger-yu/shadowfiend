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

from oslo_config import cfg
from shadowfiend.common import context
from shadowfiend.conductor.api import API as conductor_api
from shadowfiend.processor.service import service
from shadowfiend.processor.service import fetcher
from shadowfiend.tests.unit.conductor import utils as conductor_utils
from shadowfiend.tests.unit.db import base

CONF = cfg.CONF

cfg.CONF.import_group('processor', 'shadowfiend.processor.config')


class TestWorker(base.DbTestCase):
    def setUp(self):
        super(TestWorker, self).setUp()

        ctx = context.make_admin_context(all_tenants=True)
        account = conductor_utils.create_test_account(ctx)
        project = conductor_utils.create_test_project(
            ctx, user_id=account.user_id)
        conductor_utils.create_test_relation(
            ctx,
            user_id=account.user_id,
            project_id=project.project_id)

        class mock_keystone_fetcher(object):
            def get_rate_user(self, *args):
                return account.user_id

        class mock_gnocchi_fetcher(object):
            def get_resources(self, *args):
                return []

            def get_current_consume(self, *args):
                return 0

            def set_state(self, *args):
                pass

        with mock.patch.object(
            fetcher, 'KeystoneFetcher', mock_keystone_fetcher):
            with mock.patch.object(
                fetcher, 'GnocchiFetcher', mock_gnocchi_fetcher):
                self.Worker = service.Worker(ctx, project.project_id, 0)

    def test_owed_action(self):
        project_id = '0eed996268e34f96a30a4a0926822257'
        self.Worker.owed_action(project_id)

    def test_run(self):
        with mock.patch.object(
            conductor_api, 'get_account', conductor_utils.get_test_account):
            with mock.patch.object(conductor_api,
                                   'update_account',
                                   conductor_utils.update_test_account):
                self.Worker.run()


class TestProcessorPeriodTasks(base.DbTestCase):
    def setUp(self):
        super(TestProcessorPeriodTasks, self).setUp()

        class mock_keystone_fetcher(object):
            pass

        class mock_gnocchi_fetcher(object):
            def get_state(self, *args):
                if 'top' and 'shadowfiend' in args:
                    pass
                elif 'bottom' in args:
                    return 0
                elif 'top' and 'cloudkitty' in args:
                    return CONF.processor.process_period + 1

        with mock.patch.object(
            fetcher, 'KeystoneFetcher', mock_keystone_fetcher):
            with mock.patch.object(
                fetcher, 'GnocchiFetcher', mock_gnocchi_fetcher):
                self.Pro_Per = service.ProcessorPeriodTasks(CONF)

    def test_check_state_none_history(self):
        project_id = '0eed996268e34f96a30a4a0926822257'
        next_timestamp = self.Pro_Per._check_state(project_id)
        self.assertEqual(next_timestamp, 0)

    def test_check_state_history(self):
        project_id = '0eed996268e34f96a30a4a0926822257'
        cfg.CONF.set_override('historical_expenses', True, group='processor')
        next_timestamp = self.Pro_Per._check_state(project_id)
        self.assertNotEqual(next_timestamp, 0)

    def test_lock(self):
        project_id = '0eed996268e34f96a30a4a0926822257'
        result = self.Pro_Per._lock(project_id)
        catalog = (u'/var/lib/shadowfiend/locks/'
                   u'shadowfiend-%s' % project_id)
        self.assertEqual(result._name, catalog)
