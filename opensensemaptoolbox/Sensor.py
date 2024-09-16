import os
import requests
import pandas as pd
import geopandas
import numpy
import json
from io import StringIO
from urllib.parse import urljoin
import datetime as dt

from .APIressources import APIressources


class Sensor(APIressources):
    def __init__(self, boxId: str, sensorId: str):
        self.boxId = boxId
        self.sensorId = sensorId
        super().__init__(endpoints={'get_data': {
                                        'endpoint': f'/boxes/{self.boxId}/data/{self.sensorId}',
                                        'ref': 'https://docs.opensensemap.org/#api-Measurements-getData'},
                                    'sensor': {
                                        'endpoint': f'/boxes/{self.boxId}/sensors/{self.sensorId}',
                                        'ref': 'https://docs.opensensemap.org/#api-Measurements-getLatestMeasurementOfSensor'}
                                   },
        )
        self.metadata = self.get_sensor_metadata()
        self.data = self.get_sensor_data()


    def get_sensor_metadata(self):
        data = self.get_data(self.endpoint_merge('sensor'))
        return data
    def get_sensor_data(self, params = None):
        if params:
            data = self.get_data(self.endpoint_merge('get_data'), params=params, format='csv')
        else:
            data = self.get_data(self.endpoint_merge('get_data'), params={'from-date': '1970-01-01T00:00:00Z',
                                                                          'to-date': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
                                                                          'format': 'csv'}, format='csv')
        data = data.rename(columns={'value': self.metadata['title']})
        #data['createdAt'] = pd.to_datetime(data['createdAt'])
        return data
