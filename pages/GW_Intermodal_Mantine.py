import warnings
warnings.filterwarnings("ignore")


import dash
from dash import dcc, html, callback, clientside_callback
from dash.dependencies import Input, Output, State
from threading import Timer
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
import numpy as np
import dash_leaflet as dl
import geojson
from dash_extensions.javascript import assign, arrow_function
import dash_leaflet.express as dlx
import json
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
import numpy as np
import plotly.colors as pc
import time
from LivingLabUtility import *
from SQLQueries import *
from GWIntermodalLayers import *
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from keplergl import KeplerGl

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoicHJhdmVlbm0wNyIsImEiOiJjbHVseWhvY3IxN2VtMmtvMWF4MmdheGFtIn0.l_gHE7oX7G5CRxbNkOaZ1g"

dataset = {
    "points": {
        "data": [
            {"lat": 33.75, "lng": -84.39, "name": "ATL"},
            {"lat": 34.05, "lng": -84.24, "name": "GA"}
        ],
        "info": {"label": "points"}
    }
}

kepler_config = {
    "version": "v1",
    "config": {
        "visState": {
            "filters": [],
            "layers": [
                {
                    "id": "point_layer",
                    "type": "point",
                    "config": {
                        "dataId": "points",   # must match dataset["info"]["label"]
                        "label": "Points",
                        "color": [255, 0, 0],
                        "columns": {
                            "lat": "lat",
                            "lng": "lng",
                            "altitude": None
                        },
                        "isVisible": True,
                        "visConfig": {
                            "radius": 10,
                            "opacity": 0.8,
                            "strokeOpacity": 0.8,
                            "strokeColor": [0, 0, 0],
                            "thickness": 2,
                            "filled": True
                        }
                    },
                    "visualChannels": {
                        "colorField": None,
                        "colorScale": "quantile",
                        "sizeField": None,
                        "sizeScale": "linear"
                    }
                }
            ],
            "interactionConfig": {
                "tooltip": {
                    "fieldsToShow": {
                        "points": ["name", "lat", "lng"]  # which fields show on hover
                    },
                    "enabled": True
                }
            },
            "layerBlending": "normal"
        },
        "mapState": {
            "bearing": 0,
            "dragRotate": False,
            "latitude": 33.9,
            "longitude": -84.4,
            "pitch": 0,
            "zoom": 7
        },
        "mapStyle": {
            "styleType": "dark"
        }
    }
}


dash.register_page(__name__, path = '/', title="Intermodal Flow", name='Intermodal Flow')

# ******************************************
#        Dropdowns, Sliders & Input
# ******************************************
# Region Dropdown
REGION_CLUSTER_MENU = [{"label": f"All", "value": -1}] + [{"label": f"Region {region}", "value": region} for region in se_regions['cluster'].drop_duplicates().tolist()]
REGION_MENU_MANTINE = [{"label": "All", "value": "-1"}] + [{"label": f"Region {region}", "value": f"{region}"} for region in se_regions['cluster'].drop_duplicates().tolist()]
region_dropdown = create_mantine_dropdown(title="Select Region",
                                          comp_id="slct-region-cluster",
                                          menu_options=REGION_MENU_MANTINE,
                                          initial_val='-1',
                                          multi=True
                                          )

# SE Counties Dropdown
SE_COUNTIES_MENU_MANTINE = [{"group": "All Regions", "items": [{"label": "All", "value": "-1"}]}] + [{
    "group": f"Region {region}",
    "items": [
        {"label": SE_county_names[geoid], "value": f'{geoid}'}
        for geoid in region_county_mapping[region]
    ]
}
    for region in region_county_mapping.keys()
]

initial_se_county = [str(geoid) for geoid in gnw_se_counties_df['geoid'].tolist()] 

se_county_dropdown = create_mantine_dropdown(title="Select Origin County",
                                             comp_id="slct-se-cnty",
                                             menu_options = SE_COUNTIES_MENU_MANTINE,
                                             initial_val=initial_se_county,
                                             multi=True,
                                             persistence = False
                                             )

