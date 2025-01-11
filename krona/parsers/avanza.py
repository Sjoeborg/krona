from collections.abc import Iterator
from datetime import datetime
from typing import TypedDict

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

AVANZA_COLUMNS = {
    "Typ av transaktion": "Typ_av_transaktion",
    "Värdepapper/beskrivning": "Vardepapper_beskrivning",
    "Courtage (SEK)": "Courtage_SEK",
}


class AvanzaRow(TypedDict):
    Datum: datetime
    Konto: str
    Typ_av_transaktion: str
    Vardepapper_beskrivning: str
    Antal: int
    Kurs: float
    Belopp: float
    Transaktionsvaluta: str
    Courtage_SEK: float
    Valutakurs: float
    Instrumentvaluta: str
    ISIN: str
    Resultat: float


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
            new_columns=[AVANZA_COLUMNS.get(col, col) for col in schema.names()],
        ).sort(by="Datum")

        for row in df.iter_rows(named=True):
            row_typed: AvanzaRow = row
            yield Transaction(
                date=row_typed.get("Datum"),
                symbol=row_typed.get("Vardepapper_beskrivning"),
                transaction_type=TransactionType.from_term(row_typed.get("Typ_av_transaktion")),
                currency=row_typed.get("Transaktionsvaluta"),
                ISIN=row_typed.get("ISIN"),
                quantity=abs(int(row_typed.get("Antal"))),
                price=abs(row_typed.get("Kurs")),
                fees=abs(row_typed.get("Courtage_SEK")),
            )
