from collections.abc import Iterator

import polars as pl

from krona.models.transaction import Transaction, TransactionType
from krona.parsers.base import BaseParser

schema = pl.Schema({
    "Datum": pl.Date,
    "Konto": pl.Utf8,
    "Typ av transaktion": pl.Utf8,
    "Värdepapper/beskrivning": pl.Utf8,
    "Antal": pl.Int64,
    "Kurs": pl.Float64,
    "Belopp": pl.Float64,
    "Transaktionsvaluta": pl.Utf8,
    "Courtage (SEK)": pl.Float64,
    "Valutakurs": pl.Float64,
    "Instrumentvaluta": pl.Utf8,
    "ISIN": pl.Utf8,
    "Resultat": pl.Float64,
})


class AvanzaParser(BaseParser):
    def validate_format(self, file_path: str) -> bool:
        df = pl.read_csv(file_path, separator=";", encoding="utf-8-sig")
        return set(schema.names()).issubset(set(df.columns))

    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        df = pl.read_csv(
            file_path,
            separator=";",
            encoding="utf-8-sig",
            decimal_comma=True,
            schema=schema,
        ).sort(by="Datum")

        for row in df.iter_rows(named=True):
            yield Transaction(
                date=row["Datum"],
                symbol=row["Värdepapper/beskrivning"],
                transaction_type=TransactionType.from_term(row["Typ av transaktion"]),
                currency=row["Transaktionsvaluta"],
                ISIN=row["ISIN"],
                quantity=abs(int(row["Antal"])),
                price=abs(row["Kurs"] or 0.0),
                fees=abs(row["Courtage (SEK)"] or 0.0),
            )