# DESTINATION COUNTIES
DEST_COUNTIES_MENU_MANTINE = [{"label": "All", "value": "-1"}] + [{"label": name, "value": f"{geoid}"} for geoid, name in transload_county_names.items()]
transload_county_dropdown = create_mantine_dropdown(title="Select Target County",
                                             comp_id="slct-transload-cnty",
                                             menu_options=DEST_COUNTIES_MENU_MANTINE,
                                             initial_val=DEST_COUNTIES_MENU_MANTINE[0]['value'],
                                             multi=True, 
                                             persistence = False
                                             )

Truck_capacity_slider = create_mantine_slider(title ='Truck Fill Rate (%)', 
                                              comp_id = 'ltl-capacity-slider',
                                              min_val = 50, max_val = 100, steps = 5, val = 50, label_on = False,
                                              persistence = False
                                              )

Boxcar_capacity_input = dmc.Paper([
    dmc.NumberInput(
        id='boxcar-pallet-input',
        label=dmc.Text('Pallets per Box Car', fw=500, w='100%', size='xs'),
        placeholder='Input #Boxcar Pallets',
        min=1,
        value=BOX_CAR_PALLETS,
        step=1,
        size="xs",
        variant='filled',
        persistence=True,
        style={'width': '90%', 'textAlign': 'center'},
        clampBehavior="strict",  # Prevents going below min
    )
], p='md', shadow='md', radius='md', withBorder=True)

LTL_percent_input = dmc.Paper([
    dmc.NumberInput(
        id='ltl-percent-input',
         label=dmc.Text('LTL%', fw=500, w='100%', size='xs'),
        placeholder='Input LTL %',
    min=1,
    value=10,
    variant='filled',
    step=1,
    size="xs",
    persistence=True,
    style={'width': '90%', 'textAlign': 'center'},
    clampBehavior="strict",  # Prevents going below min
)
], p='md', shadow='md', radius='md', withBorder=True)

# ******************************************
#   HEATMAP GRAPH
# ******************************************
heatmap_graph = dmc.Paper([
    dmc.Stack(
        [
            dmc.Title("Origin-Destination Heatmap", order=3, size = 'h4', ta="center", c="black"),
            dcc.Graph(
                id='heatmap_graph',
                style={'height': '70vh', 'width': '100%'}
            )
        ],
        gap=0
    )
], shadow='md', radius='md', p='md', withBorder=True)

# ******************************************
# COMMODITY PIE CHART 
# ******************************************
pie_chart_container = dmc.Container(children=[], id="commodity_flow_container", fluid=True)

# ******************************************
# TOP COUNTIES BAR GRAPHS
# ******************************************


im_top_origin_bar_graph = dmc.Paper([
    dcc.Graph(figure={}, id='transmodal_origin_bar_graph', style={'height': '32vh'})
], shadow='md', radius='md', p='md', withBorder=True)

im_top_dest_bar_graph = dmc.Paper([
    dcc.Graph(figure={}, id='transmodal_dest_bar_graph', style={'height': '32vh'})
], shadow='md', radius='md', p='md', withBorder=True)
# im_top_dest_bar_graph = dmc.Container(children=[], id="transmodal_dest_bar_graph_container", fluid=True)

# ************************************************************************************
#   MAP WITH ALL LAYERS
# ************************************************************************************

SE_Regions_Layer.pane = "regions"
TransloadCountyLayer.pane = "transload-counties" 
SE_Counties_Layer.pane = "SE-counties"
SelectedShapeLayer.pane = "selected"
TransloadFlowLayer.pane = "flows"
PrimaryRailLayer.pane = "primary-rail"
IntermodalRailLayer.pane = "intermodal-rail"
InterstateLayer.pane = "interstates"    
TransloadTerminalLayer.pane = "terminals"
LTLLayer.pane = "ltl"
RegionBarLayer.pane = "bars"
GatewayHubLayer.pane = "gateway-hub"
RegionalHubLayer.pane = "regional-hub"  

