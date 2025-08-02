from dash_extensions.javascript import assign, arrow_function
import geopandas as gpd
import dash_mantine_components as dmc
from LivingLabUtility import *
from GWIntermodalFunctions import *
from dash_iconify import DashIconify
import dash_ag_grid as dag


# ******************************************
#   SOUTHEAST REGIONS
# ******************************************
region_hideout, RegionBarLayer = get_se_region_transload_colorbar(se_regions,'Transload_Flow', REGION_COLORSCALE)
region_style_handle = assign("""function(feature, context){
    const {classes, colorscale, style, colorProp} = context.hideout;  // get props from hideout
    const value = feature.properties[colorProp];  // get the value that determines the color
    
    if (value == 0) {
        style.fillColor = colorscale[0];  // Assign color for zero values
        return style;
    }

    for (let i = 0; i<classes.length - 1; ++i){
        if (value > classes[i] && value<= classes[i+1]){
            style.fillColor = colorscale[i];
            break;
        }
    }
    return style;
}""")

regions_tooltip = assign("""function(feature, layer, context){
        layer.bindTooltip(
            `<table>
                <tr><th>Region</th><td>${feature.properties.cluster}</td></tr>
                <tr><th>Flow (in thou. tons)</th><td>${feature.properties.Transload_Flow}</td></tr>
            </table>`,
            {permanent: false, direction: "center", className: "leaflet-tooltip-top"}
        );
    }""")

SE_Regions_Layer = dl.GeoJSON(data = se_regions.__geo_interface__, 
                                id="SE-regions", 
                                # zoomToBoundsOnClick=True,
                                onEachFeature=regions_tooltip,
                                style=region_style_handle,
                                hideout=region_hideout)


# ******************************************
#        SE COUNTIES STYLING
# ******************************************
style = dict(weight=0.3, opacity=0.5, color='black', fillOpacity=0)
se_county_style_handle = assign("""function(feature, context){
    const {style, colorProp} = context.hideout;  // get props from hideout
    const value = feature.properties[colorProp];  // get the value that determines the color
    
    if (value == 0) {
        style.fillColor = colorscale[0];  // Assign color for zero values
        return style;
    }

    for (let i = 0; i<classes.length - 1; ++i){
        if (value > classes[i] && value<= classes[i+1]){
            style.fillColor = colorscale[i];
            break;
        }
    }
    return style;
}""")

# regions_tooltip = assign("""function(feature, layer, context){
#         layer.bindTooltip(
#             `<table>
#                 <tr><th>Region</th><td>${feature.properties.cluster}</td></tr>
#                 <tr><th>Flow (in thou. tons)</th><td>${feature.properties.Transload_Flow}</td></tr>
#             </table>`,
#             {permanent: false, direction: "center", className: "leaflet-tooltip-top"}
#         );
#     }""")

SE_Counties_Layer = dl.GeoJSON(data = US_SE_counties.simplify(tolerance=0.01).__geo_interface__, 
                                id="SE-counties", 
                                # onEachFeature=regions_tooltip,
                                style=style)


# ******************************************
#   SELECTED REGION / COUNTY
# ******************************************
SelectedShapeLayer = dl.GeoJSON(id="selected_shapes", 
                                style = dict(weight=1, opacity=1, color='black', fillOpacity=1, fillColor = 'teal')
                                # zoomToBoundsOnClick=True,
                                # onEachFeature=regions_tooltip,
                                # style=region_style_handle,
                                # hideout=region_hideout
                                )
# ******************************************
#   TRANSLOAD COUNTIES
# ******************************************    
transload_county_style_handle = assign("""function(feature, context){
    const {classes, colorscale, style, colorProp} = context.hideout;  // get props from hideout
    const value = feature.properties[colorProp];  // get the value that determines the color
    
    if (value == 0) {
        style.fillColor = colorscale[0];  // Assign color for zero values
        style.fillOpacity = 0.8;
        return style;
    }

    for (let i = 0; i<classes.length - 1; ++i){
        if (value > classes[i] && value<= classes[i+1]){
            style.fillColor = colorscale[i];
            style.fillOpacity = 0.8;
            break;
        }
    }
    return style;
}""")

# transload_hideout, SouthGAColorBarLayer = get_transload_hideout(transload_gdf, 'SE_Inbound_Flow')
transload_hover_info = html.Div(
    children=get_transload_hover_info(),
    id="intermodal_hover_info",
    className="info",
    style={
        "position": "absolute",
        "bottom": "2vh",
        "left": "2vw",
        "zIndex": "1005",
        "backgroundColor": "#f8f9fa",  # Off-white color
        "padding": "10px",  # Add padding for better spacing
        "borderRadius": "8px",  # Add rounded corners for aesthetics
        "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",  # Subtle shadow for depth
        "border": "1px solid black",  # Black border
    }
)
onEachTransloadCounty = assign("""function(feature, layer, context){
    // Create a table for the selected properties
    let table = '<table style="width:100%">';
    table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">DESTINATION COUNTY INFO</th></tr>'; // Add a title row
    table += `<tr><td><strong>Name</strong></td><td>${feature.properties.name}</td></tr>`;
    table += `<tr><td><strong>State</strong></td><td>${feature.properties.state_name}</td></tr>`;
    table += `<tr><td><strong>Tons</strong></td><td>${feature.properties.Filtered_flow} (in thousand tons)</td></tr>`;
    table += '</table>';
    
    // Bind the tooltip with the table
    layer.bindTooltip(table, {permanent: false, direction: "center", className: "leaflet-tooltip-top"});
    }""")

