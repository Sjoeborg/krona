from collections.abc import Iterator

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
    name = "nordnet"

    def is_valid_file(self, file_path: str) -> bool:
        try:
            df = pl.read_csv(file_path, separator="\t", encoding="utf-16")
            return set(NORDNET_FIELDNAMES).issubset(set(df.columns))
        except UnicodeDecodeError:
            return False

    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        if not self.is_valid_file(file_path):
            return

        df = pl.read_csv(file_path, separator="\t", encoding="utf-16", decimal_comma=True, try_parse_dates=True).sort(
            by="Affärsdag"
        )
        for row in df.iter_rows(named=True):
            try:
                yield Transaction(
                    date=row["Affärsdag"],
                    symbol=str(row["Värdepapper"]),
                    transaction_type=TransactionType.from_term(str(row["Transaktionstyp"])),
                    currency=str(row["Valuta"]),
                    ISIN=str(row["ISIN"]),
                    quantity=abs(int(row["Antal"])),
                    price=float(row["Kurs"] or 0.0),
                    fees=float(row["Courtage"] or 0.0),
                )
            except ValueError:
                # TransactionType not found
                # logger.warning("Possible error in transaction, skipping:\n %s", row)
                continue


if __name__ == "__main__":
    parser = NordnetParser()
    print(parser.is_valid_file("nordnet.csv"))
    for transaction in parser.parse_file("nordnet.csv"):
        print(transaction)
