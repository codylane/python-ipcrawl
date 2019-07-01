# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from tests.conftest import PROJECT_ROOT_DIR

import os
import pytest


class Test_CrawlLexer(object):

    @pytest.mark.parametrize(
        'invalid_input, err_msg_data',
        [
            pytest.param(
                '1.2.3.4 @',
                dict(lineno=1, pos=9, value='@'),
            ),
            pytest.param(
                (
                    '1.2.3.4'
                    '\n'
                    '\n'
                    '@'
                ),
                dict(lineno=3, pos=1, value='@'),
            ),
        ]
    )
    def test_lexer_when_given_input_that_should_raise_an_error(
        self, invalid_input, err_msg_data, lexer_input
    ):
        err_msg = (
            "Illegal character at line: '{}'"
            " position: '{}' value: '{}'"
        ).format(
            err_msg_data['lineno'],
            err_msg_data['pos'],
            err_msg_data['value'],
        )

        with pytest.raises(ValueError) as exp:
            lexer_input(invalid_input)

        assert err_msg in str(exp.value)

    @pytest.mark.parametrize(
        'ip',
        [
            '1.2.3.4',
            '192.168.1.0',
            '255.255.255.0',
        ]
    )
    def test_lexer_will_filter_out_valid_ipv4_addresses(
        self, ip, lexer_input,
    ):
        result = lexer_input(ip)
        assert result[0].type == 'IP4ADDR'
        assert result[0].value == ip

    @pytest.mark.parametrize(
        'invalid_input',
        [
            pytest.param('lowercase'),
            pytest.param('UPPERCASE'),
            pytest.param('comboPLATER')
        ]
    )
    def test_lexer_will_ignore_lower_and_uppercase_alpha_chars(
        self, invalid_input, lexer_input,
    ):
        result = lexer_input(invalid_input)
        assert result == []

    @pytest.mark.parametrize(
        'invalid_input',
        [
            pytest.param('\t'),
            pytest.param('\r'),
            pytest.param('\n'),
            pytest.param(' '),
            pytest.param('  '),
        ]
    )
    def test_lexer_will_ignore_whitespace(
        self, invalid_input, lexer_input,
    ):
        result = lexer_input(invalid_input)
        assert result == []

    @pytest.mark.parametrize(
        'invalid_input',
        [
            pytest.param('!'),
            pytest.param(','),
            pytest.param('.'),
        ]
    )
    def test_lexer_will_ignore_special_chars(
        self, invalid_input, lexer_input,
    ):
        result = lexer_input(invalid_input)
        assert result == []

    def test_lexer_will_lex_the_dataset_that_we_were_given_matches_5000_total_ips(  # noqa
        self, lexer_input
    ):
        parse_filename = os.path.join(
            PROJECT_ROOT_DIR,
            'data',
            'parse.data'
        )
        with open(parse_filename, mode='r') as fd:
            content = fd.read()

        result = lexer_input(content)
        assert len(result) == 5000
