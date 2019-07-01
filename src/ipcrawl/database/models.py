# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from ipcrawl.utils import log  # noqa

from sqlalchemy import Column
from sqlalchemy import types

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

import uuid

# we define this here since there should only be one and each db should
# reference this instance.
Base = declarative_base()


def generate_uuid():
    """Generates a random UUID string

    """
    return uuid.uuid4().hex


class ModelDictMixin(object):

    def to_dict(self, columns=None):
        """Return model as a ``dict``

        Args:
            columns (list, tuple):
                * When ``None``, returns all columns and values.
                * When ``list`` or ``tuple`` returns only those
                  columns and values

        Returns:
            (dict):
                * With selected columns and values.

        """
        table = Base.metadata.tables[self.__tablename__]
        columns = columns or [f.name.lstrip('_') for f in table.columns]

        return {
            column: getattr(self, column)
            for column in columns
        }


class GeoLite2AsnBlocksIpv4(Base, ModelDictMixin):
    """GeoLite2 City Blocks database model

    References:
        * `GeoIP2 City and Country CSV Databases <https://dev.maxmind.com/geoip/geoip2/geoip2-city-country-csv-databases/>`_
        * `Using Descriptors and Hybrids <https://docs.sqlalchemy.org/en/13/orm/mapped_attributes.html#using-descriptors-and-hybrids/>`_

    Args:
        id (str):
            * The primary key
        network (str):
            * This is the IPv4 network in CIDR format such as “2.21.92.0/29”
        autonomous_system_number (int):
            * The autonomous system number associated with the IP address.
        autonomous_system_organization (str):
            * The organization associated with the registered autonomous
              system number for the IP address.

    """  # noqa
    __tablename__ = "geolite2_asn_blocks_ipv4"

    id = Column(
        types.String(16),
        index=True,
        primary_key=True,
        default=generate_uuid
    )

    network = Column(
        types.String(18),
        nullable=False,
    )

    autonomous_system_number = Column(
        types.Integer(),
    )

    autonomous_system_organization = Column(
        types.String(),
    )

    def __repr__(self):
        return 'GeoLite2AsnBlocksIpv4(id={!r})'.format(self.id)


class GeoLite2CityBlocksIpv4(Base, ModelDictMixin):
    """GeoLite2 City Blocks database model

    References:
        * `GeoIP2 City and Country CSV Databases <https://dev.maxmind.com/geoip/geoip2/geoip2-city-country-csv-databases/>`_

    Args:
        id (str):
            * The primary key
        network (str):
            * This is the IPv4 network in CIDR format such as “2.21.92.0/29”
        geoname_id (int):
            * A unique identifier for the network's location as specified by
              GeoNames. This ID can be used to look up the location
              information in the Location file.
        registered_country_geoname_id (int):
            * The registered country is the country in which the ISP has
              registered the network. This column contains a unique
              identifier for the network's registered country as specified
              by GeoNames. This ID can be used to look up the location
              information in the Location file.
        represented_country_geoname_id (int):
            * The represented country is the country which is represented by
              users of the IP address. For instance, the country represented
              by an overseas military base. This column contains a unique
              identifier for the network's registered country as specified
              by GeoNames. This ID can be used to look up the location
              information in the Location file.
        is_anonymous_proxy (boolean):
            * Deprecated. Please see our GeoIP2 Anonymous IP database to
              determine whether the IP address is used by an anonymizing
              service.
        is_satellite_provider (boolean):
            * Deprecated. Please see our GeoIP2 Anonymous IP database.
        postal_code (str):
            * A postal code close to the user's location. We return the first
              3 characters for Canadian postal codes. We return the
              first 2-4 characters (outward code) for postal codes in the
              United Kingdom.
        latitude (float):
            * The approximate latitude of the postal code, city, subdivision
              or country associated with the IP address.
        longitude (float):
            * The approximate longitude of the postal code, city, subdivision
              or country associated with the IP address.
        accuracy_radius (int):
            * The approximate accuracy radius, in kilometers, around the
              latitude and longitude for the geographical entity
              (country, subdivision, city or postal code) associated with
              the IP address. We have a 67% confidence that the location of
              the end-user falls within the area defined by the accuracy
              radius and the latitude and longitude coordinates.

    """  # noqa
    __tablename__ = "geolite2_city_blocks_ipv4"

    id = Column(
        types.String(16),
        index=True,
        primary_key=True,
        default=generate_uuid
    )

    network = Column(
        types.String(18),
        nullable=False,
    )

    geoname_id = Column(
        types.Integer()
    )

    registered_country_geoname_id = Column(
        types.Integer()
    )

    represented_country_geoname_id = Column(
        types.Integer()
    )

    _is_anonymous_proxy = Column(
        types.Boolean()
    )

    _is_satellite_provider = Column(
        types.Boolean()
    )

    postal_code = Column(
        types.String(9)
    )

    _latitude = Column(
        types.Float()
    )

    _longitude = Column(
        types.Float()
    )

    accuracy_radius = Column(
        types.Integer()
    )

    @hybrid_property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        value = value or float()
        self._latitude = float(value)

    @hybrid_property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        value = value or float()
        self._longitude = float(value)

    @hybrid_property
    def is_anonymous_proxy(self):
        return self._is_anonymous_proxy

    @is_anonymous_proxy.setter
    def is_anonymous_proxy(self, value):
        self._is_anonymous_proxy = bool(int(value))

    @hybrid_property
    def is_satellite_provider(self):
        return self._is_satellite_provider

    @is_satellite_provider.setter
    def is_satellite_provider(self, value):
        self._is_satellite_provider = bool(int(value))

    def __repr__(self):
        return 'GeoLite2CityBlocksIpv4(id={!r})'.format(self.id)
