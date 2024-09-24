import os
import pandas as pd
import geopandas as gpd
from shapely import LineString, Point


def create_tours(data, intervall = 15):
    data['createdAt'] = pd.to_datetime(data['createdAt'])
    data['tdiff'] = data['createdAt'].diff()
    data['tour'] = (data['tdiff'] > pd.Timedelta(minutes=intervall)).cumsum()
    data.drop(columns=['tdiff'])
    return data

def parse_point(point_str):
    if pd.isna(point_str):
        return None
    coords = point_str.strip('POINT ()').split()

    return Point(float(coords[0]), float(coords[1]))



def extract_tours(data, tourcol = 'tour'):
    tours = [int(x) for x in data[tourcol].unique()]
    res = []
    res_tours = []
    for tour in tours:
        subset = data[data[tourcol] == tour]
        ps = pd.Series([x for x in subset['geometry']])
        points = [parse_point(p) for p in ps]
        valid_points = [p for p in points if p is not None]
        if len(valid_points) > 1:
            res_tours.append(tour)
            res.append(LineString(valid_points))

    gdf = gpd.GeoDataFrame(dict(tour=[f'tour_{x}' for x in res_tours],
                           geometry=res), geometry='geometry').set_crs('EPSG:4326')

    return gdf



