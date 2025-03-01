from collections.abc import Iterator
from datetime import datetime

import polars as pl

from krona.models.transaction import Transaction, TransactionType
from krona.parsers.base import BaseParser

NORDNET_FIELDNAMES = [
    "Id",
    "Bokföringsdag",
    "Affärsdag",
    "Likviddag",
    "Depå",
    "Transaktionstyp",
    "Värdepapper",
    "ISIN",
    "Antal",
    "Kurs",
    "Ränta",
    "Total Avgift",
    "Valuta",
    "Belopp",
    "Valuta",
    "Inköpsvärde",
    "Valuta",
    "Resultat",
    "Valuta",
    "Totalt antal",
    "Saldo",
    "Växlingskurs",
    "Transaktionstext",
    "Makuleringsdatum",
    "Notanummer",
    "Verifikationsnummer",
    "Courtage",
    "Valuta",
    "Referensvalutakurs",
    "Initial låneränta",
]


class NordnetParser(BaseParser):
    def validate_format(self, file_path: str) -> bool:
        df = pl.read_csv(file_path, separator="\t", encoding="utf-16")
        return set(NORDNET_FIELDNAMES).issubset(set(df.columns))

    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        df = pl.read_csv(file_path, separator="\t", encoding="utf-16", decimal_comma=True).sort(by="Affärsdag")
        for row in df.iter_rows(named=True):
            yield Transaction(
                date=datetime.strptime(row["Affärsdag"], "%Y-%m-%d"),
                symbol=str(row["Värdepapper"]),
                transaction_type=TransactionType.from_term(str(row["Transaktionstyp"])),
                currency=str(row["Valuta"]),
                ISIN=str(row["ISIN"]),
                quantity=abs(int(row["Antal"])),
                price=float(row["Kurs"] or 0.0),
                fees=float(row["Courtage"] or 0.0),
            )
