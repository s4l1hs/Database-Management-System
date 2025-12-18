import os
from dataclasses import dataclass
from typing import List, Optional
import mysql.connector


def _get_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "db_pass"),
        database=os.getenv("DB_NAME", "wdi_project"),
        port=int(os.getenv("DB_PORT", "3306")),
    )


@dataclass
class Country:
    country_id: int
    country_name: str
    country_code: str
    region: Optional[str] = None

    @staticmethod
    def fetch_all() -> List['Country']:
        conn = _get_conn()
        try:
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute("SELECT country_id, country_name, country_code, region FROM countries")
                rows = cur.fetchall()
            finally:
                cur.close()
            return [Country(**r) for r in rows]
        finally:
            conn.close()


@dataclass
class FreshwaterData:
    data_id: int
    country_id: int
    freshwater_indicator_id: int
    year: int
    indicator_value: Optional[float]
    source_notes: Optional[str]


@dataclass
class HealthSystemRow:
    row_id: int
    country_id: int
    health_indicator_id: int
    indicator_value: Optional[float]
    year: int
    source_notes: Optional[str]

    def to_dict(self):
        return {
            "row_id": self.row_id,
            "country_id": self.country_id,
            "health_indicator_id": self.health_indicator_id,
            "indicator_value": float(self.indicator_value) if self.indicator_value is not None else None,
            "year": self.year,
            "source_notes": self.source_notes,
        }


@dataclass
class GreenhouseGasRow:
    row_id: int
    country_id: int
    ghg_indicator_id: int
    indicator_value: int
    share_of_total_pct: Optional[int]
    uncertainty_pct: Optional[int]
    year: int
    source_notes: Optional[str]

    def to_dict(self):
        return {
            "row_id": self.row_id,
            "country_id": self.country_id,
            "ghg_indicator_id": self.ghg_indicator_id,
            "indicator_value": self.indicator_value,
            "share_of_total_pct": self.share_of_total_pct,
            "uncertainty_pct": self.uncertainty_pct,
            "year": self.year,
            "source_notes": self.source_notes,
        }


@dataclass
class EnergyDataRow:
    data_id: int
    country_id: int
    energy_indicator_id: int
    year: int
    indicator_value: Optional[float]
    data_source: Optional[str]


@dataclass
class SustainabilityDataRow:
    data_id: int
    country_id: int
    sus_indicator_id: int
    year: int
    indicator_value: Optional[float]
    source_note: Optional[str]


# Note: This file now provides simple dataclasses and a minimal `fetch_all` example for Country.
# For other operations (inserts/updates/deletes or more queries), use `_get_conn()` and execute
# parameterized SQL with cursors, then map results into the dataclasses above.
