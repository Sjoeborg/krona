from collections.abc import Iterator
from datetime import datetime

import polars as pl

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
        df = pl.read_csv(file_path, separator=";", encoding="utf-8-sig")
        return set(AVANZA_FIELDNAMES).issubset(set(df.columns))

    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        df = pl.read_csv(file_path, separator=";", encoding="utf-8-sig", decimal_comma=True).sort(by="Datum")
        for row in df.iter_rows(named=True):
            yield Transaction(
                date=datetime.strptime(row["Datum"], "%Y-%m-%d"),
                symbol=row["Värdepapper/beskrivning"],
                transaction_type=TransactionType.from_term(row["Typ av transaktion"]),
                currency=row["Transaktionsvaluta"],
                ISIN=row["ISIN"],
                quantity=abs(int(row["Antal"])),
                price=abs(row["Kurs"]),
                fees=abs(row["Courtage (SEK)"]),
            )
