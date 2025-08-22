import io
import warnings
warnings.filterwarnings("ignore")
import dash
from dash import dcc, html, Dash, Input, Output, State, ctx
import geojson
import webbrowser
import pandas as pd
import geopandas as gpd
import psycopg2
from joblib import Parallel, delayed
import numpy as np
import plotly.colors as pc
import dash_leaflet as dl
from scipy.stats import gaussian_kde
import plotly.graph_objects as go
import dash_leaflet.express as dlx
from shapely.geometry import Point, LineString, Polygon
import pickle
import os
import plotly.graph_objects as go
from geopy.distance import geodesic
import random 
from tqdm import tqdm
from sklearn.neighbors import BallTree
import numpy as np
from sklearn.cluster import DBSCAN
from SQLQueries import *
import folium
import dash_mantine_components as dmc
import pickle
dmc.add_figure_templates()
import plotly.io as pio
from CacheScript import *

# ****************************************************************************************************************************************************
#   FILE PATHS
# ****************************************************************************************************************************************************

geojson_file_path = './assets/Data/Geojson'
shapefile_path = './assets/Data/Shapefiles'
data_path = './assets/Data'

# ****************************************************************************************************************************************************
# MAPPING VARIABLES 
# ****************************************************************************************************************************************************

commodity_map = {'sctg0109': 'Agricultural products', 'sctg1014': 'Gravel and mining products',
                 'sctg1519': 'Coal and other energy products', 'sctg2033': 'Chemical, wood and metals',
                 'sctg3499': 'Manufactured goods and Unknown'}
transport_mode_map = {'11': 'Truck/Air', '2': 'Rail', '3': 'Water', '5': 'Multiple modes and mail', '6': 'Pipeline'}
mode_zonal_flows = {1: 'Truck', 2: 'Rail', 3: 'Water', 4: 'Air', 5: 'Pipeline', 6: 'Multiple modes and mail', 7: 'Other'}

railroads = [
    "GSWR", "VR", "HOG", "GC", "IMRR", "TPW", "ISRR", "IORY",
    "YB", "CFE", "CUOH", "CIND", "MVRY", "YARR", "CCKY"
]

flow2Color = {'Total': 'YlOrRd', 'Inbound': 'reds', 'Outbound': 'emrld', 'Within': 'amp'}
roadColorMap = {'I':'black', 'U':'purple', 'S': 'blue'}
LTLColorMap = {'Oak Harbor Freight Lines': 'black', 'Dayton Freight Lines': 'blue', 'A. Duie Pyle': 'grey',
                'Southeastern Freight Lines': 'purple', 'Central Freight Lines': 'pink', 'Wilson Trucking': 'yellow',
                'Old Dominion Freight Line': 'red', 'Estes Express Lines': 'green', 'Saia Motor Freight Line LLC': 'orange'}
IMColorMap = { rr: "#{:06x}".format(random.randint(0, 0xFFFFFF)) for rr in railroads}
# railColorMap = {'NS': 'green', 'CSXT': 'brown'} #, 'GFRR': 'blue', 'FGA': 'red', 'PVTX': 'purple', 'SAPT': 'brown'}
railColorMap = {'NS': 'green'}
GWColorMap = {'Origin': 'red', 'Destination': 'gold'}
HubColorMap = {'Regional Hub': 'darkmagenta', 'Gateway Hub': 'springgreen'}
colorbar_bg_color = "rgba(173, 216, 230, 1)"
REGION_COLORSCALE = 'OrRd'  #'OrRd' #'blues'
FLOWLINES_COLORSCALE = 'black'
TRANSLOAD_COLORSCALE = 'purples'
MAX_TRUCK_PALLETS = 26 # Single floor of 53ft container
BOX_CAR_PALLETS = 28 # Single floor of 60'9" * 13 * 9'6"
PALLET_CAPACITY = 1500 # in lbs
flowMap = {'Total': 'Total', 'Inbound': 'inbound', 'Outbound': 'outbound', 'Within': 'inter'}