transload_county_flows_map = dl.Map(
    center=[33.4574, -82.9071],
    zoom=5,
    style={
        "width": "100%",
        "height": "65vh", 
        'backgroundColor': 'transparent',
        'border': '0.5px solid black', 
        'boxShadow': '0 4px 8px rgba(0,0,0,0.4)'
    },
    children=[
        # Define panes with z-index
        dl.Pane(name="regions", style={"zIndex": 200}),
        dl.Pane(name="transload-counties", style={"zIndex": 300}),
        dl.Pane(name="SE-counties", style={"zIndex": 400}),
        dl.Pane(name="selected", style={"zIndex": 425}),
        dl.Pane(name="flows", style={"zIndex": 450}),
        dl.Pane(name="primary-rail", style={"zIndex": 500}),
        dl.Pane(name="intermodal-rail", style={"zIndex": 550}),
        dl.Pane(name="interstates", style = {"zIndex":600}),
        dl.Pane(name="terminals", style={"zIndex": 800}),
        dl.Pane(name="ltl", style={"zIndex": 900}),
        dl.Pane(name="gateway-hub", style={"zIndex": 950}),
        dl.Pane(name="regional-hub", style={"zIndex": 1001}),

        # dl.FeatureGroup(
        #     [
        #         dl.EditControl(
        #             id="edit-control",
        #             draw={"polygon": True, "rectangle": True, "circle": False, "marker": False},
        #             edit={"edit": True},
        #             position="topleft",
        #         )
        #     ],
        #     id="edit-layer",
        #     pane="selected"
        # ),

        dl.LayersControl(
            children=[
                dl.BaseLayer(dl.TileLayer(), name="Tile Layer", checked=True),
                dl.Overlay(SE_Regions_Layer, id="Regions-layer", name="Regions", checked=True),
                dl.Overlay(SE_Counties_Layer, id="SE-Counties-layer", name="Southeast Counties", checked=False),
                dl.Overlay(TransloadCountyLayer, id="County-layer", name="Destination Counties", checked=True),
                dl.Overlay(SelectedShapeLayer, id="Selected-Shape-layer", name="Selected Region/County", checked=True),
                dl.Overlay(LTLLayer, id="LTL-layer", name="LTL", checked=False),
                dl.Overlay(PrimaryRailLayer, id="Primary-Rail-layer", name="Class 1 - RR", checked=True),
                dl.Overlay(IntermodalRailLayer, id="Tertiary-Rail-layer", name="Class 3 - RR", checked=True),
                dl.Overlay(InterstateLayer, id="Interstate-layer", name="Interstates", checked=True),
                dl.Overlay(TransloadFlowLayer, id="Flows-layer", name="O-D Flows", checked=True),
                dl.Overlay(TransloadTerminalLayer, id="Terminal-layer", name="G&W Transload Stations", checked=False),
                dl.Overlay(RegionalHubLayer, id="Region-Hub-layer", name="Regional Hubs", checked=True),
                dl.Overlay(GatewayHubLayer, id="Gateway-Hub-layer", name="Gateway Hubs", checked=False),
                dl.Overlay(RegionBarLayer, id="Region-Bar-layer", name="Region Flows Colorbar", checked=True)
            ],
            position="topright"
        ),
    ],
    id='intermodal_county_flows_map'
)

# ******************************************
#   MAIN FLOW SUMMARY CARD
# ******************************************
cardBody = dmc.Card([
    dmc.CardSection([
        dmc.Text(
            children=get_transload_card_info(transload_OD_flows_df),
            id='intermodal_card_info',
            size="xs",
            ta="center"
        )
    ],
    withBorder=True,
    inheritPadding=True,
    p='sm'
    )
], 
withBorder=True,
shadow="sm",
style={"backgroundColor": "#f5f5f5", "margin": "0.5vw"}
)

