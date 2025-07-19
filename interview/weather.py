import datetime as dt
import csv
from dataclasses import dataclass
from typing import Dict, List, Iterable, TypedDict
import itertools
from collections import defaultdict

WeatherCSVRow = TypedDict('WeatherCSVRow', {
    'Station Name': str,
    'Measurement Timestamp': str,
    'Air Temperature': float
})

@dataclass(frozen=True, slots=True)
class StationMeasurement:
    station_name: str
    timestamp: dt.datetime
    air_temperature: float

    @classmethod
    def from_csv_row(cls, csv_row: WeatherCSVRow):
        station_name = csv_row.get("Station Name", "UNKNOWN")
        timestamp_str = csv_row.get("Measurement Timestamp", None)
        if timestamp_str is None:
            raise ValueError("Invalid Timestamp passed")
        timestamp = dt.datetime.strptime(timestamp_str, "%m/%d/%Y %I:%M:%S %p")
        temperature = csv_row.get("Air Temperature", None)
        if temperature is None:
            raise ValueError("Invalid temparture passed")
        air_temperature = float(temperature)
        return cls(station_name, timestamp, air_temperature)

@dataclass(frozen=True, slots=True)
class StationStatistic:
    station_name: str
    date: dt.date
    start: float
    end: float
    low: float
    high: float

    def to_csv_row(self) -> str:
        return f"{self.station_name},{self.date},{self.low},{self.high},{self.start},{self.end}\n"

def group_daily_measures(measurements: Iterable[StationMeasurement]) -> Dict[str, List[StationMeasurement]]:
    groups = defaultdict(list)
    for measurement in measurements:
        groups[measurement.station_name].append(measurement)
    return groups

def compute_daily_stat(name: str, date: dt.date, measurements: List[StationMeasurement]) -> StationStatistic:
    """
    Can improve this function, maybe put it in factory class
    """
    start = min(measurements, key=lambda x : x.timestamp).air_temperature
    end = max(measurements, key=lambda x : x.timestamp).air_temperature
    low = min(m.air_temperature for m in measurements)
    high = max(m.air_temperature for m in measurements)
    stat = StationStatistic(name, date, start, end, low, high)
    return stat


def process_csv(reader, writer):
    writer.write("Station Name,Date,Min Temp,Max Temp,First Temp,Last Temp" + "\n")
    # TODO: check tracer malloc allocations
    rows = csv.DictReader(reader)
    measurements = (StationMeasurement.from_csv_row(row) for row in rows)
    #! Group by is also lazy since it only groups by adjacent rows
    for date, group in itertools.groupby(measurements, lambda m: m.timestamp.date()):
        measures_by_name = group_daily_measures(group)
        for name, measurements in measures_by_name.items():
            stat = compute_daily_stat(name, date, measurements)
            writer.write(stat.to_csv_row())