# ****************************************************************************************************************************************************
#   FUNCTIONS
# ****************************************************************************************************************************************************

def read_county_shapes(shapes_query):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=USER_NAME,
        password=PASSWORD,
        host=HOST,
        port=DB_PORT
    )
    county_shapes = gpd.read_postgis(shapes_query, conn, geom_col='geom')
    conn.close()
    county_shapes[['intptlat', 'intptlon']] = county_shapes[['intptlat', 'intptlon']].astype(float)
    return county_shapes


# ****************************************************************
#   DATABASE WRITE FUNCTIONS
# ****************************************************************

def find_gnw_counties(transload_locs, county_gdf, max_distance_miles=50, write_flag = True):
    
    """ Function to find counties within a specified distance of Genesee and Wyoming Transload Station locations
    Args:
        transload_locs (dict): Dictionary of intermodal locations with keys as tuples of (location, provider) and values as Point geometries.
        county_gdf (GeoDataFrame): GeoDataFrame containing county geometries.
        max_distance_miles (float): Maximum distance in miles to consider for finding intersecting counties.
        write_flag (bool): Flag to indicate whether to write the results to a database.
    Returns:
        terminal_county_map (dict): Dictionary mapping intermodal locations to lists of intersecting county GEOIDs
    """
    
    terminal_county_map = {}
    county_centroids = {row.geoid : (row.geom.centroid.y,row.geom.centroid.x)for row in county_gdf.itertuples()}
    county_coords = np.array([[coords[0], coords[1]] for coords in county_centroids.values()])
    terminal_coords = np.array([[terminal_point.y, terminal_point.x] for terminal_point in transload_locs.values()])
    
    # Convert miles to radians for haversine metric
    max_distance_radians = max_distance_miles / 3958.8  # Earth's radius in miles
    
    # Build BallTree
    tree = BallTree(np.radians(county_coords), metric='haversine')
    
    # Query BallTree for neighbors within max_distance_radians
    indices = tree.query_radius(np.radians(terminal_coords), r=max_distance_radians)
    
    # Map terminals to intersecting counties
    terminal_county_map = {}
    if write_flag:
        for idx, ((location, provider), terminal_point) in enumerate(transload_locs.items()):
            print(f"Processing terminal {idx + 1}/{len(transload_locs)}: {location}, {provider}")
            intersecting_geoids = [list(county_centroids.keys())[i] for i in indices[idx]]
            terminal_county_map[(location, provider)] = intersecting_geoids
        
        with open(f'{data_path}/transload_county_map.pkl', 'wb') as file:
            pickle.dump(terminal_county_map, file)
    
    else:
        indices = []
        
    return terminal_county_map


