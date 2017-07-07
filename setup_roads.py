# -*- coding: utf-8 -*-

"""
Creates a GeoDataFrame containing LineStrings for all roads within area 
defined by exterior polygon. 

@author: Scot Wheeler
"""

__version__ = 2.1

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Polygon
import kml2shp
import plot_roads


class Network():
    """
    A network of roads
    
    Parameters
    ----------
    name : str
        Name to assign to road network
    exterior_file : .kml file
        polygon which defines the exterior of the network
        Created and downloaded in google maps
    roads_file : .shp file
        OpenStreetMap roads layer downloaded from 
        http://download.geofabrik.de/europe/great-britain/england/oxfordshire.html
    """
    def __init__(self, name = "Ladygrove", exterior_file="Ladygrove.kml", 
                 roads_file = "gis.osm_roads_free_1.shp"):
        self.name = name
        self.exterior_file = os.path.normpath(exterior_file)
        self.all_roads_file = os.path.normpath(roads_file)
        self.create_new_directory()
        
        self.exterior_gdf = self.get_exterior()
        self.roads = self.get_roads()
        self.save_files()
        
    def create_new_directory(self):
        """
        Creates a new subfolder for the network
        """
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
        """
        Checks if roads already created and saved as shp. If so, imports, else,
        creates new network.
        """
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
        roads_in_area = all_roads[in_area].copy()
        
        # filter possible residential
        named_roads = roads_in_area["name"].notnull()
        others = roads_in_area["fclass"].isin(["primary", "secondary", "tertiary", "residential", "unknown", "unclassified"])
        to_keep = (named_roads | others)
        roads = roads_in_area[to_keep]
        
        # create columns
        roads.loc[:, "houses"] = np.nan
        roads.loc[:, "colour"] = "Red"
        roads.loc[:, "linewidth"] = 1
        roads.loc[:, "status"] = "No"
        
        # define line widths
        roads.loc[roads["fclass"]=="primary", "linewidth"] = 3
        roads.loc[roads["fclass"]=="secondary", "linewidth"] = 2
             
        # reindex
        roads.index.names=["road_index"]
        roads.reset_index(inplace=True)
        
        # save output
#        output_shp_file = os.path.normpath(self.name + "\\" + self.name + "_roads.shp")
#        output_csv_file = os.path.normpath(self.name + "\\" + self.name + "_roads.csv")
#        roads.to_file(output_shp_file)
#        roads.to_csv(output_csv_file)
        
        return roads
    
    def save_files(self):
        """Saves roads shp file and csv file"""
        # drop x and y created after plotting, could be the issue with saving as shp
        save_roads = self.roads.drop(["x", "y"], axis=1, errors='ignore').copy()

        output_shp_file = os.path.normpath(self.name + "\\" + self.name + "_roads.shp")
        output_csv_file = os.path.normpath(self.name + "\\" + self.name + "_roads.csv")
        save_roads.to_file(output_shp_file)
        self.roads.to_csv(output_csv_file)
        
    def recreate_roads(self):
        """Recalls create_roads"""
        self.roads = self.create_roads()
        
    def update_roads(self):
        """ Updates the colours based on status"""
        self.roads.loc[self.roads["status"]=="Yes", "colour"] = "SpringGreen"
        self.roads.loc[self.roads["status"]=="Arranged", "colour"] = "Gold"
        self.roads.loc[self.roads["status"]=="No", "colour"] = "Red"
        self.save_files()
        
    def update_status(self, road, status="Yes"):
        """
        Updates status. Called by input_status, 
        and update_status_from_csv.
        
        Parameters
        ----------
        road : str
            Road name string
        status : str
            "Yes", "No", "Arranged"
        """
        pd.DataFrame
#        self.roads["delivered"][self.roads["name"] == road] = status
        if road not in self.roads["name"].values:
            print(road+" not found")
            return
        else:
            self.roads.loc[self.roads["name"] == road,"status"] = status
            self.update_roads()
                  
    def input_status(self):
        """
        Interface for updating status. Can also be done by editing 
        csv then calling update_status_from_csv
        """
        status = input("New 'Yes' status road names, comma separated: ")
        status_list = [x.lstrip() for x in status.split(',')]
        for road in status_list:
            self.update_status(road.title(), status="Yes")
        
        arranged = input("New 'Arranged' status road names, comma separated: ")
        arranged_list = [x.lstrip() for x in arranged.split(',')]
        for road in arranged_list:
            self.update_status(road.title(), status="Arranged")
        self.save_status_csv() # could be dangerous if something goes wrong above
                
    def save_status_csv(self):
        """
        Saves a simple csv of road name and status.
        """
        # potential problem if a previously unknown road name is updated
        # update delivered status from csv in case road names have been changed        
        road_name = []
        statuses = []
        for index, road in self.roads.iterrows():
            status = road["status"]
            if road["name"] != None:
                if road["name"] not in road_name:
                    road_name.append(road["name"])
                    statuses.append(road["status"])
                
        statuses_df = pd.DataFrame({"road":road_name, "status":statuses})
        statuses_csv_file = os.path.normpath(self.name 
                                             + "\\" + self.name 
                                             + "_status.csv")
        statuses_df.to_csv(statuses_csv_file, index=False)
        return statuses_df
    
    def update_status_from_csv(self):
        """ 
        This will update roads status from the values in the csv file
        Status updates can then be made by editing the csv file, rather than
        running 'input_status'.
        Also useful if road names are edited (ie if blank road name is corrected)
        """
        # this needs speeding up, only update if status has changed?
        # could check by running save_status_csv code to get old statuses df
        # without saving the csv file
        
        statuses_csv_file = os.path.normpath(self.name + "\\" 
                                             + self.name 
                                             + "_status.csv")
        statuses_df = pd.read_csv(statuses_csv_file)
        for index, road in statuses_df.iterrows():
            self.update_status(road["road"], status=road["status"])
            
    def update_road_name(self, road_index = None, new_name = None):
        """
        Use this to update road names. 
        
        Parameters
        ----------
        road_index : int
            Easiest to get from map
        new_name : str
            New road name
        """
        if road_index == None:
            road_index = int(input("Enter road index: "))
            road = self.roads[self.roads["road_index"] == road_index]
            # check if index is real
            print("Current name: "+ str(road["name"]))
            new_name = str(input("Enter new road name: "))
            # check if len(name)>0
        else:
            road = self.roads[self.roads["road_index"] == road_index]
            # check if index is real
            # check if len(name)>0
        road_index = road.index[0]
        self.roads["name"][road_index] = new_name
        self.update_status_from_csv()
    
    def reset(self):
        """
        This recreates roads if something goes wrong, or new road data
        is downloaded
        """
        self.roads = self.create_roads()
        self.update_status_from_csv()


if __name__ == "__main__":
    ladygrove_canvassing = Network(name="Ladygrove_canvassing")
    ladygrove_leafleting = Network(name="Ladygrove_leafleting")
#    ladygrove.reset()

#    ladygrove.update_status_from_csv()
#    ladygrove_canvassing.update_status_from_csv()

    ladygrove_leafleting.input_status()
#    ladygrove_canvassing.input_status()

#    ladygrove.update_road_name()
    plot_roads.create_plot(ladygrove_leafleting.name, ladygrove_leafleting.exterior_gdf, ladygrove_leafleting.roads)
    pass


