# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from ipcrawl.utils import read_json
from ipcrawl.utils import to_json

import json
import os


def test_read_json_given_a_file_that_contains_valid_json(tmpdir):
    tmpdir.chdir()
    foo_json = tmpdir.join('foo.json')
    data = dict(name='foo', age=1)
    foo_json.write(
        to_json(
            dict(name='foo', age=1)
        )
    )

    actual = read_json('foo.json')

    assert os.path.isfile('foo.json')
    assert actual == data


def test_to_json_can_read_a_properly_formatted_json_file(tmpdir):
    tmpdir.chdir()
    data = dict(name='foo', age=2)
    actual = to_json(data)

    assert actual == json.dumps(
        data, indent=2, sort_keys=True, ensure_ascii=False,
        separators=(',', ': ')
    )