def write_transload_counties():
    """
    Function to write counties near transload locations to a database
    """
    county_shapes_gdf = read_county_shapes(all_county_shapes_query)
    county_boundaries = dict(zip(county_shapes_gdf['geoid'], county_shapes_gdf['geom']))
    county_centroids = {geoid: county_boundaries[geoid].centroid.coords[0][::-1] for geoid in county_boundaries}
    
    # Identify counties near Genesee and Wyoming Transload Stations
    transload_locations_df = pd.read_csv('./assets/Data/G&W_Transload_Stations_Coords.csv')
    transload_locations_df['geometry'] = transload_locations_df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
    transload_locs = dict(zip(zip(transload_locations_df['Code'], transload_locations_df['ServiceRR']), transload_locations_df['geometry']))
    transload_county_map = find_gnw_counties(transload_locs, county_shapes_gdf, max_distance_miles=50)

    # Filter Chicago NS terminals and find counties near them
    ns_terminals_gdf = gpd.read_file(f'{geojson_file_path}/IM_Terminals_NS.geojson')
    chicago_ns_terminals_gdf = ns_terminals_gdf[ns_terminals_gdf['Location'].str.contains('Chicago')].reset_index()
    chicago_ns_locs = dict(zip(zip(chicago_ns_terminals_gdf['Location'], chicago_ns_terminals_gdf['Service Provider']), chicago_ns_terminals_gdf['geometry']))
    chicago_loc_county_map = find_gnw_counties(chicago_ns_locs, county_shapes_gdf, max_distance_miles=50)
    transload_county_map.update(chicago_loc_county_map)
    
    # Add Counties around HOG, CG 
    class3_rail_roads_gdf = gpd.read_file(f'{geojson_file_path}/rail_roads_class_3_transload.geojson')
    class3_rail_roads_gdf = class3_rail_roads_gdf[class3_rail_roads_gdf['RROWNER1'].isin(['HOG', 'GC', 'CCKY'])]

    def find_counties_near_class3_railroads(class3_rail_roads_gdf, county_gdf, max_distance_miles=5):
        """
        Find counties within a specified distance of Class 3 railroads using spatial join.
        """
        # Rough conversion: 1 degree ≈ 69 miles (only valid for small distances)
        buffer_degrees = max_distance_miles / 69.0
        # Buffer the railroad geometries
        class3_rail_roads_gdf['geometry'] = class3_rail_roads_gdf.geometry.buffer(buffer_degrees)
        if class3_rail_roads_gdf.crs != county_gdf.crs: 
            county_gdf = county_gdf.to_crs(class3_rail_roads_gdf.crs)
        # Perform spatial join to find intersecting counties
        joined = gpd.sjoin(county_gdf, class3_rail_roads_gdf, how="inner", predicate='intersects')
        # Build mapping from railroad owner to list of intersecting counties
        railroad_county_map = (joined.groupby('RROWNER1')['geoid'].apply(lambda x: list(set(x))).to_dict())

        return railroad_county_map

    # Call the function to find counties near Class 3 railroads
    class3_railroad_county_map = find_counties_near_class3_railroads(class3_rail_roads_gdf, county_shapes_gdf, max_distance_miles=1)
    
    se_orig_counties = set()
    for railroad, counties in class3_railroad_county_map.items():
        se_orig_counties.update(counties)
 
    se_orig_counties_df = pd.DataFrame({'geoid': list(se_orig_counties)})
    create_sql_table(ll_se_counties_table_query)
    insert_chunk(se_orig_counties_df, 'll_se_counties')
    
    
    # for owner, counties in class3_railroad_county_map.items():
    #     transload_county_map[(f"Class3_{owner}", owner)] = counties
    
    # Plot the railroads and counties
    def plot_railroads_and_counties(class3_rail_roads_gdf, county_shapes_gdf, class3_railroad_county_map):
        """
        Function to plot Class 3 railroads and their associated counties
        """
        # Create a folium map centered on the data
        center_lat = class3_rail_roads_gdf.geometry.centroid.y.mean()
        center_lon = class3_rail_roads_gdf.geometry.centroid.x.mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
        
        # Plot railroads
        for _, railroad_row in class3_rail_roads_gdf.iterrows():
            railroad_owner = railroad_row['RROWNER1']
            folium.GeoJson(
                railroad_row['geometry'],
                style_function=lambda x, owner=railroad_owner: {
                    'color': IMColorMap.get(owner, 'red'),
                    'weight': 3,
                    'opacity': 0.8
                },
                tooltip=f"Railroad: {railroad_owner}"
            ).add_to(m)
        
        # Plot counties within 5 miles
        for owner, county_geoids in class3_railroad_county_map.items():
            for geoid in county_geoids:
                county_row = county_shapes_gdf[county_shapes_gdf['geoid'] == geoid]
                if not county_row.empty:
                    county_geom = county_row.iloc[0]['geom']
                    county_name = county_row.iloc[0]['name']
                    folium.GeoJson(
                        county_geom,
                        style_function=lambda x: {
                            'fillColor': 'lightblue',
                            'color': 'blue',
                            'weight': 2,
                            'fillOpacity': 0.3
                        },
                        tooltip=f"County: {county_name}, GEOID: {geoid}"
                    ).add_to(m)
        
        # Save the map
        m.save(f'{data_path}/class3_railroads_counties_map.html')
        print(f"Map saved to {data_path}/class3_railroads_counties_map.html")
        
        return m
    
    # counties_plot = plot_railroads_and_counties(class3_rail_roads_gdf, county_shapes_gdf, class3_railroad_county_map)
    
    
    # Find unique counties from the transload county map
    unique_counties = set()
    for counties in transload_county_map.values():
        unique_counties.update(counties)
    print(f"Unique counties: {len(unique_counties)}")
    unique_counties = list(unique_counties)
    transload_county_df = pd.DataFrame()
    transload_county_df['geoid'] = unique_counties
    
    #TODO: Create a new database table for Counties near HOG and CG Track along with Chatham and Hamilton, TN Counties

    # Create and insert the transload counties table
    create_sql_table(transload_counties_table_query)
    insert_chunk(transload_county_df, 'transload_counties')

