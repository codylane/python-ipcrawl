ipcrawl
---------------

[![Build Status](https://travis-ci.org/codylane/python-ipcrawl.svg?branch=master)](https://travis-ci.org/codylane/python-ipcrawl)

Searches for ip addresses inside unformatted text

# Overview

* The goal of the project is to take some unstructured text that
  contains Ipv4 addresses, lex that into a datastructure for later use,
  then filter down this list and perform geoip queries against the Ip
  addresses obtained.

* This project is meant to be a fun and challenging example. It
  currently doesn't support the end goal yet.  It's close, the filtering
  isn't completed, everything else seems to be in a good working state.
  See all the open issues for the missing features.

# What is currently implemented?

* The CSV geolite2 data download and data population are externalized from the
  libary to decouple data bootstraping. This was done by design so that the
  library is nice and small and flexible.

* The lexing routing for finding IP addresses uses a real lexer very
  similar to ``flex`` or ``lex``.  This is 100% tested and works great.

* The data population routine is handled by [python
  invoke](http://www.pyinvoke.org/) which is a ``Makefile`` like library
  for python tasks and execution.  To bootstrap the project, you'll use
  ``invoke <cmd>`` and to populate the Sqlite3 db.

* An attempt was made to use an ``ORM`` using the
  [SQLAlchemy](https://docs.sqlalchemy.org/en/13/) to transform the CSV
  geolite data into a small DB that has no external deps.  The dataset
  size to populate the DB is a little more than 4 million records so it
  takes a significant amoutn of time to populate the DB.
  **WARNING:** You may experience ``OOM`` exceptions if your dataset is too large.
  The DB and models have some test coverage to ensure everything works.

* There is automatted and generated API documenation using Sphinx.

* This runs on `python 3.6` and `python 3.7`

# Quickstart

* Ensure that you have cloned the repository
* Checkout the code repository and initialize your python dev environment

```
cd ipcrawl
./init.sh
```

* Once the project has been initialized we just need to source it

```
. ./init.sh
```

* **NOTE:** You only have to do this once and all further commands
  assume that you have executed this step.

* We first want to download the Geolite2 free CSV files.
  * **NOTE:** You can customize what files are present by modifying [config.json](config.json)
              Do this before you invoke the following command.
  * **NOTE:** This step isn't necessary unless you want to download a
    fresh version, [init.sh](init.sh) will do this for you if the CSV
    files don't already exist.

```
inv download-geolite-dbs
```

* After the CSV files have been downloaded, we will attempt to populate
  the database.
* **NOTE:** This may take a long time depending on your machine. This a
  synchronous operation and not threaded due to time constraints. There
  is a little over 4 million records to populate into your database.
  Benchmarks have shown on `4.2 GHz Intel Core i7` with `64g RAM` and
  `SSD` this took on average `8-12` minutes. We only need to do this
  when there is new data to populate and this depends on the geolite2
  release cycle for CSVs.  Consult their documentaiton for further
  detials.
  * **NOTE:** This step isn't necessay when the sqlite3 db does not
    exist.

```
inv populate-sqlite3
```

# Usage

## invoke tasks used to interact with the project

```
$ inv -l
Available tasks:

  bandit                        Runs bandit security linter
  benchmark-raw-csv             Perform timeit calculations on reading CSVs as raw file or into a dict
  build-sdist                   Builds the package
  clean                         Cleans all compiled artifacts recursively
  coverage                      Run code coverage
  docs-html                     Builds the sphinx documentation
  download-geolite-asn-db       Downloads the geolite2 asn db
  download-geolite-city-db      Downloads the geolite2 city db
  download-geolite-country-db   Downloads the geolite2 country db
  download-geolite-dbs          Metajob to run all other download_geolite_*_db tasks
  populate-sqlite3              Populate SQLite3 db with geolite2 CSV data
  prep-commit                   Preps the commit, runs [bandit, docs-html, coverage]
  prep-packaging                Preps the current state of this project for use with packaging as a tarball
  tests                         Runs all or specific tests
```

## build the API documentation

```
inv docs-html
```

* Then open your browser using the `file:///path/to/this/repo/docs/build/html/index.html`


## Download the geolite geoip free datasets

* The following will download the geolite data CSV files

#### Download just the ASN data

```
inv download-geolite-asn-db
```

#### Download just the city data

```
inv download-geolite-city-db
```

#### Download just the country data

```
inv download-geolite-country-db
```

#### Download all the geoite data

```
inv download-geolite-dbs
```

#### Populate the sqlite database with the CSV data

```
inv populate-sqlite3
```

## Testing

* This project is currently tested only on the newest versions of python
  which at this time of writing is only `python 3.6` and `python 3.7`
* This runs all the tests

```
tox
```

* tox environments `tox -l`

```
py36
py37
bandit
coverage
docs-html
flake8
```

* Example of running only flake8

```
tox -e flake8
```

# Author

* Cody Lane 2019
