import os
import requests
import pandas as pd
import geopandas as gpd
import numpy
import json
from io import StringIO
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlalchemy


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
        self.modes = ['csv', 'postgis']
        self.all_box_ids_table = 'all_boxids'
        self.merged_gdf = None


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
        elif isinstance(boxId, list):
            if all(isinstance(box, str) for box in boxId):
                self.boxes = [Box(bId) for bId in boxId]
            elif all(isinstance(box, Box) for box in boxId):
                self.boxes = boxId
        elif isinstance(boxId, Box):
            self.boxes.append(boxId)


    def remove_box(self, boxId, **kwargs):
        rm_all = kwargs.get('all', False)
        if rm_all:
            self.boxes = []
        elif isinstance(boxId, str):
            self.boxes = [box for box in self.boxes if box.boxId != boxId]
        elif isinstance(boxId, list):
            if all(isinstance(box, str) for box in boxId):
                self.boxes = [box for box in self.boxes if box.boxId not in boxId]
            elif all(isinstance(box, Box) for box in boxId):
                remove_ids = [box.boxId for box in boxId]
                self.boxes = [box for box in self.boxes if box.boxId not in remove_ids]
        elif isinstance(boxId, Box):
            self.boxes = [box for box in self.boxes if box.boxId != boxId.boxId]


    def save_OSM(self, **kwargs):
        mode = kwargs.get('mode', "csv")
        csv_base_path = kwargs.get('csv_base_path', './data')
        csv_name = kwargs.get('csv_name', 'data.csv')
        engine = kwargs.get('engine', None)

        if mode is None or mode not in self.modes:
            print(f"""need 'mode' to read from datasource. Possible modes are: {' ,'.join(self.modes)}""")

        if len(self.boxes) > 0:
            if mode == 'csv':
                for box in self.boxes:
                    box.combine_records_with_fetched_data()
                    box_data_path = os.path.join(csv_base_path, box.boxId)
                    os.makedirs(box_data_path, exist_ok=True)
                    if isinstance(box.data, gpd.GeoDataFrame):
                        box.save_csv(data=box.data, path=os.path.join(box_data_path, csv_name))

            if mode == 'postgis':
                if engine is None or not isinstance(engine, sqlalchemy.engine.Engine):
                    print(f"you need a sql-alchemist engine to proceed ")
                    return
                if isinstance(engine, sqlalchemy.engine.Engine):
                    all_boxIds = pd.DataFrame(sorted([box.boxId for box in self.boxes]), columns=['id'])
                    all_boxIds.to_sql(self.all_box_ids_table, con=engine, if_exists="replace", index=False)
                    for box in self.boxes:
                        box.combine_records_with_fetched_data()
                        box.write_to_db(**kwargs)


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
        engine = kwargs.get('engine', None)

        if mode is None or mode not in self.modes:
            print(f"""need 'mode' to read from datasource. Possible modes are: {' ,'.join(self.modes)}""")
        else:
            if mode == 'postgis':
                df = pd.read_sql(f"SELECT * FROM {self.all_box_ids_table}", con=engine)
                box_ids = [i for i in df['id']]
                self.add_box(box_ids)
            for box in self.boxes:
                box.read_box_data(**kwargs)


    def update_OSM(self, **kwargs):
        self.read_OSM(**kwargs)
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(box.check_for_new_data) for box in self.boxes]
            for future in as_completed(futures):
                future.result()


    def merge_OSM(self, **kwargs):
        ids = kwargs.get('ids', None)
        if ids:
            buffer = []
            for box in self.boxes:
                if box.boxId in ids:
                    box.combine_records_with_fetched_data()
                    if box.data is not None:
                        box.data['id'] = box.boxId
                        buffer.append(box.data)
            print(buffer)
            clean_crs = [gdf.to_crs('EPSG:4326') for gdf in buffer]
            merged_gdf = gpd.GeoDataFrame(pd.concat(clean_crs, ignore_index=True))
            self.merged_gdf = merged_gdf

            return merged_gdf
        else:
            buffer = []
            for box in self.boxes:
                box.combine_records_with_fetched_data()
                if box.data is not None:
                    buffer.append(box.data)
            clean_crs = [gdf.to_crs("EPSG:4326") for gdf in buffer]
            merged_gdf = gpd.GeoDataFrame(pd.concat(clean_crs, ignore_index=True))
            self.merged_gdf = merged_gdf

            return merged_gdf
