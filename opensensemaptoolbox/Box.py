import os
import requests
import pandas as pd
import geopandas as gpd
import numpy
import json
from io import StringIO
from urllib.parse import urljoin
from .APIressources import APIressources
from .Sensor import Sensor
from shapely import Point
import datetime as dt

import logging

logger = logging.getLogger('osm')


class Box(APIressources):
    def __init__(self, boxId: str):
        self.boxId = boxId
        self.sensors = []
        super().__init__(endpoints = {'box': {
                                        'endpoint': f'/boxes/{self.boxId}',
                                        'ref': 'https://docs.opensensemap.org/#api-Boxes-getBox'},
                                      'location': {
                                        'endpoint': f'/boxes/{self.boxId}/locations',
                                        'ref': 'https://docs.opensensemap.org/#api-Measurements-getLocations'}
                                     })
        self.metadata = self.get_box_metadata()
        self.locations = self.get_box_locations()
        self.get_box_sensors()
        self.data = self.get_box_data()
        self.a = 1

    def add_sensor(self, sensorId):
        if isinstance(sensorId, str):
            sensor = Sensor(self.boxId, sensorId)
            self.sensors.append(sensor)
        if isinstance(sensorId, list):
            if isinstance(sensorId[0], str):
                self.sensors = [Sensor(self.boxId, sId) for sId in sensorId]
            elif isinstance(sensorId[0], Sensor):
                self.sensors = sensorId
        if isinstance(sensorId, Sensor):
            self.sensors.append(sensorId)

    def get_box_metadata(self):
        data = self.get_data(self.endpoint_merge('box'))
        return data

    def get_box_sensors(self):
        ids = [sen['_id'] for sen in  self.metadata['sensors']]
        logger.info(f"found {len(ids)} sensor(s) for box '{self.boxId}' ")
        self.add_sensor(ids)

    def get_box_data(self):
        if len(self.sensors) > 1:
            logger.info(f"merging data for box '{self.boxId}' with {len(self.sensors)} sensor(s)")
            if len(self.sensors[0].data) == 0:
                pass
            merged_df = self.sensors[0].data
            for sensor in self.sensors[1:]:
                if len(sensor.data) == 0:
                    pass
                merged_df = pd.merge(merged_df, sensor.data, on='createdAt', how='outer')
                merged_df = merged_df.drop_duplicates(subset='createdAt', keep='first').reset_index(drop=True)
            merged_df['createdAt'] = pd.to_datetime(merged_df['createdAt'])
            merged_df['createdAt'] = merged_df['createdAt'].dt.tz_localize(None)


            loc = pd.merge(merged_df, self.locations, on='createdAt', how='outer')
            loc = loc.drop_duplicates(subset='createdAt', keep='first').reset_index(drop=True)

            gdf = gpd.GeoDataFrame(loc)
            gdf['createdAt'] = pd.to_datetime(gdf['createdAt'])
            #gdf['createdAt'] += pd.to_timedelta(1, unit='us')
            return gdf

        elif len(self.sensors) == 1:
            return

        else:
            logger.info('No sensors')
            return

    def get_box_locations(self):
        data = self.get_data(self.endpoint_merge('location'), params={'from-date': '1970-01-01T00:00:00Z',
                                                                          'to-date': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
                                                                          'format': 'json'}, format='json')
        coords = [Point(p['coordinates'][0], p['coordinates'][1]) for p in data]
        time = [p['timestamp'] for p in data]
        df = pd.DataFrame({'createdAt': time, 'geometry': coords}).drop_duplicates(subset='createdAt', keep='first').reset_index(drop=True)
        df['createdAt'] = pd.to_datetime(df['createdAt'])
        df['createdAt'] = df['createdAt'].dt.tz_localize(None)
        #df['createdAt'] += pd.to_timedelta(1, unit='us')
        return df
