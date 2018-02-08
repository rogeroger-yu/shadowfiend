from oslo_utils import uuidutils
from shadowfiend.db import api as db_api
from shadowfiend.db import models as db_models


def get_test_account(**kw):
    attrs = {
        'user_id': kw.get('user_id',
                          ''.join(uuidutils.generate_uuid().split('-'))),
        'domain_id': kw.get('user_id', 'default'),
        'balance': kw.get('balance', 10.0),
        'consumption': kw.get('consumption', 0.0),
        'level': kw.get('level', 4),
        'owed': kw.get('owed', False),
        'deleted': kw.get('deleted', False),
        'owed_at': kw.get('owed_at'),
        'created_at': kw.get('created_at'),
        'updated_at': kw.get('updated_at'),
        'deleted_at': kw.get('delete_at'),
    }
    return attrs


def get_test_project(**kw):
    attrs = {
        'user_id': kw.get('user_id',
                          ''.join(uuidutils.generate_uuid().split('-'))),
        'project_id': kw.get('project_id',
                             ''.join(uuidutils.generate_uuid().split('-'))),
        'domain_id': kw.get('user_id', 'default'),
        'consumption': kw.get('consumption', 0.0),
        'created_at': kw.get('created_at'),
    }
    return attrs


def get_test_charge(**kw):
    attrs = {
        'id': kw.get('id', 42),
        'charge_id': kw.get('user_id', 'default'),
        'user_id': kw.get('user_id',
                          ''.join(uuidutils.generate_uuid().split('-'))),
        'domain_id': kw.get('domain_id', 'default'),
        'value': kw.get('value', 10),
        'type': kw.get('type', 'bonus'),
        'come_from': kw.get('come_from', 'system'),
        'charge_time': kw.get('charge_time', '2018-01-09T03:17:47Z'),
        'trading_number': kw.get('trading_number', None),
        'created_at': kw.get('created_at', '2018-01-09T03:16:47Z'),
        'operator': kw.get('operator', None),
        'remarks': kw.get('remarks', None),
        'updated_at': kw.get('updated_at', '2018-01-09T03:17:47Z'),
        'deleted_at': kw.get('delete_at', '2018-01-09T03:18:47Z'),
    }
    return attrs


def create_test_account(context, **kwargs):
    account = get_test_account(**kwargs)
    dbapi = db_api.get_instance()
    return dbapi.create_account(context, db_models.Account(**account))