# ****************************************************************
#   DATA FUNCTIONS AND CALLS
# ****************************************************************

def read_transload_layers(transload_gdf):
    """ 
    Function to read transload layers and prepare GeoDataFrames for intermodal terminals, LTL carriers, and transload flows.
    Args:
        - transload_gdf (GeoDataFrame): GeoDataFrame containing transload county geometries.
    Returns:
        - transload_gdf (GeoDataFrame): Updated GeoDataFrame with transload county geometries.
        - transload_OD_flows_df (DataFrame): DataFrame containing transload O-D flows.
        - class1_rail_roads_gdf (GeoDataFrame): GeoDataFrame containing Class 1 railroads.
        - class3_rail_roads_gdf (GeoDataFrame): GeoDataFrame containing Class 3 railroads.
        - transload_county_centroids (dict): Dictionary mapping transload county GEOIDs to their centroids.
        - se_transload_flows_dict (dict): Dictionary mapping Southeastern region transload flows.
        - intermodal_terminals_gdf (GeoDataFrame): GeoDataFrame containing intermodal terminals.
        - LTL_carriers_gdf (GeoDataFrame): GeoDataFrame containing LTL carriers.
    """
    intermodal_term_df = pd.read_csv(f'{data_path}/G&W_Transload_Stations_Coords.csv')
    intermodal_term_df['color'] = np.where(intermodal_term_df['State'] == 'GA', GWColorMap['Origin'], GWColorMap['Destination'])
    intermodal_term_df['geometry'] = intermodal_term_df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
    intermodal_terminals_gdf = gpd.GeoDataFrame(intermodal_term_df, geometry='geometry')
    
    LTL_carriers_df = pd.read_csv(f'{data_path}/LTL_Regional&National.csv')
    LTL_carriers_df = LTL_carriers_df[LTL_carriers_df['State'] == 'GA']
    LTL_carriers_df.rename(columns={'Company Name': 'Company'}, inplace=True)
    LTL_carriers_df['color'] = LTL_carriers_df['Company'].map(LTLColorMap)
    LTL_carriers_df['geometry'] = LTL_carriers_df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
    LTL_carriers_gdf = gpd.GeoDataFrame(LTL_carriers_df, geometry='geometry')
    
    transload_county_names = {row.geoid: row.name + ', ' + row.state_name for row in transload_gdf.itertuples()}
    transload_OD_flows_df = select_data(transload_flows_query)
    transload_OD_flows_df['orig_cnty_name'] = transload_OD_flows_df['orig_cnty'].map(SE_county_names)
    transload_OD_flows_df['dest_cnty_name'] = transload_OD_flows_df['dest_cnty'].map(transload_county_names)
    transload_OD_flows_df = transload_OD_flows_df.groupby(['orig_cnty', 'orig_cnty_name', 'orig_reg','dest_cnty', 'dest_cnty_name','commodity_code'])['tons'].sum().reset_index()
    dest_cnty_flows_df = transload_OD_flows_df.groupby(['dest_cnty', 'dest_cnty_name'])['tons'].sum().reset_index()
    dest_cnty_flows_df['tons'] = dest_cnty_flows_df['tons'].round(1)
    dest_cnty_flows_dict = dict(zip(dest_cnty_flows_df['dest_cnty'], dest_cnty_flows_df['tons']))
    
    se_transload_flows_df = transload_OD_flows_df.groupby(['orig_reg'])['tons'].sum().reset_index()
    se_transload_flows_df['tons'] = se_transload_flows_df['tons'].round(1)
    se_transload_flows_dict = dict(zip(se_transload_flows_df['orig_reg'], se_transload_flows_df['tons']))
    
    transload_gdf['SE_Inbound_Flow'] = transload_gdf['geoid'].map(dest_cnty_flows_dict)    

    # rail_roads_gdf = gpd.read_file(f'{geojson_file_path}/us_railroads.geojson')
    # rail_roads_IM_gdf = rail_roads_gdf[rail_roads_gdf['RROWNER1'].isin(['NS','CSXT'])].copy()
    # rail_roads_IM_gdf.to_file(f'{geojson_file_path}/us_railroads_ns_csx.geojson', driver='GeoJSON')
    
    class1_rail_roads_gdf = gpd.read_file(f'{geojson_file_path}/us_railroads_ns_csx.geojson')
    class1_rail_roads_gdf = class1_rail_roads_gdf[class1_rail_roads_gdf['RROWNER1'] == 'NS']
    class1_rail_roads_gdf['geometry'] = class1_rail_roads_gdf['geometry'].apply(lambda x: x.simplify(0.05, preserve_topology=True))
    class3_rail_roads_gdf = gpd.read_file(f'{geojson_file_path}/rail_roads_class_3_transload.geojson')
    class3_rail_roads_gdf['geometry'] = class3_rail_roads_gdf['geometry'].apply(lambda x: x.simplify(0.05, preserve_topology=True))
    
    interstates_gdf = gpd.read_file(f'{geojson_file_path}/roads.geojson')
    interstates_gdf['geometry'] = interstates_gdf['geometry'].apply(lambda x: x.simplify(0.05, preserve_topology=True))
    
    return transload_gdf, transload_OD_flows_df, class1_rail_roads_gdf, class3_rail_roads_gdf, transload_county_centroids, se_transload_flows_dict, intermodal_terminals_gdf, LTL_carriers_gdf, interstates_gdf

