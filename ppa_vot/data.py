import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests


class DataScraper:
    def __init__(self, dataset_name, limit=None, start_time=None, end_time=None, sort_order="ASC"):
        self.path_data = Path("data")
        self.path_data.mkdir(exist_ok=True)
        self.dataset_name = dataset_name
        self.limit = limit
        self.start_time = start_time
        self.end_time = end_time
        self.sort_order = sort_order

    def api_call(self):
        params = {}
        if self.limit is not None:
            params["limit"] = self.limit
        if self.start_time:
            params["start"] = self.start_time
        if self.end_time:
            params["end"] = self.end_time
        params["sort"] = f"Minutes1UTC {self.sort_order}"

        start = time.perf_counter()
        response = requests.get(
            f"https://api.energidataservice.dk/dataset/{self.dataset_name}", params=params
        )
        elapsed = time.perf_counter() - start
        print(f"API call took {elapsed:.2f}s")
        response.raise_for_status()
        return response.json()["records"]

    def data_export(self, export_format="csv"):
        data_json = self.api_call()

        start = time.perf_counter()
        df = pd.DataFrame(data_json)
        df["Minutes1UTC"] = pd.to_datetime(df["Minutes1UTC"])
        df = df.set_index("Minutes1UTC")
        print(df)

        if export_format == "csv":
            df.to_csv(self.path_data / f"{self.dataset_name}.csv")
        elif export_format == "parquet":
            table = pa.Table.from_pandas(df)
            pq.write_table(table, self.path_data / f"{self.dataset_name}.parquet")
        elapsed = time.perf_counter() - start
        print(f"Export ({export_format}) took {elapsed:.2f}s")


# Usage:
scraper = DataScraper(
    dataset_name="PowerSystemRightNow",
    start_time="2020-01-01T00:00",
    end_time="2025-01-01T00:00",
    sort_order="ASC",
)
scraper.data_export(export_format="parquet")
scraper.data_export(export_format="csv")
