# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 12:42:14 2017

@author: scotw

Convert .kml downloaded from google maps *with single polygon* to shapefile
"""

__version__ = 1.0

import pandas as pd
import geopandas as gpd
from bs4 import BeautifulSoup as bs
from io import StringIO
from shapely.geometry import Point, Polygon
from fiona.crs import from_epsg

def kml2shp(filename):
    # should check file exists
    with open(filename) as file:
        doc = bs(file, 'lxml')
    name = str(doc.placemark.find("name").string)
    coordinates = str(doc.placemark.coordinates.string)
    coords = StringIO(coordinates)
    coord_df = pd.read_csv(coords, header=None, names=["long", "lat", "x"])
    coord_df = coord_df[["long", "lat"]]
    points = []
    for index, coord in coord_df.iterrows():
        point = (coord["long"], coord["lat"])
        points.append(point)
    points.pop(-1)
    poly = Polygon(points)
    poly_gdf = gpd.GeoDataFrame({"geometry": [poly], "name":[name]})     
    poly_gdf.crs = from_epsg(4326)
#    poly_gdf.to_file((name+"_polygon.shp"))
        
    return poly_gdf


        
if __name__ == "__main__":
    gdf = kml2shp("Ladygrove.kml")