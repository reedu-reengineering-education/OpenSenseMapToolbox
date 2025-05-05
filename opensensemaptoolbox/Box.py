import os
import requests
import pandas as pd
import geopandas as gpd
import numpy
import json
from io import StringIO
from urllib.parse import urljoin

import sqlalchemy

from .APIressources import APIressources
from .Sensor import Sensor
from shapely import Point
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        self.metadata = None
        self.locations = None
        # self.get_box_sensors()
        self.data = None
        self.data_fetched = None
        self.data_read = None
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
        if self.metadata is None:
            self.metadata = self.get_box_metadata()
        ids = [sen['_id'] for sen in  self.metadata['sensors']]
        logger.info(f"found {len(ids)} sensor(s) for box '{self.boxId}' ")
        self.add_sensor(ids)


    def get_box_sensors_data(self, **kwargs):
        if len(self.sensors) == 0:
            self.get_box_sensors()
        # for sens in self.sensors:
        #     sens.get_sensor_data(**kwargs)

        with ThreadPoolExecutor(max_workers=19) as executor:
            futures = [executor.submit(sensor.get_sensor_data, **kwargs) for sensor in self.sensors]
            for future in as_completed(futures):
                try:
                    future.result()  # Wait for each sensor data fetching to complete
                except Exception as e:
                    logger.error(f"Error fetching sensor data: {e}")


    def merge_sensors_data(self, **kwargs):
        if self.sensors is None:
            self.get_box_sensors_data(**kwargs)
        if self.locations is None:
            self.locations = self.get_box_locations()

        valid_sensors = [sensor for sensor in self.sensors if sensor.data is not None]
        if len(valid_sensors) == 0:
            return None

        logger.info(f"Merging data for box '{self.boxId}' with {len(valid_sensors)} valid sensor(s)")
        merged_df = valid_sensors[0].data

        for sensor in valid_sensors[1:]:
            if len(sensor.data) == 0:
                continue
            merged_df = pd.merge(merged_df, sensor.data, on='createdAt', how='outer')
            merged_df = merged_df.drop_duplicates(subset='createdAt', keep='first').reset_index(drop=True)

        merged_df['createdAt'] = pd.to_datetime(merged_df['createdAt']).dt.tz_localize(None)
        # merged_df['createdAt'] = pd.to_datetime(merged_df['createdAt']).dt.tz_localize(None).dt.strftime(
        #     '%Y-%m-%d %H:%M:%S')
        loc = pd.merge(merged_df, self.locations, on='createdAt', how='outer')
        loc = loc.drop_duplicates(subset='createdAt', keep='first').reset_index(drop=True)
        gdf = gpd.GeoDataFrame(loc)
        gdf['createdAt'] = pd.to_datetime(gdf['createdAt'])
        gdf.set_crs("EPSG:4326", inplace=True)

        return gdf


    def get_box_locations(self, **kwargs):
        self.t_from = kwargs.get("t_from", self.t_from)
        self.t_to = kwargs.get("t_to", self.t_to)
        data = self.get_data(self.endpoint_merge('location'), params={'from-date': self.t_from,
                                                                          'to-date': self.t_to,
                                                                          'format': 'json'}, format='json')
        coords = [Point(p['coordinates'][0], p['coordinates'][1]) for p in data]
        time = [p['timestamp'] for p in data]
        df = pd.DataFrame({'createdAt': time, 'geometry': coords}).drop_duplicates(subset='createdAt', keep='first').reset_index(drop=True)
        df['createdAt'] = pd.to_datetime(df['createdAt'])
        df['createdAt'] = df['createdAt'].dt.tz_localize(None)
        #df['createdAt'] += pd.to_timedelta(1, unit='us')

        return df


    def fetch_box_data(self, **kwargs):
        self.metadata = self.get_box_metadata()
        self.locations = self.get_box_locations(**kwargs)
        self.get_box_sensors_data(**kwargs)
        self.data_fetched = self.merge_sensors_data(**kwargs)



    def read_box_data(self, **kwargs):
        mode = kwargs.get('mode', None)
        csv_base_path = kwargs.get('csv_base_path', './data')
        csv_name = kwargs.get('csv_name', 'data.csv')
        engine = kwargs.get('engine', None)

        if mode == 'csv':
            print(f"Reading csv '{csv_name}' from '{csv_base_path}' for box '{self.boxId}'")
            csv_file_path = os.path.join(csv_base_path, self.boxId, csv_name)
            if os.path.exists(csv_file_path):
                df = pd.read_csv(csv_file_path, index_col=False)
                df['geometry'] = df['geometry'].astype(str)
                df['geometry'] = df['geometry'].apply(lambda x: x if x != 'nan' else None)
                df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'], crs='EPSG:4326')
                gdf = gpd.GeoDataFrame(df, geometry='geometry')

                # df['createdAt'] = pd.to_datetime(df['createdAt'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
                self.data_read = gdf
                return gdf

        if mode == 'postgis':
            inspector = sqlalchemy.inspect(engine)
            table_exists = self.boxId in inspector.get_table_names()
            if table_exists:
                gdf = gpd.read_postgis(sql=f"""SELECT * FROM "{self.boxId}"; """, con=engine, geom_col='geometry')
                self.data_read = gdf
                return gdf
            else:
                return None


    def combine_records_with_fetched_data(self, **kwargs):

        if self.data_fetched is None and self.data_read is None:
            print("Cannot combine data need to fetch or read first!")
            return
        elif self.data_fetched is not None and self.data_read is None:
            self.data = self.data_fetched
        elif self.data_fetched is None and self.data_read is not None:
            self.data = self.data_read
        elif self.data_fetched is not None and self.data_read is not None:
            # self.data_fetched['createdAt'] = self.data_fetched['createdAt'].apply(
            #     lambda x: x.strftime('%Y-%m-%d %H:%M:%S.') + f"{x.microsecond:06d}"
            # )
            df = pd.concat([self.data_read, self.data_fetched]).reset_index(drop=True)
            df = df.drop_duplicates(subset='createdAt', keep='first')
            self.data = gpd.GeoDataFrame(df, geometry='geometry')

            # todo:
            # self.data = self.combine_fetch_read_data(self.data_read, self.data_fetched)


    def check_for_new_data(self, **kwargs):
        self.metadata = self.get_box_metadata()
        if self.data_read is None:
            self.fetch_box_data()
            return
        lastEntry = pd.to_datetime(self.data_read.iloc[-1]['createdAt']).tz_localize('UTC')
        lastMeasurement = pd.to_datetime(self.metadata['lastMeasurementAt'])
        if  lastEntry != lastMeasurement:
            self.fetch_box_data(
                t_from=lastEntry.strftime('%Y-%m-%dT%H:%M:%SZ'),
                t_to=lastMeasurement.strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.combine_records_with_fetched_data()


    def write_to_db(self, **kwargs):
        engine = kwargs.get('engine', None)
        if isinstance(self.data, gpd.GeoDataFrame):
            # Add tags column to the GeoDataFrame
            tags = self.metadata.get('tags', []) if self.metadata else []
            self.data['tags'] = ','.join(tags)  # Convert tags list to a comma-separated string

            # Write to PostGIS
            self.data.to_postgis(name=self.boxId, con=engine, if_exists='replace', index=False)
