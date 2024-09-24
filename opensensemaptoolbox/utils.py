import os
import pandas as pd
import geopandas as gpd
from shapely import LineString, Point

data = pd.read_csv("/work/PROJEKTE/ATRAI-BIKES/OpenSenseMapToolbox/data/6696762ce3b7f100086e80ff/data.csv")

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


def points_to_line(data):
    ps = pd.Series([x for x in data['geometry']])
    points = [parse_point(p) for p in ps]
    valid_points = [p for p in points if p is not None]

    return LineString(valid_points)


def extract_tours(data, tourcol = 'tour'):
    tours = [int(x) for x in data[tourcol].unique()]
    res = []
    res_tours = []
    for tour in tours:
        subset = data[data[tourcol] == tour]
        if len(subset) > 1:
            res_tours.append(tour)
            res.append(points_to_line(subset))

    gdf = gpd.GeoDataFrame(dict(tour=[f'tour_{x}' for x in res_tours],
                           geometry=res), geometry='geometry')

    return gdf

aa = extract_tours(data)

