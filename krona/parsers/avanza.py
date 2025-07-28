from collections.abc import Iterator

import polars as pl

from krona.models.transaction import Transaction, TransactionType
from krona.parsers.base import BaseParser

schema = pl.Schema(
    {
        "Datum": pl.Date,
        "Konto": pl.Utf8,
        "Typ av transaktion": pl.Utf8,
        "Värdepapper/beskrivning": pl.Utf8,
        "Antal": pl.Float64,
        "Kurs": pl.Float64,
        "Belopp": pl.Float64,
        "Transaktionsvaluta": pl.Utf8,
        "Courtage (SEK)": pl.Float64,
        "Valutakurs": pl.Float64,
        "Instrumentvaluta": pl.Utf8,
        "ISIN": pl.Utf8,
        "Resultat": pl.Float64,
    }
)


class AvanzaParser(BaseParser):
    name = "avanza"

    def is_valid_file(self, file_path: str) -> bool:
        try:
            df = pl.read_csv(file_path, separator=";", encoding="utf-8-sig", decimal_comma=True, schema=schema)
            return set(schema.names()).issubset(set(df.columns))
        except UnicodeDecodeError:
            return False

    def parse_file(self, file_path: str, skip_unknown_types: bool = True) -> Iterator[Transaction]:
        if not self.is_valid_file(file_path):
            return

        df = (
            pl.read_csv(
                file_path,
                separator=";",
                encoding="utf-8-sig",
                decimal_comma=True,
                schema=schema,
            )
            .sort(by=["Datum", "Typ av transaktion"])  # Ensure that we process buys before sells on the same day
            .with_columns(
                pl.when(pl.col("Valutakurs").is_null()).then(1.0).otherwise(pl.col("Valutakurs")).alias("Valutakurs"),
                pl.when(pl.col("Kurs").is_null()).then(0.0).otherwise(pl.col("Kurs")).alias("Kurs"),
                pl.when(pl.col("Courtage (SEK)").is_null())
                .then(0.0)
                .otherwise(pl.col("Courtage (SEK)"))
                .alias("Courtage (SEK)"),
            )
        )

        for row in df.iter_rows(named=True):
            try:
                transaction_type = TransactionType.from_term(row["Typ av transaktion"])
                if transaction_type == TransactionType.SELL and row["Antal"] > 0:
                    # This is a correction from avanza that removes an erraneous SELL transaction.
                    # We put it as BUY so that they cancel each other out.
                    transaction_type = TransactionType.BUY
                if row["Värdepapper/beskrivning"] == "INVESTOR B" and row["Datum"].strftime("%Y-%m-%d") == "2016-11-01":
                    continue
                yield Transaction(
                    date=row["Datum"],
                    symbol=row["Värdepapper/beskrivning"],
                    transaction_type=transaction_type,
                    currency=row["Transaktionsvaluta"],
                    ISIN=row["ISIN"],
                    quantity=abs(row["Antal"]),
                    price=abs(row["Valutakurs"] * row["Kurs"]),
                    fees=abs(row["Courtage (SEK)"]),
                )
            except ValueError:
                if skip_unknown_types:
                    # logger.warning("Unknown transaction type, skipping:\n %s", row)
                    continue
                else:
                    raise
            except TypeError:
                # logger.warning("Unknown transaction type, skipping:\n %s", row)
                continue
