# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from contextlib import contextmanager

from ipcrawl.database.models import Base
from ipcrawl.utils import log

from sqlalchemy.orm import sessionmaker

from sqlalchemy import create_engine

Session = sessionmaker()
DEFAULT_DB = 'ipcrawl.sqlite3'


def init_engine(filename=None, **kwargs):
    """Initialize a sqlite3 db engine for sqlalchemy

    Args:
        filename (str):
            * A path to the db filename
        kwargs (dict):
            * Extra key value pairs to pass ``create_engine``

    Returns:
        (Engine): See :class:`sqlalchemy.engine.base.Engine`

    """
    filename = filename or DEFAULT_DB
    db_uri = 'sqlite:///{filename}'.format(filename=filename)
    return create_engine(db_uri, **kwargs)


def init_db(engine=None, filename=None):
    """Create database tables if they do not exist, otherwise do nothing.

    Schema migrations will need to be handled manually.

    """
    filename = filename or DEFAULT_DB
    engine = engine or init_engine(filename)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    return engine


@contextmanager
def session_scope(**kwargs):
    """Provide a transactional scope around a series of operations.

    Borrowed from https://docs.sqlalchemy.org/en/13/orm/session_basics.html

    """
    session = Session(**kwargs)

    if session.bind is None:
        log.info('bind is not set for session, attempting to initialize db.')

        # attempt to initialize the db and recreate the session
        init_db(filename=DEFAULT_DB)
        session = Session(**kwargs)

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
