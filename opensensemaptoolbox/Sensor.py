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
        self.metadata = None
        self.data = None
        self.status = {}


    def get_sensor_metadata(self):
        data = None

        try:
            data = self.get_data(self.endpoint_merge('sensor'))
        except Warning as w:
            print(f"Warning encountered: {w} !")
            self.status = {self.sensorId: "Error"}
        self.metadata = data
        return data


    def get_sensor_data(self, **kwargs):
        if self.metadata == None:
            self.get_sensor_metadata()

        self.t_from = kwargs.get("t_from", self.t_from)
        self.t_to = kwargs.get("t_to", self.t_to)

        res = pd.DataFrame()
        all_data = False
        default_params = {'from-date': self.t_from,
                          'to-date': self.t_to,
                          'format': 'csv'}

        while not all_data:
            data = self.get_data(self.endpoint_merge('get_data'), params=default_params, format='csv')
            res = pd.concat([res, data], ignore_index=True)
            if len(data) > 0:
                last_date = data['createdAt'].iloc[-1]
                default_params ={'from-date': self.t_from,
                                 'to-date': last_date,
                                 'format': 'csv'}
            else:
                return(res.rename(columns={'value': self.metadata['title']}))
            if len(data) < 1000:
                all_data = True

        data_return = res.rename(columns={'value': self.metadata['title']})
        #data['createdAt'] = pd.to_datetime(data['createdAt'])
        self.data = data_return

        return data_return
