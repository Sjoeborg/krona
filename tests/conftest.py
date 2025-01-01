import pytest

from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser


@pytest.fixture
def nordnet_file():
    return "tests/data/transactions-and-notes-export.csv"


@pytest.fixture
def nordnet_parser():
    return NordnetParser()


@pytest.fixture
def avanza_file():
    return "tests/data/transaktioner_2016-11-17_2024-12-15.csv"


@pytest.fixture
def avanza_parser():
    return AvanzaParser()
