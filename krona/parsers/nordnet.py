import csv
from collections.abc import Iterator
from datetime import datetime

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
        with open(file_path, encoding="utf-16") as f:
            reader = csv.DictReader(f, delimiter="\t")
            return set(NORDNET_FIELDNAMES).issubset(set(reader.fieldnames or []))

    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        # TODO: use polars instead of csv
        with open(file_path, encoding="utf-16") as f:
            lines = f.readlines()
            header = lines.pop(0)
            data_lines = lines[1:]  # Extract the data lines

            reader = csv.DictReader([header, *list(reversed(data_lines))], delimiter="\t")
            for row in reader:
                yield Transaction(
                    date=datetime.strptime(row["Affärsdag"], "%Y-%m-%d"),
                    symbol=row["Värdepapper"],
                    transaction_type=TransactionType.from_term(row["Transaktionstyp"]),
                    currency=row["Valuta"],
                    ISIN=row["ISIN"],
                    quantity=abs(int(row["Antal"])),
                    price=abs(self.to_float(row["Kurs"])),
                    fees=abs(self.to_float(row["Courtage"])),
                )
