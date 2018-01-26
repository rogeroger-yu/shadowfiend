# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools

import shadowfiend.api.app
import shadowfiend.common.service
import shadowfiend.conductor.config
import shadowfiend.processor.config
import shadowfiend.db


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(shadowfiend.api.OPTS,
                         shadowfiend.api.app.auth_opts,
                         shadowfiend.common.service.service_opts,
                         )),
        ('api', shadowfiend.api.app.api_opts),
        ('conductor', shadowfiend.conductor.config.SERVICE_OPTS),
        ('processor', shadowfiend.processor.config.SERVICE_OPTS),
        ('database', shadowfiend.db.sql_opts),
    ]
