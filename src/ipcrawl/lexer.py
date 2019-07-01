# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from ipcrawl.utils import calculate_position

from ipaddress import ip_address
from sly import Lexer

# from sly import Parser


def create_lexer(text):
    lexer = CrawlLexer()
    return [token for token in lexer.tokenize(text)]


class CrawlLexer(Lexer):

    # our lexer tokens
    tokens = {
        IP4ADDR,  # noqa
    }

    # stuff we want to ignore while lexing
    ignore = ' .,!\t\r'
    ignore_word = r'[a-zA-Z]+'

    @_(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    def IP4ADDR(self, t):
        # verify value is actually an ip4 address or raise error
        val = ip_address(t.value)
        t.value = val.compressed

        return t

    @_(r'\n+')
    def newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        pos = calculate_position(
            lexdata=self.text,
            lexpos=t.index,
        )
        err_msg = (
            "Illegal character at line: '{0}'"
            " position: '{1}' value: '{2}'"
            "\n"
        ).format(
            t.lineno,
            pos,
            t.value
        )
        self.index += 1

        raise ValueError(err_msg)
