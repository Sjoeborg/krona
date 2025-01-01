from krona.parsers.nordnet import NordnetParser


def test_nordnet_parser(nordnet_file: str, nordnet_parser: NordnetParser):
    assert nordnet_parser.validate_format(nordnet_file)
    for _ in nordnet_parser.parse_file(nordnet_file):
        pass