TransloadCountyLayer = dl.GeoJSON(
    # data= transload_gdf.__geo_interface__,
    style=transload_county_style_handle,
    id="transload-county-geojson",
    onEachFeature=onEachTransloadCounty,
    # hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
    # hideout = transload_hideout
)


# ******************************************
#        TRANSLOAD TERMINAL STYLING
# ******************************************
terminal_point_to_layer = assign("""function(feature, latlng, context){
    const {colorProp, colorMap, circleOptions} = context.hideout;
    const icon = L.divIcon({
        className: 'custom-icon',
        html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                   <polygon points="12,4 4,20 20,20" 
                            style="fill:${feature.properties[colorProp]};stroke:black;stroke-width:0.5" />
               </svg>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    return L.marker(latlng, { icon: icon });
}""")

onEachTransloadTerminal = assign("""function(feature, layer, context) {
    // Specify the properties you want to display
    let selectedProperties = ['Location', 'ServiceRR']; // Replace with your column names
    
    // Create a table for the selected properties
    let table = '<table style="width:100%">';
    table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">TRANSLOAD TERMINAL INFO</th></tr>'; // Add a title row
    selectedProperties.forEach(function(property) {
        if (feature.properties[property]) {
        table += `<tr><td><strong><i>${property}</i></strong></td><td> ${feature.properties[property]}</td></tr>`;
        }
    });
    table += '</table>';
    
    // Bind the tooltip with the table
    layer.bindTooltip(table, {permanent: false, direction: "center", className: "leaflet-tooltip-top"});
    }""")

transload_hideout=dict(colorProp='color', colorMap=railColorMap, circleOptions=dict(fillOpacity=1, radius=5, weight = 0.7, color = 'navy'))

TransloadTerminalLayer = dl.GeoJSON(
    data= intermodal_terminals_gdf.__geo_interface__,
    id="im-terminal-geojson",
    pointToLayer=terminal_point_to_layer,  # how to draw points
    onEachFeature=onEachTransloadTerminal,
    zoomToBoundsOnClick=False,
    hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
    hideout = transload_hideout 
)


# ******************************************
#        LTL CARRIERS STYLING
# ******************************************
ltl_hideout = dict(colorMap = LTLColorMap, colorProp = 'Company')
onEachLTL = assign("""function(feature, layer, context){
                                    layer.bindTooltip(`${feature.properties.Company}`
                                    ,{permanent: false, direction: "center", className: "leaflet-tooltip-top"});
                                }""")

point_to_layer_LTL = assign("""function(feature, latlng, context) {
    const {colorProp, colorMap} = context.hideout;
    const icon = L.divIcon({
        className: 'custom-icon',
        html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                   <rect x="4" y="4" width="8" height="8" 
                         style="fill:${colorMap[feature.properties[colorProp]]};stroke:black;stroke-width:0.5" />
               </svg>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    return L.marker(latlng, { icon: icon });
}
""")

LTLLayer = dl.GeoJSON(data=LTL_carriers_gdf.__geo_interface__,
                             pointToLayer= point_to_layer_LTL,
                             hideout=ltl_hideout,
                             id="gateway-hub-layer",
                             onEachFeature=onEachLTL
                           )

# ******************************************
#   CLASS 1 RAIL ROADS STYLING
# ******************************************
prim_rail_style = dict(weight=1.5)
prim_rail_hideout = dict(colorProp='RROWNER1', style=prim_rail_style, colorMap = railColorMap)

prim_rail_style_handle = assign("""function(feature, context){
            const {colorProp, style, colorMap} = context.hideout;
            value = feature.properties[colorProp];
            style.color = colorMap[value];
            return style;
        }""")

onEachClass1RR = assign("""function(feature, layer, context) {
    // Specify the properties you want to display
    let selectedProperties = ['RROWNER1', 'DIVISION', 'MILES']; // Replace with your column names
    
    // Create a table for the selected properties
    let table = '<table style="width:100%">';
    table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">CLASS 1 RAILROAD INFO</th></tr>'; // Add a title row
    selectedProperties.forEach(function(property) {
        if (feature.properties[property]) {
        table += `<tr><td><strong>${property}</strong></td><td> ${feature.properties[property]}</td></tr>`;
        }
    });
    table += '</table>';
    
    // Bind the tooltip with the table
    layer.bindTooltip(table, {permanent: false, direction: "center", className: "leaflet-tooltip-top"});
    }""")

