# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from socket import inet_aton


import json
import logging
import struct

ENCODING = 'utf-8'

logging.basicConfig(
    level=logging.WARNING,
    format=(
        "%(asctime)s::%(levelname)s::%(filename)10s::%(message)s"
    )
)

log = logging.getLogger('ipcrawl')
log.setLevel(logging.WARNING)


def calculate_position(lexdata, lexpos):
    r"""Given ``lexdata`` get pos from last newline via a 1-based offset

    Example:

        * 0-based postion '#' refers to index == 4.

            .. code-block::

                calculate_position('foo #', 4)  # >>> 4

        * 1-based position, '@' refers to index = 5

            .. code-block::

                calculate_position('\nbar\nfoo @', 9)  # >>> 5

    Args:
        lexdata (str):
            * A string of data
        lexpos (int):
            * A ``int``, referring to the location of your match object.
              This should be 0-based

    Returns:
        (int):
            * with 1-based position.

    """
    # because we are 1-based offset
    lexpos += 1
    last_newline_pos = lexdata.rfind('\n', 0, lexpos) + 1
    return(lexpos - last_newline_pos)


def read_file(filename, mode='r', encoding=ENCODING):
    """Reads a file

    Args:
        filename (str):
            * A path to a filename.
        mode (str):
            * The mode operation. Default ``r``
        encoding (str):
            * The file encoding. Default :class:`ENCODING`

    """
    with open(filename, mode=mode, encoding=encoding) as fd:
        content = fd.read()

    return content


def read_json(filename):
    """Attempt to read a JSON file

    Args:
        (str): A filename path.

    Raises:
        * See :func:`io.open.read`
        * See :func:`json.loads`

    Returns:
        (dict):

    """
    content = read_file(filename)
    data = json.loads(content)
    return data


def to_json(
    data, indent=2, sort_keys=True, ensure_ascii=False, separators=None,
    **kwargs
):
    """Converts from dict to JSON encoded string.

    Args:
        data (dict):
            * The dictionary to convert to a string.
        indent (int):
            * Default ``2``.
        sort_keys (bool):
            * Default ``True``
        ensure_ascii (bool):
            * Default ``False``
        separators (None, list, tuple):
            * When ``None`` defaults to ``(',', ': ')``

    Returns:
        (str): By default a `utf-8` encoded BLOB of JSON text.

    """
    separators = separators or (',', ': ')
    json_str = json.dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        separators=separators,
    )
    return json_str


def sort_ips(ips):
    """Given a list of ips, sort them

    Credit: https://stackoverflow.com/questions/6545023/how-to-sort-ip-addresses-stored-in-dictionary-in-python/6545090#6545090

    Args:
        ips (list, tuple):
            * A ``list`` or ``tuple`` of ips

    """  # noqa
    return sorted(ips, key=lambda ip: struct.unpack('!L', inet_aton(ip))[0])
