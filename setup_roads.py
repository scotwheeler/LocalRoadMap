
# coding: utf-8

# # Ladygrove delivery map

"""
Creates a GeoDataFrame containing LineStrings for all roads within area 
defined by exterior polygon. 
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Polygon
import kml2shp

import os
import numpy as np

import plot_roads


class Network():
    def __init__(self, name = "Ladygrove", exterior_file="Ladygrove.kml", 
                 roads_file = "gis.osm_roads_free_1.shp"):
        self.name = name
        self.exterior_file = os.path.normpath(exterior_file)
        self.all_roads_file = os.path.normpath(roads_file)
        self.create_new_directory()
        
        self.exterior_gdf = self.get_exterior()
        self.roads = self.get_roads()
        
    def create_new_directory(self):
        directory = os.path.normpath(self.name)
        if not os.path.isdir(directory):
            os.makedirs(self.name)
            
    def get_exterior(self):
        """
        Imports the exterior boundary from a .kml file containing a polygon 
        created in and downloaded from google maps.
        """
        new_path = os.path.normpath(self.name + "\\" + self.name + "_exterior.shp")
        if os.path.isfile(new_path):
            exterior=gpd.read_file(new_path)
        else:
            if self.exterior_file[-3:] == "kml":
                exterior = kml2shp.kml2shp(self.exterior_file)
                exterior.to_file(new_path)
        return exterior
        
    def get_roads(self):
        roads_shp_file = os.path.normpath(self.name + "\\" + self.name + "_roads.shp")
        if os.path.isfile(roads_shp_file):
            roads = gpd.read_file(roads_shp_file)
            print ("Found existing network")
        else:
            roads = self.create_roads()
            print ("Created new network")
        return roads
        
        
    def create_roads(self):
        """
        Imports roads file for county downloaded from xxx. 
        Filters roads within area defined by exterior.
        Filters possible residential roads, and those with names. 
        """
        all_roads = gpd.read_file(self.all_roads_file)
        
        #filter within exterior
        in_area = all_roads["geometry"].within(self.exterior_gdf["geometry"][0])
        roads_in_area = all_roads[in_area]
        
        # filter possible residential
        named_roads = roads_in_area["name"].notnull()
        others = roads_in_area["fclass"].isin(["primary", "secondary", "tertiary", "residential", "unknown", "unclassified"])
        to_keep = (named_roads | others)
        roads = roads_in_area[to_keep]
        
        # create columns
        roads["houses"] = np.nan
        roads["colour"] = "Red"
        roads["linewidth"] = 1
        roads["delivered"] = "No"
        
        # define line widths
        roads["linewidth"][roads["fclass"]=="primary"] = 3
        roads["linewidth"][roads["fclass"]=="secondary"] = 2
        
        # save output
        output_shp_file = os.path.normpath(self.name + "\\" + self.name + "_roads.shp")
        output_csv_file = os.path.normpath(self.name + "\\" + self.name + "_roads.csv")
        roads.to_file(output_shp_file)
        roads.to_csv(output_csv_file)
        
        return roads
    
    def resave_files(self):
        # save output
        output_shp_file = os.path.normpath(self.name + "\\" + self.name + "_roads.shp")
        output_csv_file = os.path.normpath(self.name + "\\" + self.name + "_roads.csv")
        self.roads.to_file(output_shp_file)
        self.roads.to_csv(output_csv_file)
        
    def recreate_roads(self):
        self.roads = self.create_roads()
        
    def update_roads(self):
        self.roads["colour"][self.roads["delivered"]=="Yes"] = "SpringGreen"
        self.roads["colour"][self.roads["delivered"]=="Arranged"] = "Gold"
        self.roads["colour"][self.roads["delivered"]=="No"] = "Red"
        self.resave_files()
        
    def update_delivery_status(self, road, status="Yes"):
        self.roads["delivered"][self.roads["name"] == road] = status
        self.update_roads()
                  
    def input_delivery_status(self):
        delivered = input("Newly delivered road names, comma separated:")
        delivered_list = [x.lstrip() for x in delivered.split(',')]
        for road in delivered_list:
            if road not in self.roads["name"].values:
                print(road+" not found")
            else:
                self.update_delivery_status(road, status="Yes")
        
        arranged = input("Newly arranged road names, comma separated:")
        arranged_list = [x.lstrip() for x in arranged.split(',')]
        for road in arranged_list:
            if road not in self.roads["name"].values:
                print(road+" not found")
            else:
                self.update_delivery_status(road, status="Arranged")


if __name__ == "__main__":
    ladygrove = Network()
    ladygrove.input_delivery_status()
    plot_roads.create_plot(ladygrove.name, ladygrove.exterior_gdf, ladygrove.roads)