PrimaryRailLayer = dl.GeoJSON(
    data=primary_RR_gdf.__geo_interface__,
    style=prim_rail_style_handle,
    id="primary-rail-geojson",
    onEachFeature=onEachClass1RR,
    zoomToBoundsOnClick=False,
    hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray='')),  # style applied on hover
    hideout = prim_rail_hideout
)

# ******************************************
#   CLASS 3 RAIL ROADS STYLING
# ******************************************
ga_rail_style = dict(weight=1.5)
ga_rail_hideout = dict(colorProp='RROWNER1', style=ga_rail_style, colorMap = IMColorMap)
ga_rail_style_handle = assign("""function(feature, context){
            const {colorProp, style, colorMap} = context.hideout;
            value = feature.properties[colorProp];
            style.color = 'black' //colorMap[value];
            return style;
        }""")
onEachClass3RR = assign("""function(feature, layer, context) {
    // Specify the properties you want to display
    let selectedProperties = ['RROWNER1', 'DIVISION', 'MILES']; // Replace with your column names
    
    // Create a table for the selected properties
    let table = '<table style="width:100%">';
    table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">CLASS 3 RAILROAD INFO</th></tr>'; // Add a title row
    selectedProperties.forEach(function(property) {
        if (feature.properties[property]) {
        table += `<tr><td><strong>${property}</strong></td><td> ${feature.properties[property]}</td></tr>`;
        }
    });
    table += '</table>';
    
    // Bind the tooltip with the table
    layer.bindTooltip(table, {permanent: false, direction: "center", className: "leaflet-tooltip-top"});
    }""")

IntermodalRailLayer = dl.GeoJSON(
    data=tertiary_RR_gdf.simplify(tolerance=0.001).__geo_interface__,
    style=ga_rail_style_handle,
    id="tertiary-rail-geojson",
    onEachFeature=onEachClass3RR,
    zoomToBoundsOnClick=False,
    hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray='')),  # style applied on hover
    hideout = ga_rail_hideout
)

# ******************************************
#   TRANSLOAD FLOW LINES STYLING
# ******************************************
transload_flow_style = dict(color = FLOWLINES_COLORSCALE)
transload_flow_style_handle = assign("""function(feature, context){
            const {weightProp, opacityProp, style} = context.hideout;
            style.weight = feature.properties[weightProp];
            style.opacity = feature.properties[opacityProp] || 0.8; 
            return style;
        }""")
# let origin = feature.properties.orig_cnty_name ? feature.properties.orig_cnty_name : `Region ${feature.properties.orig_reg}`;

onEachFlowLine = assign("""function(feature, layer, context){
    let origin = feature.properties.orig_cnty_name ? feature.properties.orig_cnty_name : `Region ${feature.properties.orig_reg}`;
    let table = '<table style="width:100%">';
    table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">FLOW LINE INFO</th></tr>'; // Add a title row
    table += `<tr><td><strong>Origin</strong></td><td>${origin}</td></tr>`;
    table += `<tr><td><strong>Destination</strong></td><td> ${feature.properties.dest_cnty_name} </td></tr>`;
    table += `<tr><td><strong>Tons</strong></td><td><b>${feature.properties.tons}</b></td></tr>`;
    table += '</table>';
    
    layer.bindTooltip(table, {
        permanent: false, 
        direction: "center", 
        className: "leaflet-tooltip-top"
    });
    }""")

TransloadFlowLayer = dl.GeoJSON(
    id="Flow-geojson-Transload",
    style=transload_flow_style_handle,
    onEachFeature=onEachFlowLine,
    hideout=dict(weightProp='weight', opacityProp='opacity', style=transload_flow_style)
)

# ******************************************
#   INTERMODAL LEGEND TABLE STYLING
# ******************************************
def create_box_legend(color, label):
    return dmc.Group(
        [
            DashIconify(
                icon="mdi:horizontal-line",  # outline with border
                width=48,
                height=48,
                style = {'stroke-width': '0.1', 'stroke': 'black'},
                color=color
            ),
            dmc.Text(label, size="xs"),
        ],
        gap=0.5,
        align="center",
    )

def create_triangle_legend(color, label):
    return dmc.Group(
        [
            DashIconify(
                icon="ion:triangle-sharp",  # outline with border
                width=18,
                style = {'stroke-width': '15', 'stroke': 'black'},
                color=color
            ),
            dmc.Text(label, size="xs"),
        ],
        gap="xs",
        align="center"
    )

TransloadLegendTable = dmc.Box(
    dmc.Group(
        [
            # Class 1 Railroads
            *[
                create_box_legend(railColorMap[term], term)
                for term in railColorMap
            ],
            
            # Class 3 Railroad
            create_box_legend("black", "Class 3 - RR"),
            # G&W Terminals using triangle icons
            *[
                create_triangle_legend(GWColorMap[term], f"{term} G&W")
                for term in GWColorMap
            ],
        ],
        gap="xl",
        pos="right",
        style={"justifyContent": "center", "flexWrap": "wrap", "maxWidth": "100%"},
    ),
    p=0,
    id="intermodal_legend_table",
    style={
        "zIndex": 1000,
        "backgroundColor": "#f5f5f5",
        "border": "1px solid black"
    }
)

