# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy
import os

import fixtures
import mock
from oslo_config import cfg
from oslo_log import log
import oslo_messaging
from oslotest import base
import pecan
import testscenarios

from shadowfiend.common import context as shadowfiend_context
from shadowfiend.common import keystone as shadowfiend_keystone
from shadowfiend.tests import conf_fixture
from shadowfiend.tests import fake_notifier
from shadowfiend.tests import policy_fixture


CONF = cfg.CONF
try:
    log.register_options(CONF)
except cfg.ArgsAlreadyParsedError:
    pass
CONF.set_override('use_stderr', False)


class BaseTestCase(testscenarios.WithScenarios, base.BaseTestCase):
    """Test base class."""

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.addCleanup(cfg.CONF.reset)


class TestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        token_info = {
            'token': {
                'project': {
                    'id': 'fake_project'
                },
                'user': {
                    'id': 'fake_user'
                }
            }
        }

        trustee_domain_id = '12345678-9012-3456-7890-123456789abc'

        self.context = shadowfiend_context.RequestContext(
            auth_token_info=token_info,
            project_id='fake_project',
            user_id='fake_user',
            is_admin=True)

        self.global_mocks = {}

        self.keystone_client = shadowfiend_keystone.KeystoneClientV3(
            self.context)

        self.policy = self.useFixture(policy_fixture.PolicyFixture())

        self.useFixture(fixtures.MockPatchObject(
            oslo_messaging, 'Notifier',
            fake_notifier.FakeNotifier))
        self.addCleanup(fake_notifier.reset)

        def make_context(*args, **kwargs):
            # If context hasn't been constructed with token_info
            if not kwargs.get('auth_token_info'):
                kwargs['auth_token_info'] = copy.deepcopy(token_info)
            if not kwargs.get('project_id'):
                kwargs['project_id'] = 'fake_project'
            if not kwargs.get('user_id'):
                kwargs['user_id'] = 'fake_user'

            context = shadowfiend_context.RequestContext(*args, **kwargs)
            return shadowfiend_context.RequestContext.from_dict(
                context.to_dict())

        p = mock.patch.object(shadowfiend_context, 'make_context',
                              side_effect=make_context)

        self.global_mocks['shadowfiend.common.context.make_context'] = p

        q = mock.patch.object(shadowfiend_keystone.KeystoneClientV3,
                              'trustee_domain_id',
                              return_value=trustee_domain_id)

        self.global_mocks[('shadowfiend.common.keystone.'
                           'KeystoneClientV3.trustee_domain_id')] = q

        self.mock_make_context = p.start()
        self.addCleanup(p.stop)

        self.mock_make_trustee_domain_id = q.start()
        self.addCleanup(q.stop)

        self.useFixture(conf_fixture.ConfFixture())
        self.useFixture(fixtures.NestedTempfile())

        def reset_pecan():
            pecan.set_config({}, overwrite=True)

        self.addCleanup(reset_pecan)

    def start_global(self, name):
        self.global_mocks[name].start()

    def stop_global(self, name):
        self.global_mocks[name].stop()

    def config(self, **kw):
        """Override config options for a test."""
        group = kw.pop('group', None)
        for k, v in kw.items():
            CONF.set_override(k, v, group)

    def get_path(self, project_file=None):
        """Get the absolute path to a file. Used for testing the API.

        :param project_file: File whose path to return. Default: None.
        :returns: path to the specified file, or path to project root.
        """
        root = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '..',
                                            '..',
                                            )
                               )
        if project_file:
            return os.path.join(root, project_file)
        else:
            return root
