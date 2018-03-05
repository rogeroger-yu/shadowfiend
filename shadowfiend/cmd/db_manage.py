# -*- coding: utf-8 -*-
# Copyright 2017 Openstack Foundation.
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

"""Starter script for shadowfiend-db-manage."""

from oslo_config import cfg
from shadowfiend.common import context
from shadowfiend.db import migration
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models
from shadowfiend.services import keystone as keystone_client
from shadowfiend.services.gnocchi import GnocchiClient


CONF = cfg.CONF
dbapi = dbapi.get_instance()


def do_version():
    print('Current DB revision is %s' % migration.version())


def do_upgrade():
    migration.upgrade(CONF.command.revision)


def do_stamp():
    migration.stamp(CONF.command.revision)


def do_revision():
    migration.revision(message=CONF.command.message,
                       autogenerate=CONF.command.autogenerate)


def do_init():
    GnocchiClient().init_storage_backend()
    synchronize_database()


def synchronize_database():
    ctx = context.make_admin_context(all_tenants=True)
    context.set_ctx(ctx)

    def _generate_group(_set, _type):
        ids_set = []
        for subset in _set:
            ids_set.append(subset[_type])
        return ids_set

    rate_projects_id = _generate_group(dbapi.get_projects(ctx), 'project_id')
    rate_accounts_id = _generate_group(dbapi.get_accounts(ctx), 'user_id')
    ks_projects = keystone_client.get_project_list()
    ks_users = keystone_client.get_user_list()

    billing_admin = keystone_client.get_user_list(name='billing_admin')[0]
    billing_admin_id = billing_admin.id
    domain_id = billing_admin.domain_id

    for ks_project in ks_projects:
        if ks_project.id not in rate_projects_id:
            dbapi.create_project(ctx,
                                 db_models.Project(
                                     user_id=billing_admin_id,
                                     project_id=ks_project.id,
                                     domain_id=domain_id,
                                     consumption=0))
    for ks_user in ks_users:
        if ks_user.id not in rate_accounts_id:
            dbapi.create_account(ctx,
                                 db_models.Account(
                                     user_id=ks_user.id,
                                     domain_id=domain_id,
                                     balance=0,
                                     consumption=0,
                                     level=4))
            dbapi.charge_account(ctx, user_id=ks_user.id, value=10,
                                 type='bonus', come_from='system')
    context.set_ctx(None)


def add_command_parsers(subparsers):
    parser = subparsers.add_parser('version')
    parser.set_defaults(func=do_version)

    parser = subparsers.add_parser('upgrade')
    parser.add_argument('revision', nargs='?')
    parser.set_defaults(func=do_upgrade)

    parser = subparsers.add_parser('stamp')
    parser.add_argument('revision')
    parser.set_defaults(func=do_stamp)

    parser = subparsers.add_parser('revision')
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')
    parser.set_defaults(func=do_revision)

    parser = subparsers.add_parser('init')
    parser.set_defaults(func=do_init)


command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help='Available commands',
                                handler=add_command_parsers)


def main():
    CONF.register_cli_opt(command_opt)

    CONF(project='shadowfiend')
    CONF.command.func()


if __name__ == '__main__':
    main()
