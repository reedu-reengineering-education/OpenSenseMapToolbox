import os
import requests
import pandas as pd
import geopandas as gpd
import numpy
import json
from io import StringIO
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed


from .APIressources import APIressources
from .Box import Box


class OpenSenseMap(APIressources):
    def __init__(self):
        self.boxes = []
        super().__init__(endpoints={
            'tags': {
                'endpoint': '/tags',
                'ref': 'https://docs.opensensemap.org/#api-Boxes-getAllTags'
            },
            'box_data_bytag': {
                'endpoint': '/boxes/data/bytag',
                'ref': 'https://docs.opensensemap.org/#api-Measurements-getDataByGroupTag'
            },
        })

    def get_tags(self):
        data = self.get_data((self.endpoint_merge('tags')))
        return data

    def box_sensor_dict_by_tag(self, tag: str):
        data = self.get_data(self.endpoint_merge('box_data_bytag'), params=dict(grouptag=tag), format='json')
        box_ids = set(sorted([item['boxId'] for item in data]))
        boxes_sensors = [dict(boxId=box_id,
                              sensorId=list(set(sorted([item['sensorId'] for item in data if box_id == item['boxId']]))))
                         for box_id in box_ids]
        return boxes_sensors

    def add_box(self, boxId):
        if isinstance(boxId, str):
            box = Box(boxId)
            self.boxes.append(box)
        if isinstance(boxId, list):
            if isinstance(boxId[0], str):
                self.boxes = [Box(bId) for bId in boxId]
            if isinstance(boxId, Box):
                self.boxes = boxId
        if isinstance(boxId, Box):
            self.boxes.append(boxId)

    def save_OSM(self, **kwargs):
        mode = kwargs.get('mode', "csv")
        csv_base_path = kwargs.get('csv_base_path', './data')
        csv_name = kwargs.get('csv_name', 'data.csv')

        if len(self.boxes) > 0:
            if mode == 'csv':
                for box in self.boxes:
                    box.combine_records_with_fetched_data()
                    box_data_path = os.path.join(csv_base_path, box.boxId)
                    os.makedirs(box_data_path, exist_ok=True)
                    if isinstance(box.data, gpd.GeoDataFrame):
                        box.save_csv(data=box.data, path=os.path.join(box_data_path, csv_name))

    def fetch_box_data(self, **kwargs):
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(box.fetch_box_data, **kwargs) for box in self.boxes]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error fetching box data: {e}")

    def read_OSM(self, **kwargs):
        mode = kwargs.get('mode', None)
        if mode is None:
            print("need mode to read from datasource")
        else:
            for box in self.boxes:
                box.read_box_data(**kwargs)

    def update_OSM(self, **kwargs):
        self.read_OSM(**kwargs)
        for box in self.boxes:
            box.check_for_new_data()

