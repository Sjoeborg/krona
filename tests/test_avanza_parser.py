from krona.parsers.avanza import AvanzaParser


def test_avanza_parser(avanza_file: str, avanza_parser: AvanzaParser):
    assert avanza_parser.validate_format(avanza_file)
    for transaction in avanza_parser.parse_file(avanza_file):
        print(transaction)