# ******************************************
#   FILTERED FLOW TABLE CARD
# ******************************************
ContainerInfoCardBody = dmc.Card([
    dmc.CardSection([
        dmc.Text(
            id='load_card_info',
            size="xs",
            ta="center"
        )
    ])
], 
withBorder=True,
shadow="sm",
style={"backgroundColor": "#f5f5f5"}
)

# *************************************************************************************
#    LAYOUT
# *************************************************************************************
TitleHeader = dmc.Title(
    "Potential Intermodal Freight Flows: Southeast to Midwest Counties",
    id='im_title',
    order=1,
    ta="center",
    size="h2",
    c="darkslategray",
    mb='xs'
)
SummaryButton = dmc.Button(
    "Summary",
    id='flow-modal-button',
    leftSection=DashIconify(icon="mdi:chart-line"),
    gradient={"from": "blue", "to": "cyan", "deg": 90},
    variant="gradient"
)


ModalContent = dmc.Modal(
    # title="Flow Summary",
    id='flow-modal',
    children=[cardBody],
    zIndex=2000,
    centered=True
)

TitleRow = dmc.Grid([
    dmc.GridCol(TitleHeader, span=10),
    dmc.GridCol(SummaryButton, span=2, style={"textAlign": "right"}),
    ModalContent
    
], align="center", mb="xs")

OptionsRows = dmc.Grid([
        dmc.GridCol(region_dropdown, span=2),
        dmc.GridCol(se_county_dropdown, span=3),
        dmc.GridCol(transload_county_dropdown, span=3),
        dmc.GridCol(Truck_capacity_slider, span=1.5),
        dmc.GridCol(Boxcar_capacity_input, span=1.5),
        dmc.GridCol(LTL_percent_input, span=1),
    ], mb="xs")

MapLegendColumn = dmc.GridCol(
    [
        dmc.Stack(
            [ TransloadLegendTable,
              dmc.Box([transload_county_flows_map])
               
            ],
            gap='xs',
            justify='flex-start',
            style={"height": "73vh"},
        )
    ],
    span=8,
)

GraphsColumn = dmc.GridCol([
            dmc.Stack([
                # cardBody,
                dmc.Grid([dmc.GridCol(ContainerInfoCardBody, span="auto"), 
                          dmc.GridCol(pie_chart_container, span="auto")
                        ]
                )
            ]),
        ], span=4)

HeatMapColumn = dmc.GridCol(heatmap_graph, span=6, mt='sm')
FlowGridColumn = dmc.GridCol([
        dmc.Button("Download CSV", id='flow-export-csv-btn', size="xs",  variant="gradient",
                    gradient={"from": "green", "to": "darkgreen"}, mb = "xs", ml='auto'),
        dmc.Box(id='flow-grid-column', style={'height': '70vh', 'width': '100%'}, flex=True)
], span=6, id='flow-grid-column', h='70vh', mt='sm')

# KeplerGraphContainer = dmc.Container(
#     id="kepler-graph-container",
#     fluid=True,
#     children=[
#         dmc.Paper(  # gives a block with explicit height
#             withBorder=True, p="xs",
#             style={"height": "82vh"}, 
#             children=KeplerGl(
#                 id="kepler-map",
#                 config = kepler_config,
#                 height=500, width="100%",
#                 mapboxApiAccessToken=MAPBOX_ACCESS_TOKEN
#             )
#         )
#     ]
# )

layout = dmc.Box([
    dcc.Store(id='shared-data-store', data={}),
    TitleRow,
    OptionsRows,
    dmc.Grid([ MapLegendColumn, GraphsColumn], gutter = 'sm'),
    dmc.Grid([dmc.GridCol(im_top_origin_bar_graph, span=6), dmc.GridCol(im_top_dest_bar_graph, span=6)]),
    dmc.Grid([HeatMapColumn, FlowGridColumn])
    # KeplerGraphContainer
    ]
)

