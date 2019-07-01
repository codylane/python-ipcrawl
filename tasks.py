#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from glob import glob
from invoke import task

import json

from ipcrawl.lexer import create_lexer
from ipcrawl.utils import read_json
from ipcrawl.utils import sort_ips
from ipcrawl.utils import to_json

from ipcrawl.database import models
from ipcrawl.database import sqlite3

from shutil import rmtree

from urllib import parse as urlparse

import csv
import hashlib
import logging
import os
import requests
import shutil
import zipfile

PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

BANDIT_TARGET_DIRS = [
    os.path.relpath(
        os.path.join(PROJECT_ROOT_DIR, 'src', 'ipcrawl')
    ),
]

PROJECT_NAME = os.path.basename(PROJECT_ROOT_DIR)

GEOLITE_BASE_URI = 'http://localhost:8080/'
GEOLITE_BASE_URI = 'https://geolite.maxmind.com/download/geoip/database/'


logging.basicConfig(
    level=logging.WARNING,
    format=(
        "%(asctime)s::%(levelname)s::%(filename)10s::%(message)s"
    )
)

log = logging.getLogger('ipcrawl')
log.setLevel(logging.WARNING)


def md5_checksum(filename, blocksize=65536):
    md5 = hashlib.md5()
    try:
        with open(os.path.realpath(filename), 'rb') as infile:
            block = infile.read(blocksize)
            while block:
                md5.update(block)
                block = infile.read(blocksize)
        return md5.hexdigest()
    except IOError:
        pass


def unzip_file(filename, directory):
    zipf = zipfile.ZipFile(filename)
    zipf.extractall(directory)


def rename_directory(src, dst, **kwargs):
    unpack_directory = glob(src, **kwargs)

    if unpack_directory:
        src = unpack_directory[0]

        if os.path.isdir(dst):
            shutil.rmtree(dst)

        shutil.move(src, dst)


def remove_file(filename, whitelist=None, **kwargs):
    filenames = glob(filename, **kwargs)
    whitelist = whitelist or []

    for filename in filenames:
        if os.path.isfile(filename):
            if os.path.basename(filename) in whitelist:
                continue

            os.unlink(filename)


def validate_md5_checksum(filename, expected):
    actual_md5 = md5_checksum(filename)
    expected_md5 = expected

    if os.path.isfile(expected):
        with open(expected, 'r') as fd:
            expected_md5 = fd.read().strip()

    if actual_md5 != expected_md5:
        err_msg = (
            'MD5 checksum mismatch for {filename},'
            ' expected {expected} to equal {actual}'
        ).format(
            filename=filename,
            expected=expected_md5,
            actual=actual_md5,
        )
        raise ValueError(err_msg)


def get_request(url, save_as=None, save_mode='wb', **kwargs):
    resp = requests.get(url, **kwargs)

    if resp.status_code != 200:
        err_msg = 'url={} status_code={} reason={}'.format(
            url,
            resp.status_code,
            resp.reason,
        )
        raise ValueError(err_msg)

    if save_as:
        if resp.encoding is None:
            resp.encoding = 'utf-8'

        with open(save_as, save_mode) as fd:
            shutil.copyfileobj(resp.raw, fd)

    return resp


@task
def build_sdist(
    c, echo=True, hide=False, pty=True
):
    """Builds the package

    """
    default_args = [
        'python',
        'setup.py',
        'sdist',
    ]
    cmd = ' '.join(default_args)

    with c.cd(PROJECT_ROOT_DIR):
        c.run(cmd, echo=echo, hide=hide, pty=pty)


@task(
    incrementable=['level'],
)
def bandit(
    c, level=0, dirs=None, format=None, output=None, echo=True, pty=True
):
    """Runs bandit security linter

    """
    format = format or 'json'
    output = output or 'bandit.{}'.format(format)
    output_file = os.path.relpath(
        os.path.join(PROJECT_ROOT_DIR, 'reports', output)
    )

    target_dirs = dirs or ' '.join(BANDIT_TARGET_DIRS)

    args = [
        'bandit',
        '-r',
    ]

    if format:
        args.append(
            '-f {}'.format(format)
        )

    if output_file:
        args.append(
            '-o {}'.format(output_file)
        )

    if level:
        args.append('-' + 'l' * level)

    args.append(target_dirs)

    cmd = ' '.join(args)
    c.run(cmd, echo=echo, pty=pty)

    if output_file:
        c.run('git add {}'.format(output_file))