# ****************************************************************
#   DROPDOWN AND SLIDER FUNCTIONS
# ****************************************************************
# ---------------------------------------
#   DROPDOWN COMPONENT
# ---------------------------------------

def create_mantine_dropdown(title, comp_id, menu_options, initial_val, multi=False, persistence=False):
    """ 
    Function to create a dropdown menu component using Dash Mantine Components
    """
    dropdown_component = dmc.Paper([
        dmc.Select(
            id=comp_id,
            label=title,
            data=menu_options,
            value=initial_val,
            searchable=True,
            clearable=True,
            variant='filled',
            ta='center',
            persistence=persistence,
            size="xs",
            style={'width': '100%'},
            styles = {'input': {'textAlign': 'center', 'justifyContent': 'center', 'backgroundColor': "#d4d1a6"}}
        ) if not multi else dmc.MultiSelect(
            id=comp_id,
            label=title,
            data=menu_options,
            value=initial_val if isinstance(initial_val, list) else [initial_val] if initial_val else [],
            searchable=True,
            persistence=persistence,
            clearable=True,
            variant='filled',
            ta='center',
            size="xs",
            style={
                'width': '100%',
                'maxHeight': '60px',
                'overflowY': 'auto',
                'flex': '0 0 50px',  # Prevent growing, fixed height
            },
            styles={
                'dropdown': {'zIndex': 2000, 'backgroundColor': "#d4d1a6"},
                'value': {'overflowY': 'auto'}, # Limit selected area height, scroll if overflow,
                'input': {'textAlign': 'center', 'justifyContent': 'center'}
            }
        )
    ],
    p='md',
    shadow='md',
    radius='md',
    withBorder=True                               
    )
    
    return dropdown_component
    
