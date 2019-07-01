# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from copy import deepcopy

from ipcrawl.database import models
from ipcrawl.database import sqlite3
from ipcrawl.utils import log

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import logging
import mock
import os
import pytest


log.setLevel(logging.DEBUG)


@pytest.fixture
def test_db(request, tmpdir):
    tmpdir.chdir()

    def on_call(db_filename=None, **kwargs):
        kwargs.setdefault('echo', True)
        db_filename = db_filename or 'test.sqlite3'

        # we must recreate the Session object since we are using a global
        # static variable. We do this so that one test that modifies the db
        # doesn't cause another test to use the same session. We only care
        # about this here since each test should be isolated.
        sqlite3.Session = sqlite3.sessionmaker()

        engine = sqlite3.init_engine(filename=db_filename)
        sqlite3.init_db(engine=engine)

        return sqlite3.session_scope()

    return on_call


class Test_GeoLite2AsnBlocksIpv4(object):

    def test_saving_a_single_record_given_data_that_contains_all_strings(
        self, test_db
    ):
        data = {
            'network': '223.255.254.0/24',
            'autonomous_system_number': '55415',
            'autonomous_system_organization': 'MARINA BAY SANDS PTE LTD'
        }

        rec = models.GeoLite2AsnBlocksIpv4(**data)

        with test_db() as session:
            session.add(rec)

        results = session.query(models.GeoLite2AsnBlocksIpv4)

        assert len(results.all()) == 1
        assert isinstance(results.first().id, str)
        assert isinstance(results.first().network, str)
        assert isinstance(results.first().autonomous_system_number, int)
        assert isinstance(results.first().autonomous_system_organization, str)

    def test_saving_a_single_record_given_data_that_contains_all_proper_types(
        self, test_db
    ):
        data = {
            'network': '223.255.254.0/24',
            'autonomous_system_number': 55415,
            'autonomous_system_organization': 'MARINA BAY SANDS PTE LTD'
        }

        rec = models.GeoLite2AsnBlocksIpv4(**data)

        with test_db() as session:
            # rec.id = models.generate_uuid()
            session.add(rec)

        results = session.query(models.GeoLite2AsnBlocksIpv4)

        assert len(results.all()) == 1
        assert isinstance(results.first().id, str)
        assert isinstance(results.first().network, str)
        assert isinstance(results.first().autonomous_system_number, int)
        assert isinstance(results.first().autonomous_system_organization, str)

    def test_when_session_is_created_without_initializing_the_db_we_attempt_to_recover_and_initialize_the_db_and_recreate_a_new_session(  # noqa
        self, tmpdir
    ):
        tmpdir.chdir()

        data = {
            'network': '223.255.254.0/24',
            'autonomous_system_number': 55415,
            'autonomous_system_organization': 'MARINA BAY SANDS PTE LTD'
        }
        rec = models.GeoLite2AsnBlocksIpv4(**data)

        # we must recreate the session
        sqlite3.Session = sqlite3.sessionmaker()

        with sqlite3.session_scope() as session:
            session.add(rec)

        results = session.query(models.GeoLite2AsnBlocksIpv4)

        assert len(results.all()) == 1

    def test_attempting_to_save_a_record_to_the_db_that_raises_an_exception_we_should_rollback_the_transaction(  # noqa
        self,
    ):
        # we create a dummy object to represent a sessionmaker instance
        # we will replace the real implementation with this one
        class MockedSession(object):
            bind = None

            def add(*args, **kwargs):
                pass

            def commit(*args, **kwargs):
                raise Exception('boom')

            def rollback(*args, **kwargs):
                pass

            def close(*args, **kwargs):
                pass

        with mock.patch.object(
            sqlite3,
            'Session',
            return_value=MockedSession,
        ):
            data = {
                'network': '223.255.254.0/24',
                'autonomous_system_number': 55415,
                'autonomous_system_organization': 'MARINA BAY SANDS PTE LTD'
            }
            rec = models.GeoLite2AsnBlocksIpv4(**data)

            with pytest.raises(Exception) as exp:
                with sqlite3.session_scope() as session:
                    session.add(rec)

            assert 'boom' in str(exp.value)

    def test__repr__(self):
        data = {
            'network': '223.255.254.0/24',
            'autonomous_system_number': 55415,
            'autonomous_system_organization': 'MARINA BAY SANDS PTE LTD'
        }
        rec = models.GeoLite2AsnBlocksIpv4(**data)

        assert repr(rec) == 'GeoLite2AsnBlocksIpv4(id=None)'


class Test_GeoLite2CityBlocksIpv4(object):

    def test_saving_a_single_record_given_data_that_contains_all_strings(
        self, test_db
    ):
        data = {
            'network': '1.0.0.0/24',
            'geoname_id': '8349238',
            'registered_country_geoname_id': '2077456',
            'represented_country_geoname_id': '',
            'is_anonymous_proxy': '0',
            'is_satellite_provider': '0',
            'postal_code': '5107',
            'latitude': '-34.7825',
            'longitude': '138.6106',
            'accuracy_radius': '100'
        }

        rec = models.GeoLite2CityBlocksIpv4(**data)

        with test_db() as session:
            session.add(rec)

        results = session.query(models.GeoLite2CityBlocksIpv4)
        expected = deepcopy(data)
        expected['id'] = results.first().id
        expected['geoname_id'] = 8349238
        expected['is_anonymous_proxy'] = False
        expected['is_satellite_provider'] = False
        expected['latitude'] = -34.7825
        expected['longitude'] = 138.6106
        expected['accuracy_radius'] = 100
        expected['registered_country_geoname_id'] = 2077456
        expected['represented_country_geoname_id'] = ''

        assert len(results.all()) == 1
        assert results.first().to_dict() == expected

    def test_when_longitude_is_a_string_and_not_a_boolean(self, test_db):
        data = {
            '_is_anonymous_proxy': False,
            '_is_satellite_provider': True,
            'represented_country_geoname_id': '',
            'accuracy_radius': '',
            'geoname_id': '',
            'latitude': 3.141592654,
            'network': '5.145.149.142/32',
            'longitude': '',
            'registered_country_geoname_id': '6252001',
            'postal_code': ''
        }
        rec = models.GeoLite2CityBlocksIpv4(**data)

        with test_db() as session:
            session.add(rec)

    def test_when_latitude_is_a_string_and_not_a_boolean(self, test_db):
        data = {
            '_is_anonymous_proxy': False,
            '_is_satellite_provider': True,
            'represented_country_geoname_id': '',
            'accuracy_radius': '',
            'geoname_id': '',
            'latitude': '',
            'network': '5.145.149.142/32',
            'longitude': 3.141592654,
            'registered_country_geoname_id': '6252001',
            'postal_code': ''
        }
        rec = models.GeoLite2CityBlocksIpv4(**data)

        with test_db() as session:
            session.add(rec)

    def test__repr__(self):
        data = {
            'network': '1.0.0.0/24',
            'geoname_id': 8349238,
            'registered_country_geoname_id': 2077456,
            'represented_country_geoname_id': '',
            'is_anonymous_proxy': False,
            'is_satellite_provider': False,
            'postal_code': '5107',
            'latitude': -34.7825,
            'longitude': 138.6106,
            'accuracy_radius': 100
        }

        # test without id
        rec = models.GeoLite2CityBlocksIpv4(**data)

        assert repr(rec) == 'GeoLite2CityBlocksIpv4(id=None)'
