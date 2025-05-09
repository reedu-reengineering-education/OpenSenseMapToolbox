import os
import requests
import pandas as pd
import geopandas
import numpy
import json
from io import StringIO
from urllib.parse import urljoin
import logging
import time
import datetime as dt
logger = logging.getLogger('osm')


class APIressources:
    def __init__(self, endpoints: dict):
        self.endpoints = endpoints
        self.endpoint_base = 'https://api.opensensemap.org'
        self.status = {}
        self.t_from = '1970-01-01T00:00:00Z'
        self.t_to = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
        self.data = None


    def get_data(self, endpoint: str, params: dict = None, format: str = 'json', retries = 3):
        for attempt in range(retries):
            try:
                print(f'getting: {endpoint}')
                res = requests.get(endpoint, params=params, timeout=30)
                res.raise_for_status()
                if format == 'json':
                    return json.loads(res.text)
                if format == 'csv':
                    return pd.read_csv(StringIO(res.text))
            except requests.RequestException as e:
                if attempt == retries - 1:
                    print(retries - 1)
                    logger.critical(f"an error occurred: '{e}' at source {endpoint}")
                    self.status = {'code': 'error'}
                    raise Warning(f"an error occurred: '{e}' at source {endpoint}")
                time.sleep(5)


    def endpoint_merge(self, endpoint):
        if endpoint not in self.endpoints.keys():
            raise KeyError(f"'{endpoint}' not found in endpoints must be one of {self.endpoints.keys()}")
        return urljoin(self.endpoint_base, self.endpoints[endpoint]['endpoint'])


    def save_json(self, data, path):
        base_path = os.path.dirname(path)
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
        with open(path, 'w') as json_file:
            json.dump(data, json_file)


    def read_json(self, path):
        with open(path, 'r') as json_file:
            return json.load(json_file)


    def save_csv(self, data, path):
        if isinstance(data, pd.DataFrame):
            data.to_csv(path, index=False)
        else:
            raise TypeError('data needs to be pandas dataframe')


    def read_csv(self, path):
        return pd.read_csv(path, index_col=False)