# ---------------------------------------
#   SLIDER COMPONENT
# ---------------------------------------
def create_mantine_slider(title, comp_id, min_val, max_val, steps, val, label_on, persistence=False):
    """ 
    Function to create a slider component using Dash Mantine Components
    """
    slider_component = dmc.Paper([
                                dmc.Flex([
                                    dmc.Text(title, fw=500, size="xs", ta="center"),
                                    dmc.Slider(
                                        id=comp_id,
                                        min=min_val,
                                        max=max_val,
                                        step=steps,
                                        value=val,
                                        color='orange',
                                        labelAlwaysOn=label_on,
                                        persistence=persistence,
                                        size="sm",
                                        w='100%',
                                        marks=[
                                            {"value": min_val, "label": f"{min_val}%"},
                                            {"value": max_val, "label": f"{max_val}%"}
                                        ],
                                        styles={
                                            "mark": {"fontSize": "10px"},
                                            "markLabel": {"fontSize": "10px", "whiteSpace": "nowrap"}
                                        }
                                    )
                                ],
                                mt=3,
                                mb=5,
                                direction = 'column',
                                justify="center",
                                align="center"
                            )
                        ],
                        shadow='md',
                        radius='md',
                        p='lg',
                        withBorder=True
    )
    
    return slider_component

# ---------------------------------------
#   INPUT BOX COMPONENT
# ---------------------------------------
def create_mantine_input_box(title, comp_id, placeholder, input_type="text", value=None, maxlength=None):
    """ 
    Function to create an input box component using Dash Mantine Components
    """
    input_component = dmc.Paper([
        dmc.NumberInput(
        id=comp_id,
        label=title,
        ta='center',
        placeholder=placeholder,
        value=value,
        max=maxlength if input_type == "number" else None,
        style={'width': '100%'}
    ) if input_type == "number" else dmc.TextInput(
        id=comp_id,
        label=title,
        ta='center',
        placeholder=placeholder,
        value=value,
        maxLength=maxlength,
        style={'width': '100%'}
    )],
    p ='md', 
    shadow='md',
    radius='md',
    withBorder=True
    )
    
    return input_component

# ****************************************************************************************************************************************************
#                                                                   DATA
# ****************************************************************************************************************************************************

# ---------------------------------
# SE Region Clusters and Counties
# ---------------------------------
cache_file = './assets/Data/se_region_cache.pkl'
cache_exists = os.path.exists(cache_file)
if cache_exists:
    with open(cache_file, 'rb') as f:
        (
            US_SE_region_clusters,
            region_cluster_centroids,
            US_SE_counties,
            SE_county_centroids,
            SE_county_names,
            county_region_mapping,
            region_county_mapping,
            gnw_se_counties_df,
            SE_regional_hubs_gdf,
            SE_gateway_hubs_gdf
        ) = pickle.load(f)
else:
    conn = psycopg2.connect(
            dbname=DB_NAME,
            user=USER_NAME,
            password=PASSWORD,
            host=HOST,
            port=DB_PORT
        )
    US_SE_region_clusters = gpd.read_postgis(US_SE_region_query, conn, geom_col='geom')
    conn.close()

    region_cluster_centroids = {row.cluster_id: row.geom.centroid.coords[0] for row in US_SE_region_clusters.itertuples()}
    US_SE_counties = read_county_shapes(US_SE_county_query)
    US_SE_counties['geom'] = US_SE_counties['geom'].simplify(0.05, preserve_topology=True)
    SE_county_centroids = {row.geoid: row.geom.centroid.coords[0] for row in US_SE_counties.itertuples()}
    SE_county_names = {row.geoid: f"{row.name}, {row.state_name}" for row in US_SE_counties[['geoid', 'name', 'state_name']].drop_duplicates().sort_values(by='state_name').itertuples()}

    county_region_cluster_mapping_df = select_data(region_cluster_county_mapping_query)
    county_region_mapping = dict(zip(county_region_cluster_mapping_df['geoid'], county_region_cluster_mapping_df['cluster_id']))
    region_county_mapping = {row.cluster_id : [] for row in US_SE_region_clusters.itertuples()}
    for row in county_region_cluster_mapping_df.itertuples():
        if row.geoid not in region_county_mapping[row.cluster_id]:
            region_county_mapping[row.cluster_id].append(row.geoid)
            
    SE_regional_hubs_df = pd.read_csv(f'{data_path}/SE_Regional_Hubs.csv')
    SE_regional_hubs_df = SE_regional_hubs_df.rename(columns={'lon': 'Longitude', 'lat': 'Latitude'})
    SE_regional_hubs_df['geometry'] = SE_regional_hubs_df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
    SE_regional_hubs_gdf = gpd.GeoDataFrame(SE_regional_hubs_df, geometry='geometry')

    SE_gateway_hubs_df = pd.read_csv(f'{data_path}/SE_Gateway_Hubs.csv')
    SE_gateway_hubs_df['geometry'] = SE_gateway_hubs_df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
    SE_gateway_hubs_gdf = gpd.GeoDataFrame(SE_gateway_hubs_df, geometry='geometry')
    
    gnw_se_counties_df = select_data(ll_se_counties_read_query)
    
    # Save to cache
    with open(cache_file, 'wb') as f:
        pickle.dump(
            (
                US_SE_region_clusters,
                region_cluster_centroids,
                US_SE_counties,
                SE_county_centroids,
                SE_county_names,
                county_region_mapping,
                region_county_mapping,
                gnw_se_counties_df,
                SE_regional_hubs_gdf,
                SE_gateway_hubs_gdf
            ),
            f
        )


