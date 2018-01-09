# -*- coding: utf-8 -*-
# Copyright 2014 Objectif Libre
#
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

"""Base classes for storage engines
"""
import abc
import six

from oslo_config import cfg
from oslo_db import concurrency as db_concurrency


CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'shadowfiend.db.sqlalchemy.api'}
IMPL = db_concurrency.TpoolDbapiWrapper(CONF, _BACKEND_MAPPING)


def get_instance():
    """Return a DB API instance."""
    return IMPL


@six.add_metaclass(abc.ABCMeta)
class StorageEngine(object):
    """Base class for storage engines."""

    @abc.abstractmethod
    def get_connection(self, conf):
        """Return a Connection instance based on the configuration settings."""


@six.add_metaclass(abc.ABCMeta)
class Connection(object):
    """Base class for storage system connections."""

    @abc.abstractmethod
    def __init__(self, conf):
        """Constructor."""

    @abc.abstractmethod
    def upgrade(self):
        """Migrate the database to `version` or the most recent version."""
