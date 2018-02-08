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

import datetime
import functools
import os

from decimal import Decimal
from oslo_config import cfg
from oslo_db import api as oslo_db_api
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_log import log
from oslo_utils import timeutils
from oslo_utils import uuidutils

from shadowfiend.common import context as shadow_context
from shadowfiend.common import exception
from shadowfiend.common import utils
from shadowfiend.db import api
from shadowfiend.db import models as db_models
from shadowfiend.db.sqlalchemy import migration
from shadowfiend.db.sqlalchemy import models as sa_models

from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

LOG = log.getLogger(__name__)
CONF = cfg.CONF

_FACADE = None

quantize = utils._quantize_decimal


def require_admin_context(f):
    """Decorator to require admin request context.

    The second argument to the wrapped function must be the context.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        shadow_context.require_admin_context(args[1])
        return f(*args, **kwargs)
    return wrapper


def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`nova.context.authorize_project_context` and
    :py:func:`nova.context.authorize_user_context`.

    The second argument to the wrapped function must be the context.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        shadow_context.require_context(args[1])
        return f(*args, **kwargs)
    return wrapper


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade.from_config(CONF)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return Connection(cfg.CONF)


def model_query(context, model, *args, **kwargs):
    """Query helper for simpler session usage.

    :param session: if present, the session to use
    """

    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)

    if (shadow_context.is_domain_owner_context(context) and
            hasattr(model, 'domain_id')):
        query = query.filter_by(domain_id=context.domain_id)
    if shadow_context.is_user_context(context) and hasattr(model, 'user_id'):
        query = query.filter_by(user_id=context.user_id)
    return query


def paginate_query(context, model, limit=None, offset=None,
                   sort_key=None, sort_dir=None, query=None):
    if not query:
        query = model_query(context, model)
    sort_keys = ['id']
    # support for multiple sort_key
    keys = []
    if sort_key:
        keys = sort_key.split(',')
    for k in keys:
        k = k.strip()
        if k and k not in sort_keys:
            sort_keys.insert(0, k)
    query = _paginate_query(query, model, limit, sort_keys,
                            offset=offset, sort_dir=sort_dir)
    return query.all()


def _paginate_query(query, model, limit, sort_keys, offset=None,
                    sort_dir=None, sort_dirs=None):
    if 'id' not in sort_keys:
        # TODO(justinsb): If this ever gives a false-positive, check
        # the actual primary key, rather than assuming its id
        LOG.warn('Id not in sort_keys; is sort_keys unique?')

    assert(not (sort_dir and sort_dirs))

    # Default the sort direction to ascending
    if sort_dirs is None and sort_dir is None:
        sort_dir = 'desc'

    # Ensure a per-column sort direction
    if sort_dirs is None:
        sort_dirs = [sort_dir for _sort_key in sort_keys]

    assert(len(sort_dirs) == len(sort_keys))

    # Add sorting
    for current_sort_key, current_sort_dir in zip(sort_keys, sort_dirs):
        try:
            sort_dir_func = {
                'asc': asc,
                'desc': desc,
            }[current_sort_dir]
        except KeyError:
            raise ValueError("Unknown sort direction, "
                             "must be 'desc' or 'asc'")
        try:
            sort_key_attr = getattr(model, current_sort_key)
        except AttributeError:
            raise exception.Invalid()
        query = query.order_by(sort_dir_func(sort_key_attr))

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query


class Connection(api.Connection):
    """SqlAlchemy connection."""

    def __init__(self, conf):
        url = conf.database.connection
        if url == 'sqlite://':
            conf.database.connection = \
                os.environ.get('GRINGOTTS_TEST_SQL_URL', url)

    def upgrade(self):
        migration.upgrade()

    def clear(self):
        engine = get_engine()
        for table in reversed(sa_models.Base.metadata.sorted_tables):
            engine.execute(table.delete())

    @staticmethod
    def _transfer_time2str(datetime):
        if datetime is not None:
            return datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            return datetime

    @staticmethod
    def _transfer_decimal2float(date):
        if isinstance(date, Decimal):
            return float(date)
        else:
            return date

    def _transfer(self, model_type):
        model_type.value = self._transfer_decimal2float(
            model_type.value if hasattr(model_type, 'value') else None)
        model_type.balance = self._transfer_decimal2float(
            model_type.balance if hasattr(model_type, 'balance') else None)
        model_type.consumption = self._transfer_decimal2float(
            model_type.consumption if hasattr(model_type, 'consumption')
            else None)
        model_type.user_consumption = self._transfer_decimal2float(
            model_type.user_consumption
            if hasattr(model_type, 'user_consumption') else None)
        model_type.project_consumption = self._transfer_decimal2float(
            model_type.project_consumption
            if hasattr(model_type, 'project_consumption') else None)
        model_type.unit_price = self._transfer_decimal2float(
            model_type.unit_price if hasattr(model_type, 'unit_price')
            else None)
        model_type.total_price = self._transfer_decimal2float(
            model_type.total_price if hasattr(model_type, 'total_price')
            else None)

        model_type.charge_time = self._transfer_time2str(
            model_type.charge_time if hasattr(model_type, 'charge_time')
            else None)
        model_type.created_at = self._transfer_time2str(
            model_type.created_at if hasattr(model_type, 'created_at')
            else None)
        model_type.updated_at = self._transfer_time2str(
            model_type.updated_at if hasattr(model_type, 'updated_at')
            else None)
        model_type.deleted_at = self._transfer_time2str(
            model_type.deleted_at if hasattr(model_type, 'deleted_at')
            else None)
        model_type.cron_time = self._transfer_time2str(
            model_type.cron_time if hasattr(model_type, 'cron_time')
            else None)
        model_type.date_time = self._transfer_time2str(
            model_type.date_time if hasattr(model_type, 'date_time')
            else None)

    @staticmethod
    def _row_to_db_account_model(row):
        return db_models.Account(user_id=row.user_id,
                                 domain_id=row.domain_id,
                                 balance=row.balance,
                                 consumption=row.consumption,
                                 level=row.level,
                                 owed=row.owed,
                                 deleted=row.deleted,
                                 created_at=row.created_at,
                                 updated_at=row.updated_at,
                                 deleted_at=row.deleted_at)

    @staticmethod
    def _row_to_db_project_model(row):
        return db_models.Project(user_id=row.user_id,
                                 project_id=row.project_id,
                                 domain_id=row.domain_id,
                                 consumption=row.consumption,
                                 created_at=row.created_at,
                                 updated_at=row.updated_at)

    @staticmethod
    def _row_to_db_charge_model(row):
        return db_models.Charge(charge_id=row.charge_id,
                                user_id=row.user_id,
                                domain_id=row.domain_id,
                                value=row.value,
                                type=row.type,
                                come_from=row.come_from,
                                trading_number=row.trading_number,
                                operator=row.operator,
                                remarks=row.remarks,
                                charge_time=row.charge_time,
                                created_at=row.created_at,
                                updated_at=row.updated_at)

    @staticmethod
    def _row_to_db_precharge_model(row):
        return db_models.PreCharge(code=row.code,
                                   price=row.price,
                                   used=row.used,
                                   dispatched=row.dispatched,
                                   deleted=row.deleted,
                                   operator_id=row.operator_id,
                                   user_id=row.user_id,
                                   domain_id=row.domain_id,
                                   created_at=row.created_at,
                                   deleted_at=row.deleted_at,
                                   expired_at=row.expired_at,
                                   remarks=row.remarks)

    def _update_params(self, query, ref, filters,
                       params, failed_exception):
        update_filters = {}
        for f in filters:
            update_filters[f] = getattr(ref, f)
        rows_update = query.filter_by(**update_filters).\
            update(params, synchronize_session='evaluate')

        if not rows_update:
            LOG.debug('The row was updated in a concurrent transaction, '
                      'we will fetch another one')
            raise db_exc.RetryRequest(failed_exception)

    def _update_consumption(self, context, session,
                            obj, model, total_price,
                            user_id=False):
        consumption = obj.consumption + total_price
        params = dict(consumption=consumption,
                      updated_at=datetime.datetime.utcnow())
        filters = params.keys()
        filters.append('project_id')
        if user_id:
            filters.append('user_id')
        self._update_params(model_query(context,
                                        model,
                                        session=session),
                            obj, filters, params,
                            exception.ConsumptionUpdateFailed())

    def create_account(self, context, account):
        session = get_session()
        with session.begin():
            account_ref = sa_models.Account()
            account_ref.update(account.as_dict())
            session.add(account_ref)
        self._transfer(account_ref)
        return self._row_to_db_account_model(account_ref).__dict__

    @require_context
    def get_account(self, context, user_id, project_id=None):
        if project_id:
            query = get_session().query(sa_models.Account).\
                filter_by(project_id=project_id)
        else:
            query = get_session().query(sa_models.Account).\
                filter_by(user_id=user_id)
        try:
            account_ref = query.one()
        except NoResultFound:
            raise exception.AccountNotFound(user_id=user_id)
        self._transfer(account_ref)
        return self._row_to_db_account_model(account_ref).__dict__

    @oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
    def delete_account(self, context, user_id):
        """delete the account and projects"""

        session = get_session()
        with session.begin():
            try:
                account = session.query(sa_models.Account).\
                    filter_by(user_id=user_id).one()
            except NoResultFound:
                raise exception.AccountNotFound(user_id=user_id)

            # delete the account
            session.delete(account)

            # delete the projects which are related to the account
            projects = session.query(sa_models.Project).\
                filter_by(user_id=user_id).all()
            for project in projects:
                session.delete(project)

            # delete the user_projects which were related to the account
            user_projects = session.query(sa_models.UsrPrjRelation).\
                filter_by(user_id=user_id).all()
            for user_project in user_projects:
                session.delete(user_project)

    def get_accounts(self, context, user_id=None, read_deleted=False,
                     owed=None, limit=None, offset=None,
                     sort_key=None, sort_dir=None, active_from=None):
        query = get_session().query(sa_models.Account)
        if owed is not None:
            query = query.filter_by(owed=owed)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if active_from:
            query = query.filter(sa_models.Account.updated_at > active_from)
        if not read_deleted:
            query = query.filter_by(deleted=False)

        result = paginate_query(context, sa_models.Account,
                                limit=limit, offset=offset,
                                sort_key=sort_key, sort_dir=sort_dir,
                                query=query)

        accounts = []
        for r in result:
            self._transfer(r)
            accounts.append(self._row_to_db_account_model(r).__dict__)
        return accounts

    def get_accounts_count(self, context, read_deleted=False,
                           user_id=None, owed=None, active_from=None):
        query = get_session().query(
            sa_models.Account,
            func.count(sa_models.Account.id).label('count'))
        if owed is not None:
            query = query.filter_by(owed=owed)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if active_from:
            query = query.filter(sa_models.Account.updated_at > active_from)
        if not read_deleted:
            query = query.filter_by(deleted=False)

        return query.one().count or 0

    @oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
    def change_account_level(self, context, user_id, level, project_id=None):
        session = get_session()
        with session.begin():
            account_ref = (session.query(sa_models.Account).
                           filter_by(user_id=user_id).one())
            params = {'level': level}
            filters = params.keys()
            filters.append('user_id')

            self._update_params(model_query(context,
                                            sa_models.Account,
                                            session=session),
                                account_ref, filters, params,
                                exception.AccountUpdateFailed())

        self._transfer(account_ref)
        return self._row_to_db_account_model(account_ref).__dict__

    @oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
    def charge_account(self, context, user_id, project_id=None,
                       operator=None, **data):
        """Do the charge charge account trick"""

        session = get_session()
        with session.begin():
            account = session.query(sa_models.Account).\
                filter_by(user_id=user_id).\
                one()
            account.balance += Decimal(data['value'])

            if account.balance >= 0:
                account.owed = False

            # add charge records
            if not data.get('charge_time'):
                charge_time = datetime.datetime.utcnow()
            else:
                charge_time = timeutils.parse_isotime(data['charge_time'])

            charge_ref = sa_models.Charge(charge_id=uuidutils.generate_uuid(),
                                          user_id=account.user_id,
                                          domain_id=account.domain_id,
                                          value=data['value'],
                                          type=data.get('type'),
                                          come_from=data.get('come_from'),
                                          trading_number=data.get(
                                              'trading_number'),
                                          charge_time=charge_time,
                                          operator=operator,
                                          remarks=data.get('remarks'))
            session.add(charge_ref)

        self._transfer(charge_ref)
        return self._row_to_db_charge_model(charge_ref).__dict__

    @oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
    def update_account(self, context, user_id, project_id, consumption,
                       **data):
        """Update account"""

        session = get_session()
        with session.begin():
            account = model_query(
                context,
                sa_models.Account,
                session=session).filter_by(user_id=user_id).one()
            balance = account.balance - consumption
            params = dict(balance=balance,
                          updated_at=datetime.datetime.utcnow())
            if balance < 0:
                params.update(owed=True, owed_at=datetime.datetime.utcnow())
            filters = params.keys()
            filters.append('user_id')
            self._update_params(model_query(context,
                                            sa_models.Account,
                                            session=session),
                                account, filters, params,
                                exception.AccountUpdateFailed())

            # Update relation
            user_project = model_query(
                context, sa_models.UsrPrjRelation, session=session).\
                filter_by(user_id=user_id).\
                filter_by(project_id=project_id).\
                one()
            consumption = user_project.consumption + consumption
            params = dict(consumption=consumption,
                          updated_at=timeutils.utcnow())
            filters = params.keys()
            filters.append('user_id')
            filters.append('project_id')
            self._update_params(model_query(context,
                                            sa_models.UsrPrjRelation,
                                            session=session),
                                user_project, filters, params,
                                exception.UserProjectUpdateFailed())

    def get_charges(self, context, user_id=None, project_id=None, type=None,
                    start_time=None, end_time=None,
                    limit=None, offset=None, sort_key=None, sort_dir=None):
        query = get_session().query(sa_models.Charge)

        if project_id:
            query = query.filter_by(project_id=project_id)

        if user_id:
            query = query.filter_by(user_id=user_id)

        if type:
            query = query.filter_by(type=type)

        if all([start_time, end_time]):
            query = query.filter(sa_models.Charge.charge_time >= start_time,
                                 sa_models.Charge.charge_time < end_time)

        result = paginate_query(context, sa_models.Charge,
                                limit=limit, offset=offset,
                                sort_key=sort_key, sort_dir=sort_dir,
                                query=query)

        charges = []
        for r in result:
            self._transfer(r)
            charges.append(self._row_to_db_charge_model(r).__dict__)
        return charges

    def get_charges_price_and_count(self, context, user_id=None,
                                    project_id=None, type=None,
                                    start_time=None, end_time=None):
        query = get_session().query(
            sa_models.Charge,
            func.count(sa_models.Charge.id).label('count'),
            func.sum(sa_models.Charge.value).label('sum'))

        if project_id:
            query = query.filter_by(project_id=project_id)

        if user_id:
            query = query.filter_by(user_id=user_id)

        if type:
            query = query.filter_by(type=type)

        if all([start_time, end_time]):
            query = query.filter(sa_models.Charge.charge_time >= start_time,
                                 sa_models.Charge.charge_time < end_time)

        return (self._transfer_decimal2float(query.one().sum) or 0,
                query.one().count or 0)

    def create_project(self, context, project):
        session = get_session()
        with session.begin():
            project_ref = sa_models.Project(**project.as_dict())
            user_project_ref = sa_models.UsrPrjRelation(**project.as_dict())
            session.add(project_ref)
            session.add(user_project_ref)
        project_ref.created_at = self._transfer_time2str(
            project_ref.created_at)
        return self._row_to_db_project_model(project_ref).__dict__

    @require_context
    def get_billing_owner(self, context, project_id):
        try:
            project = model_query(context, sa_models.Project).\
                filter_by(project_id=project_id).one()
        except NoResultFound:
            raise exception.ProjectNotFound(project_id=project_id)

        try:
            account_ref = model_query(context, sa_models.Account).\
                filter_by(user_id=project.user_id).one()
        except NoResultFound:
            raise exception.AccountNotFound(user_id=project.user_id)

        self._transfer(account_ref)
        return self._row_to_db_account_model(account_ref).__dict__

    def get_project(self, context, project_id):
        try:
            project_ref = get_session().query(sa_models.Project).\
                filter_by(project_id=project_id).one()
        except NoResultFound:
            raise exception.ProjectNotFound(project_id=project_id)

        self._transfer(project_ref)
        return self._row_to_db_project_model(project_ref).__dict__

    @require_context
    def get_relation(self, context, user_id=None,
                     limit=None, offset=None):
        # get user's all historical projects
        query = model_query(context, sa_models.UsrPrjRelation)
        if user_id:
            query = query.filter_by(user_id=user_id)
        user_projects = query.all()

        result = []

        # get project consumption
        for u in user_projects:
            try:
                p = model_query(context, sa_models.Project).\
                    filter_by(project_id=u.project_id).\
                    filter_by(user_id=u.user_id).\
                    one()
            except NoResultFound:
                p = None

            up = db_models.UsrPrjRelation(
                user_id=user_id,
                project_id=u.project_id,
                user_consumption=u.consumption,
                project_consumption=p.consumption if p else u.consumption,
                is_historical=False if p else True,
                created_at=u.created_at)

            self._transfer(up)
            result.append(up.__dict__)

        return result

    @require_context
    def get_projects(self, context, project_ids=None,
                     user_id=None, active_from=None):
        if not project_ids:
            query = model_query(context, sa_models.Project)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if active_from:
                query = query.filter(sa_models.Project.updated_at >
                                     active_from)
            projects = query.all()
            return (self._row_to_db_project_model(p) for p in projects)
        else:
            result = get_session().query(sa_models.Project).\
                filter(sa_models.Project.project_id.in_(project_ids)).\
                all()

            projects = []
            for r in result:
                self._transfer(r)
                projects.append(self._row_to_db_project_model(r).__dict__)
            return projects

    @oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
    def change_billing_owner(self, context, project_id, user_id):
        session = get_session()
        with session.begin():
            # ensure user exists
            try:
                model_query(context, sa_models.Account).\
                    filter_by(user_id=user_id).one()
            except NoResultFound:
                LOG.error("Could not find the user: %s" % user_id)
                raise exception.AccountNotFound(user_id=user_id)

            # ensure project exists
            try:
                project = model_query(
                    context, sa_models.Project, session=session).\
                    filter_by(project_id=project_id).\
                    one()
            except NoResultFound:
                LOG.error('Could not find the project: %s' % project_id)
                raise exception.ProjectNotFound(project_id=project_id)

            # change payer of this project
            params = dict(user_id=user_id)
            filters = params.keys()
            filters.append('project_id')
            self._update_params(model_query(context,
                                            sa_models.Project,
                                            session=session),
                                project, filters, params,
                                exception.ProjectUpdateFailed())

            # add/update relationship between user and project
            try:
                user_project = model_query(
                    context, sa_models.UsrPrjRelation, session=session).\
                    filter_by(user_id=user_id).\
                    filter_by(project_id=project_id).\
                    one()
                params = dict(updated_at=timeutils.utcnow())
                filters = params.keys()
                filters.append('user_id')
                filters.append('project_id')
                self._update_params(model_query(context,
                                                sa_models.UsrPrjRelation,
                                                session=session),
                                    user_project, filters, params,
                                    exception.UserProjectUpdateFailed())
            except NoResultFound:
                session.add(
                    sa_models.UsrPrjRelation(user_id=user_id,
                                             project_id=project_id,
                                             consumption='0',
                                             domain_id=project.domain_id))

    def _check_if_account_charged(self, account):
        if not account.owed:
            return True
        return False

    def _check_if_account_first_owed(self, account):
        if account.level == 9:
            return False
        if not account.owed and account.balance <= 0:
            return True
        else:
            return False