@task
def benchmark_raw_csv(
    c, csv_filename, as_raw=True, as_dict=True, number=100
):
    """Perform timeit calculations on reading CSVs as raw file or into a dict

    """
    import csv
    from timeit import timeit

    def as_raw_test(filename):
        with open(filename, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            [_ for _ in reader]

    def as_dict_test(filename):
        with open(filename, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            [_ for _ in reader]

    results = {
        'as_raw': None,
        'as_dict': None,
    }

    if as_raw:
        results['as_raw'] = timeit(
            lambda: as_raw_test(csv_filename), number=number
        )

    if as_dict:
        results['as_dict'] = timeit(
            lambda: as_dict_test(csv_filename), number=number
        )

    results['summary'] = {
        'number': number,
        'tested_reading_raw_csv': as_raw,
        'tested_reading_raw_csv_into_dict': as_dict,
    }

    result_as_json = to_json(results)
    print(result_as_json)


@task
def clean(c, dir=PROJECT_ROOT_DIR, echo=False):
    """Cleans all compiled artifacts recursively

    """
    file_patterns = [
        '*.csv',
        '*.pyc',
        '*.retry',
        '.coverage',
    ]

    dir_patterns = [
        'dist',
        '*.egg-info',
        '.tox',
        '__pycache__',
        'tmp',
    ]

    for pattern in file_patterns:
        cmd = 'find {} -name "{}" -type f | xargs rm -f'.format(dir, pattern)
        c.run(cmd, echo=echo)

    for pattern in dir_patterns:
        cmd = 'find {} -name "{}" -type d | xargs rm -rf'.format(dir, pattern)
        c.run(cmd, echo=echo)

    with c.cd(PROJECT_ROOT_DIR):
        c.run('pip install -e .')


@task
def extract_ips(c, filename):
    """Extracts all IPv4 ip addresses out of @filename

    """
    with open(filename, mode='r') as fd:
        content = fd.read()

    sorted_ips = sort_ips([t.value for t in create_lexer(content)])

    tables = [
        models.GeoLite2AsnBlocksIpv4,
        models.GeoLite2CityBlocksIpv4,
    ]

    with open('results.json', mode='w') as fd:
        for ip in sorted_ips:
            network = '.'.join(ip.split('.')[0:3])
            network_wildcard = '{}%'.format(network)

            with sqlite3.session_scope() as session:
                for table in tables:
                    results = session.query(table).filter(table.network.startswith(network_wildcard))  # noqa
                    if results.all():
                        json.dump([x.to_dict() for x in results.all()], fp=fd, ensure_ascii=False, separators=(',', ': '))  # noqa


@task
def prep_packaging(c, dir=PROJECT_ROOT_DIR, echo=False):
    """Preps the current state of this project for use with packaging as a tarball

    """
    clean(c, dir=PROJECT_ROOT_DIR, echo=echo)
    dest_dir = os.path.join(PROJECT_ROOT_DIR, 'tmp')
    args = [
        'rsync',
        '-am',
        '--exclude "__pycache__"',
        '--exclude "*.egg*"',
        '--exclude "*.out"',
        '--exclude "*.pyc"',
        '--exclude "*.vim*"',
        '--exclude "*.tar.gz"',
        '--exclude "*.zip"',
        '--exclude ".*.lcts"',
        '--exclude ".coverage"',
        '--exclude ".git"',
        '--exclude ".pytest_cache"',
        '--exclude ".tox"',
        '--exclude ".vagrant"',
        '--exclude "build"',
        '--exclude "diagrams"',
        '--exclude "dist"',
        '--exclude "reports"',
        '--exclude "vagrant"',
        PROJECT_ROOT_DIR,
        dest_dir,
    ]
    cmd = ' '.join(args)

    tar_cmd = 'tar czf {}.tar.gz -C {} .'.format(
        PROJECT_NAME,
        dest_dir
    )

    with c.cd(PROJECT_ROOT_DIR):
        if os.path.isdir(dest_dir):
            rmtree(dest_dir)
        c.run('rm -f {}.tar.gz'.format(PROJECT_NAME), echo=echo)
        c.run(cmd, echo=echo)
        c.run(tar_cmd, echo=echo)


@task
def coverage(c, echo=True, extra=None, pty=True, hide=False):
    """Run code coverage

    """
    if os.path.isfile('.coverage'):
        os.unlink('.coverage')

    default_args = [
        'coverage',
        'run',
        '-m',
        'pytest',
        '-v',
        '-rs',
        '-s',
    ]

    cmd = ' '.join(default_args)
    if extra:
        cmd += ' {}'.format(extra)
    with c.cd(PROJECT_ROOT_DIR):
        c.run(cmd, echo=echo, pty=pty, hide=hide, warn=True)
        c.run('coverage report -m', pty=pty, hide=hide)


# @task
# def deploy_aws(c, echo=True, extra=None, pty=True):
#     extra_args = ''
#     if extra:
#         extra_args += ' {}'.format(extra)
#
#     args = (
#         'ansible-playbook',
#         '-vv',
#         'deploy.yml',
#         extra_args,
#     )
#
#     ansible_dir = os.path.join(
#         PROJECT_ROOT_DIR,
#         'ansible'
#     )
#
#     cmd = ' '.join(args)
#     syntax_cmd = cmd + ' --syntax-check'
#
#     prep_packaging(c, echo=echo)
#
#     with c.cd(ansible_dir):
#         c.run(syntax_cmd, echo=echo, pty=pty)
#         c.run(cmd, echo=echo, pty=pty)


@task
def docs_html(c, echo=False, extra=None, pty=True, hide=False):
    """Builds the sphinx documentation

    """
    default_args = [
        'make',
        'html',
    ]
    cmd = ' '.join(default_args)
    if extra:
        cmd += ' {}'.format(extra)

    docs_dir = os.path.join(
        PROJECT_ROOT_DIR, 'docs'
    )

    with c.cd(docs_dir):
        c.run('make clean')
        c.run(cmd, pty=pty, hide=hide, echo=echo)

    with c.cd(PROJECT_ROOT_DIR):
        c.run('git add docs/', warn=True)


@task
def prep_commit(c, echo=False,  pty=True, hide=False):
    """Preps the commit, runs [bandit, docs-html, coverage]

    """
    with c.cd(PROJECT_ROOT_DIR):
        bandit(c, echo=echo, pty=pty)
        c.run(
            'git add reports/'
            ' && git commit -m "auto: Updates bandit report"',
            warn=True,
        )

        docs_html(c, echo=echo, pty=pty, hide=hide)
        c.run(
            'git add docs/'
            ' && git commit -m "auto: Updates sphinx docs"',
            warn=True,
        )

        coverage(c, echo=echo, extra=None, pty=pty, hide=hide)


@task
def tests(c, extra=None, pty=True, hide=False):
    """Runs all or specific tests

    """
    default_args = [
        'pytest',
        '-vvs',
        '-rs',
        'tests',
    ]
    cmd = ' '.join(default_args)
    if extra:
        cmd += ' {}'.format(extra)

    with c.cd(PROJECT_ROOT_DIR):
        c.run(cmd, pty=pty, hide=hide)


@task
def download_geolite_city_db(c, cleanup=True):
    """Downloads the geolite2 city db

    """
    with c.cd(PROJECT_ROOT_DIR):
        filename = 'GeoLite2-City-CSV.zip'
        md5_filename = '{filename}.md5'.format(filename=filename)

        city_csv_url = urlparse.urljoin(GEOLITE_BASE_URI, filename)
        city_csv_url_md5 = urlparse.urljoin(GEOLITE_BASE_URI, md5_filename)

        get_request(city_csv_url, save_as=filename, stream=True)
        get_request(city_csv_url_md5, save_as=md5_filename, stream=True)

        validate_md5_checksum(filename, md5_filename)

        unzip_file(filename, os.path.join('data', 'geolite2'))

        rename_directory(
            os.path.join('data', 'geolite2', 'GeoLite2-City-CSV_*'),
            os.path.join('data', 'geolite2', 'city')
        )

        whitelist = CONFIG['geolite_data']['city']['whitelist']
        remove_file(
            os.path.join('data', 'geolite2', 'city', '*.csv'),
            whitelist=whitelist,
        )

        if cleanup:
            remove_file(filename)


@task
def download_geolite_asn_db(c, cleanup=True):
    """Downloads the geolite2 asn db

    """
    with c.cd(PROJECT_ROOT_DIR):
        filename = 'GeoLite2-ASN-CSV.zip'
        md5_filename = '{filename}.md5'.format(filename=filename)

        asn_csv_url = urlparse.urljoin(GEOLITE_BASE_URI, filename)
        asn_csv_url_md5 = urlparse.urljoin(GEOLITE_BASE_URI, md5_filename)

        get_request(asn_csv_url, save_as=filename, stream=True)
        get_request(asn_csv_url_md5, save_as=md5_filename, stream=True)

        validate_md5_checksum(filename, md5_filename)

        unzip_file(filename, os.path.join('data', 'geolite2'))

        rename_directory(
            os.path.join('data', 'geolite2', 'GeoLite2-ASN-CSV_*'),
            os.path.join('data', 'geolite2', 'asn')
        )

        whitelist = CONFIG['geolite_data']['asn']['whitelist']
        remove_file(
            os.path.join('data', 'geolite2', 'asn', '*.csv'),
            whitelist=whitelist,
        )

        if cleanup:
            remove_file(filename)


@task
def download_geolite_country_db(c, cleanup=True):
    """Downloads the geolite2 country db

    """
    with c.cd(PROJECT_ROOT_DIR):
        filename = 'GeoLite2-Country-CSV.zip'
        md5_filename = '{filename}.md5'.format(filename=filename)

        country_csv_url = urlparse.urljoin(GEOLITE_BASE_URI, filename)
        country_csv_url_md5 = urlparse.urljoin(GEOLITE_BASE_URI, md5_filename)

        get_request(country_csv_url, save_as=filename, stream=True)
        get_request(country_csv_url_md5, save_as=md5_filename, stream=True)

        validate_md5_checksum(filename, md5_filename)

        unzip_file(filename, os.path.join('data', 'geolite2'))

        rename_directory(
            os.path.join('data', 'geolite2', 'GeoLite2-Country-CSV_*'),
            os.path.join('data', 'geolite2', 'country')
        )

        whitelist = CONFIG['geolite_data']['country']['whitelist']
        remove_file(
            os.path.join('data', 'geolite2', 'country', '*.csv'),
            whitelist=whitelist,
        )

        if cleanup:
            # remove the zip file
            remove_file(filename)


@task
def download_geolite_dbs(c, cleanup=True):
    """Metajob to run all other download_geolite_*_db tasks

    """
    download_geolite_asn_db(c, cleanup=cleanup)
    download_geolite_city_db(c, cleanup=cleanup)
    download_geolite_country_db(c, cleanup=cleanup)


@task
def populate_sqlite3(c):
    """Populate SQLite3 db with geolite2 CSV data

    """
    with c.cd(PROJECT_ROOT_DIR):

        def geolite2_city_blocks_ipv4():
            return models.GeoLite2CityBlocksIpv4

        def geolite2_asn_blocks_ipv4():
            return models.GeoLite2AsnBlocksIpv4

        # create a mapping of CSV files to models but to avoid the import
        # problem we just put this behind a small wrapper function.
        model_mapping = {
            'GeoLite2-City-Blocks-IPv4.csv': geolite2_city_blocks_ipv4,
            'GeoLite2-ASN-Blocks-IPv4.csv': geolite2_asn_blocks_ipv4,
        }

        csv_files = [
            os.path.join(
                'data', 'geolite2', 'city', 'GeoLite2-City-Blocks-IPv4.csv',
            ),
            os.path.join(
                'data', 'geolite2', 'asn', 'GeoLite2-ASN-Blocks-IPv4.csv',
            )
        ]

        for csv_file in csv_files:
            reader = csv.reader(open(csv_file))
            headers = next(reader)
            ModelClass = model_mapping[os.path.basename(csv_file)]()

            with sqlite3.session_scope() as session:
                for i, line in enumerate(reader):
                    model = ModelClass()

                    for key, value in zip(headers, line):
                        setattr(model, key, value)

                    log.debug('adding model={}'.format(model.__dict__))
                    session.add(model)

                    if i % 10000 == 0:
                        # commit every 10000 records to avoid OOM
                        session.commit()

CONFIG = read_json(
    os.path.join(PROJECT_ROOT_DIR, 'config.json'),
)