# ************************************************************************************
#   CALLBACKS
# ************************************************************************************
# -----------------------------------------
#   Modal Callback
# -----------------------------------------
@callback(
    Output("flow-modal", "opened"),
    Input("flow-modal-button", "n_clicks"),
    State("flow-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_modal(n_clicks, opened):
    return not opened

# -----------------------------------------
#   Update County Dropdown Callback
# -----------------------------------------
@callback(
    Output("slct-se-cnty", "data"),
    Output("slct-se-cnty", "value"),
    Input("slct-region-cluster", "value"),
    prevent_initial_call=True
)
def update_county_dropdown(selected_region):
    # if selected_region is None or selected_region == [] or selected_region == ['-1']:
    #     return SE_COUNTIES_MENU_MANTINE, ['-1']

    # selected_region_list = [int(r) for r in selected_region if r != '-1']
    
    # if not selected_region_list:
    #     return SE_COUNTIES_MENU_MANTINE, ['-1']
    
    # county_options = [{"label": "All", "value": "-1"}] + [
    #     {
    #         "group": f"Region {region}",
    #         "items": [  # Changed from "options" to "items"
    #             {"label": SE_county_names[county_id], "value": f'{county_id}'}
    #             for county_id in region_county_mapping[region]
    #         ]
    #     }
    #     for region in selected_region_list
    # ]

    # return county_options, ['-1']
    
    if selected_region in (None, [], '-1'):
        return dash.no_update, dash.no_update
    else:
        region_list = [int(r) for r in selected_region if r != '-1']
        county_options = [{"label": "All", "value": "-1"}] + [
        {
            "group": f"Region {region}",
            "items": [  # Changed from "options" to "items"
                {"label": SE_county_names[county_id], "value": f'{county_id}'}
                for county_id in region_county_mapping[region]
            ]
        }
        for region in region_list
    ]

    return county_options, ['-1']

# -----------------------------------------
#   Update Dash Grid Callback
# -----------------------------------------
@callback(
    Output("flow-grid-column", "children"),
    Input("slct-region-cluster", "value"),
    Input("slct-se-cnty", "value"),
    Input("slct-transload-cnty", "value")
)
def update_flow_grid(selected_region, selected_county, selected_transload_county):
    flows_df = transload_OD_flows_df.copy()
    filtered_flows = filter_flows_optimized(flows_df, selected_region, selected_county, selected_transload_county)
    
    filtered_flows['orig_reg'] = 'Region ' + filtered_flows['orig_reg'].astype(str) 
    filtered_flows['tons'] = (filtered_flows['tons']*1000).astype(int)
    
    if filtered_flows.empty:
        return []

    row_data = filtered_flows.to_dict('records')
    flow_grid = get_flow_grid(row_data)

    return flow_grid


# -----------------------------------------
#   Update Dash Grid Callback
# -----------------------------------------
@callback(
    Output("flows-grid", "exportDataAsCsv"),
    Input("flow-export-csv-btn", "n_clicks"),
    prevent_initial_call=True
)
def export_data_as_csv(n_clicks):
    if ctx.triggered_id == 'flow-export-csv-btn':
        return True
    return dash.no_update

# -----------------------------------------
#   Update Load Card Info Callback
# -----------------------------------------
@callback(
    Output("load_card_info", "children"),
    Input("slct-region-cluster", "value"),
    Input("slct-se-cnty", "value"),
    Input("slct-transload-cnty", "value"),
    Input("ltl-capacity-slider", "value"),
    Input("boxcar-pallet-input", "value"),
    Input("ltl-percent-input", "value")
)
def update_load_card_info(selected_region, selected_county, selected_transload_county, slider_val, boxcar_pallets, ltl_percent):
    flows_df = transload_OD_flows_df.copy()
    filtered_flows = filter_flows_optimized(flows_df, selected_region, selected_county, selected_transload_county)
    metric_card_info = get_metric_card_info(filtered_flows, selected_region, selected_county, selected_transload_county, slider_val, boxcar_pallets, ltl_percent)
    return metric_card_info

# -----------------------------------------
#   Update Heatmaps and Bar Charts Callback
# -----------------------------------------
@callback(
    Output("heatmap_graph", "figure"),
    Output("transmodal_origin_bar_graph", "figure"),
    Output("transmodal_dest_bar_graph", "figure"),
    Input("slct-region-cluster", "value")
)
def update_heatmap_and_barcharts(selected_region):
    flows_df = transload_OD_flows_df.copy()
    filtered_flows = filter_flows_region(flows_df, selected_region)
    
    top10_orig_container = get_transload_top_few_counties_bar_graph(filtered_flows, selected_region, 'orig_cnty_name', REGION_COLORSCALE,10)
    
    top10_dest_container = get_transload_top_few_counties_bar_graph(filtered_flows, selected_region, 'dest_cnty_name', TRANSLOAD_COLORSCALE, 10)
    
    heatmap_fig = generate_heatmap_graph(filtered_flows, selected_region)
    
    return heatmap_fig, top10_orig_container, top10_dest_container

# -----------------------------------------------------
#   Update Transload County Callback
# -----------------------------------------------------
@callback(
    Output('transload-county-geojson', 'data'),
    Output('transload-county-geojson', 'hideout'),
    Input('slct-region-cluster', 'value'),
    Input('slct-se-cnty', 'value'),
    Input('slct-transload-cnty', 'value')
)
def update_transload_county_geojson(selected_region, selected_county, selected_transload_county):
    transload_agg_flows_df = transload_gdf.copy()
    flows_df = transload_OD_flows_df.copy()
    filtered_flows = filter_flows_optimized(flows_df, selected_region, selected_county, selected_transload_county)
    if filtered_flows.empty:
        return {}, {}
    
    transload_data = get_transload_data(filtered_flows, transload_agg_flows_df, selected_region, selected_county, selected_transload_county)
    transload_geojson = transload_data.__geo_interface__
    transload_hideout = get_transload_hideout(transload_data, 'Filtered_flow')
    
    return transload_geojson, transload_hideout

# -----------------------------------------------------
#   Update Selected Shapes Callback
# -----------------------------------------------------
@callback(
    Output("selected_shapes", "data"),
    Input('slct-region-cluster', 'value'),
    Input('slct-se-cnty', 'value')
)
def update_selected_shapes(selected_region, selected_county):
    sel_shapes_info = get_selected_shapes_info(se_regions, US_SE_counties, selected_region, selected_county)
    sel_shapes_info = sel_shapes_info.__geo_interface__
    return sel_shapes_info

# -----------------------------------------------------
#   Update Flow Lines Callback
# -----------------------------------------------------
@callback(
    Output("Flow-geojson-Transload", "data"),
    Input('slct-region-cluster', 'value'),
    Input('slct-se-cnty', 'value'),
    Input("slct-transload-cnty", "value")
)
def update_flow_lines(selected_region, selected_county, selected_transload_county):
    flows_df = transload_OD_flows_df.copy()
    filtered_flows = filter_flows_optimized(flows_df, selected_region, selected_county, selected_transload_county)
    filtered_flow_lines_gdf = get_weighted_flow_lines(filtered_flows, selected_region, selected_county, selected_transload_county, transload_county_centroids, region_cluster_centroids, SE_county_centroids)
    flow_lines_geojson = filtered_flow_lines_gdf.__geo_interface__
    
    return flow_lines_geojson

# -----------------------------
#   Update Pie Chart Callback
# -----------------------------
@callback(
          Output("commodity_flow_container", "children"),
          Input("slct-region-cluster", "value"),
          Input("slct-se-cnty", "value"),
          Input("slct-transload-cnty", "value")
        )
def update_pie_chart(selected_region, selected_county, selected_transload_county):
    OD_flows_df = transload_OD_flows_df.copy()
    filtered_flows = filter_flows_with_commodity_optimized(OD_flows_df, selected_region, selected_county, selected_transload_county)
    commodity_pie_fig = get_transload_pie_commodity_mantine(filtered_flows, selected_region, selected_county, selected_transload_county)
    return commodity_pie_fig
