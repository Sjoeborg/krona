from krona.parsers.avanza import AvanzaParser


def test_avanza_parser():
    filename = "tests/data/transaktioner_2016-11-17_2024-12-15.csv"
    parser = AvanzaParser()
    assert parser.validate_format(filename)
    for transaction in parser.parse_file(filename):
        print(transaction)
