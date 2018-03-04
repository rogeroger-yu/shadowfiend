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

from glanceclient import client as glance_client
from shadowfiend.services import glance
from shadowfiend.tests.unit.db import base


def mock_client_init(self):
    self.glance_client = glance_client.Client(
        version='2',
        session=None,
        auth_url=None)


class mock_glance_client(object):
    def __init__(*args, **kwargs):
        pass

    class images(object):
        @staticmethod
        def delete(*args):
            pass


class TestDropGlanceResource(base.DbTestCase):
    def setUp(self):
        super(TestDropGlanceResource, self).setUp()

        with mock.patch.object(
            glance.GlanceClient, '__init__', mock_client_init):
            with mock.patch.object(
                glance_client, 'Client', mock_glance_client):
                self.client = glance.GlanceClient()

    def test_delete_image(self):
        self.client.delete_image('5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')

    def test_drop_image(self):
        with mock.patch.object(
            glance_client, 'Client', mock_glance_client):
            glance.drop_resource('image',
                                 '5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')
