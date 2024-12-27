import csv
from collections.abc import Iterator
from datetime import datetime

from krona.models.transaction import Transaction, TransactionType
from krona.parsers.base import BaseParser

AVANZA_FIELDNAMES = [
    "Datum",
    "Konto",
    "Typ av transaktion",
    "Värdepapper/beskrivning",
    "Antal",
    "Kurs",
    "Belopp",
    "Transaktionsvaluta",
    "Courtage (SEK)",
    "Valutakurs",
    "Instrumentvaluta",
    "ISIN",
    "Resultat",
]


class AvanzaParser(BaseParser):
    def validate_format(self, file_path: str) -> bool:
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            return set(AVANZA_FIELDNAMES).issubset(set(reader.fieldnames or []))

    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                yield Transaction(
                    date=datetime.strptime(row["Datum"], "%Y-%m-%d"),
                    symbol=row["Värdepapper/beskrivning"],
                    transaction_type=TransactionType(row["Typ av transaktion"].lower()),
                    currency=row["Transaktionsvaluta"],
                    ISIN=row["ISIN"],
                    quantity=self.to_float(row["Antal"]),
                    amount=self.to_float(row["Kurs"]),
                    fees=self.to_float(row.get("Courtage (SEK)", "0")),
                )