# ---------------------------------
# Transload Counties and Flows
# ---------------------------------
transload_cache_file = './assets/Data/transload_cache.pkl'
transload_cache_exists = os.path.exists(transload_cache_file)
if transload_cache_exists:
    with open(transload_cache_file, 'rb') as f:
        (
            transload_gdf,
            transload_county_centroids,
            transload_county_names,
            transload_OD_flows_df,
            primary_RR_gdf,
            tertiary_RR_gdf,
            se_transload_flows_dict,
            intermodal_terminals_gdf,
            LTL_carriers_gdf,
            interstates_gdf
        ) = pickle.load(f)
else:
    transload_gdf = read_county_shapes(transload_read_query)
    transload_gdf = transload_gdf[~transload_gdf['geoid'].isin(list(SE_county_centroids.keys()))]
    transload_county_centroids = {row.geoid: row.geom.centroid.coords[0] for row in transload_gdf.itertuples()}
    transload_county_names = {row.geoid: f"{row.name}, {row.state_name}" for row in transload_gdf[['geoid', 'name', 'state_name']].drop_duplicates().sort_values(by='state_name').itertuples()}
    transload_gdf['geom'] = transload_gdf['geom'].simplify(0.05, preserve_topology=True)
    transload_gdf, transload_OD_flows_df,  primary_RR_gdf, tertiary_RR_gdf, transload_county_centroids, se_transload_flows_dict, intermodal_terminals_gdf, LTL_carriers_gdf, interstates_gdf = read_transload_layers(transload_gdf)

    # Save to cache
    with open(transload_cache_file, 'wb') as f:
        pickle.dump(
            (
                transload_gdf,
                transload_county_centroids,
                transload_county_names,
                transload_OD_flows_df,
                primary_RR_gdf,
                tertiary_RR_gdf,
                se_transload_flows_dict,
                intermodal_terminals_gdf,
                LTL_carriers_gdf,
                interstates_gdf
            ),
            f
        )
        
# ---------------------------------
# SE Regions
# ---------------------------------
se_regions_cache_file = './assets/Data/se_regions_transload_flow_cache.pkl'
se_regions_cache_exists = os.path.exists(se_regions_cache_file)
if se_regions_cache_exists:
    with open(se_regions_cache_file, 'rb') as f:
        se_regions = pickle.load(f)
else:
    se_regions = gpd.read_file('./assets/Data/Geojson/weighted_kmeans_50.geojson')
    se_regions['Transload_Flow'] = se_regions['cluster'].map(se_transload_flows_dict)
    
    # Save to cache
    with open(se_regions_cache_file, 'wb') as f:
        pickle.dump(se_regions, f)
