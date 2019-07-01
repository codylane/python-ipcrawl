# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from ipcrawl.lexer import create_lexer

import os
import pytest

PROJECT_ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


@pytest.fixture
def lexer_input():
    """A test fixture for feeding a string into our lexer

    """
    def on_call(string):
        return create_lexer(string)
    return on_call
