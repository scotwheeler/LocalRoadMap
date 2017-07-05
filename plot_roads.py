# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 20:56:54 2017

@author: scotw
"""

from shapely.geometry import Point, LineString, Polygon
import pandas as pd
import geopandas as gpd
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, HoverTool
#from bokeh.io import export_png

    
def getCoords(row, geom, coord_type):
    """
    Returns the coordinates ('x' of 'y') of shapely Point, LineString or 
    Polygon
    """
    item = row[geom]
    if type(item) == type(LineString()):
        if coord_type == 'x':
            return list( row[geom].coords.xy[0] )
        elif coord_type == 'y':
            return list( row[geom].coords.xy[1] )
    elif type(item) == type(Polygon()):
        # Parse the exterior of the coordinate
        exterior = row[geom].exterior
        if coord_type == 'x':
            # Get the x coordinates of the exterior
            return list( exterior.coords.xy[0] )
        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return list( exterior.coords.xy[1] )
    elif type(item) == type(Point()):
        if coord_type == 'x':
            return row[geom].x
        elif coord_type == 'y':
            return row[geom].y

def geometry_to_coordinates(gdf):
    """
    Converts shapely geometry to coordinates
    """
    gdf["x"] = gdf.apply(getCoords, geom = "geometry", coord_type = "x",
                         axis = 1)
    gdf["y"] = gdf.apply(getCoords, geom = "geometry", coord_type = "y",
                         axis = 1)

    return gdf

def create_cds(gdf):
    """
    Create bokeh ColumnDataSource from GeoDataFrame
    """
    #Convert shapely geometry to coordinates
    gdf_coords = geometry_to_coordinates(gdf)
    
    # create ColumnDataSource
    df = gdf_coords.drop('geometry', axis=1).copy()
    cds = ColumnDataSource(df)
    
    return cds
    
def create_plot(name, exterior, roads):
    exterior_cds = create_cds(exterior)
    roads_cds = create_cds(roads)
    
    tools = "pan, wheel_zoom, reset, hover, save"
    network_map = bk.Figure(tools=tools, active_scroll='wheel_zoom',
                            x_axis_location=None, y_axis_location=None, 
                            webgl=True)
    
    network_map.patches("x", "y", source=exterior_cds, fill_color=None,
                        line_color="black")
    
    roads_plot = network_map.multi_line("x", "y", source=roads_cds,
                                        color="colour", line_width=2)
    # for an unknown reason, defining line_width stops hover tool working
    
    hover = network_map.select_one(HoverTool)
    hover.renderers=[roads_plot]
    hover.point_policy = "follow_mouse"
    hover.tooltips = [("Name", "@name"),("Delivered", "@delivered")]
    bk.save(network_map, filename = (name+"_map.html"), title=(name+"_map"))
    bk.show(network_map)
    return network_map