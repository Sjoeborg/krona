from krona.parsers.avanza import AvanzaParser


def test_avanza_parser(avanza_file: str, avanza_parser: AvanzaParser):
    for _ in avanza_parser.parse_file(avanza_file):
        pass
