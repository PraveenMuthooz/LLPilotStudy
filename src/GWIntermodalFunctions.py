from LivingLabUtility import * 
import dash_ag_grid as dag

# ******************************************
#   SOUTHEAST REGIONS
# ******************************************
def get_se_region_transload_colorbar(se_region_gdf, color_prop = 'Transload_FLow', region_color_scale = 'reds'):
    ############################### COUNTY-FLOW STYLING ########################################
    num_classes = 5
    min_value = se_region_gdf[color_prop].min()
    max_value = np.floor(se_region_gdf[color_prop].max())
    classes = np.geomspace(min_value, max_value, num=num_classes).astype(int).tolist() + [int(np.ceil(max_value))]
    mil_classes = classes
    
    # mil_classes = []
    # if classes[1] == 0:
    #     classes[1] = 1
    # for i in classes: 
    #     if i/1000 < 1:
    #         mil_classes.append(np.round(i/1000,3))
    #     else:
    #         mil_classes.append(np.round(i/1000,1))
    
    colorscale = pc.sample_colorscale(region_color_scale, np.linspace(0, 1, num_classes))
    ctg = [f"<{mil_classes[i + 1]}" for i in range(len(mil_classes) - 2)] + [f"{mil_classes[-1]}"]
    
    colorbar_width, colorbar_height, padding_length = 250, 10, 10
    
    colorbar = dlx.categorical_colorbar(
        categories=ctg, colorscale=colorscale, width=colorbar_width, height=colorbar_height, position="bottomleft",
        style={ "zIndex": "1505", "flexDirection": "row",  "backgroundColor": f"{colorbar_bg_color}", 
               "padding": f"{padding_length}px"}
    )
    
    FlowBarLayer = dmc.Container(
                    [
                        dmc.Title("Outbound Flows (in thousand tons)", id='colorbar_title', size="h7", ta="center", w = "100%"),
                        dmc.Container(colorbar, id='region_colorbar')
                    ],
                    style={
                        "position": "absolute",
                        "bottom": f"{20 + colorbar_height + 3 * padding_length}px",
                        "left": f"{padding_length}px",
                        "width": f"{colorbar_width + 2 * padding_length}px",
                        "zIndex": 1500,
                        "backgroundColor": f"{colorbar_bg_color}",
                        "paddingTop": "5px"
                    }
            )

    style = dict(weight=0.6, opacity=0.7, color='black', dashArray='1', fillOpacity=0.7)
    region_hideout = dict(colorscale=colorscale, classes=classes, style=style, colorProp=color_prop)

    return region_hideout, FlowBarLayer


# ******************************************
#   SELECTED REGION / COUNTY
# ******************************************
def get_selected_shapes_info(se_region_gdf, SE_counties, selected_region, selected_county):
    """ 
    Function to get the selected shapes based on the selected region and county.
    Arguments:
    - se_region_gdf: GeoDataFrame containing the regions
    - SE_counties: GeoDataFrame containing the counties
    - selected_region: List of selected region IDs
    - selected_county: List of selected county IDs
    Returns:
    - GeoDataFrame containing the selected shapes based on the provided region and county filters
    """
    if selected_county and selected_county != ['-1']:
        selected_county_list = [int(c) for c in selected_county if c != '-1']
        sel_shape_gdf = SE_counties[SE_counties['geoid'].isin(selected_county_list)].copy()
        return sel_shape_gdf

    if selected_region != ['-1'] or selected_region is not None or selected_region != []:
        selected_region_list = [int(r) for r in selected_region if r != '-1']
        sel_shape_gdf = se_region_gdf[se_region_gdf['cluster'].isin(selected_region_list)].copy()
        return sel_shape_gdf
    
    return None

# ******************************************
#   TRANSLOAD COUNTIES
# ******************************************    
def get_transload_data(OD_flows, transload_agg_flows_df, selected_region, selected_county, selected_transload_county):
    """ 
    Function to get transload data based on selected filters
    Arguments:
    - OD_flows: DataFrame containing origin-destination flows
    - transload_agg_flows_df: DataFrame containing transload aggregated flows
    - selected_region: List of selected region IDs
    - selected_county: List of selected county IDs
    - selected_transload_county: List of selected transload county IDs
    Returns:
    - DataFrame containing transload data filtered based on the provided region and county selections
    """
    transload_table = transload_agg_flows_df.copy()
    OD_flows = OD_flows.groupby(['dest_cnty'], as_index=False)['tons'].sum()
    dest_cnty_flow_dict = dict(zip(OD_flows['dest_cnty'], OD_flows['tons']))
    transload_table['Filtered_flow'] = transload_table['geoid'].map(dest_cnty_flow_dict).fillna(0).round(1)
    
    return transload_table

    
def get_transload_hideout(transload_table, color_prop):
    num_classes = 5
    if len(transload_table) < 5:
        num_classes = len(transload_table)
    
    max_value = np.floor(transload_table[color_prop].max())
    if max_value == 0:
        classes = [0]
    else:
        min_value = transload_table[color_prop].min() if transload_table[color_prop].min() != 0 else 1
        classes = np.geomspace(min_value, max_value, num=num_classes).astype(int).tolist() + [int(np.ceil(transload_table[color_prop].max()))]
    mil_classes = classes
    
    colorbar_width, colorbar_height, padding_length = 250, 10, 10
    
    # mil_classes = []
    # if classes[1] == 0:
    #     classes[1] = 1
    # for i in classes: 
    #     if i/1000 < 1:
    #         mil_classes.append(np.round(i/1000,3))
    #     else:
    #         mil_classes.append(np.round(i/1000,1))
    
    colorscale = pc.sample_colorscale(TRANSLOAD_COLORSCALE, np.linspace(0, 1, num_classes))
    ctg = [f"<{mil_classes[i + 1]}" for i in range(len(mil_classes) - 2)] + [f"{mil_classes[-1]}"]
    # colorbar = dlx.categorical_colorbar(
    #     categories=ctg, colorscale=colorscale, width=colorbar_width, height=colorbar_height, position="bottomright",
    #     style={"transform": "translate(-1vw 1vh)", "zIndex": "1500", "flexDirection": "row",
    #             "backgroundColor":  f"{colorbar_bg_color}", "padding": f"{padding_length}px"
    #            }
    # )
    style = dict(weight=0.6, opacity=0.7, color='black', dashArray='2', fillOpacity=0.8)
    intermodal_hideout = dict(colorscale=colorscale, classes=classes, style=style, colorProp=color_prop)
    
    # FlowBarLayer = dmc.Container(
    #                 [
    #                     dmc.Title("Inbound Flows (in thou. tons)", size="h7", ta="center", w = "100%"),
    #                     dmc.Container(colorbar, id='transload_colorbar')
    #                 ],
    #                 style={
    #                     "position": "absolute",
    #                     "bottom": f"{20 + colorbar_height + 3 * padding_length}px",
    #                     "right": f"{padding_length}px",
    #                     "width": f"{colorbar_width + 2 * padding_length}px",
    #                     "zIndex": 1500,
    #                     "backgroundColor": f"{colorbar_bg_color}",
    #                     "paddingTop": "5px"
    #                 }
    #         )
    
    return intermodal_hideout

def get_transload_hover_info(feature=None):
    if not feature:
        header = [html.H5(f"County Flow", style={"textAlign": "center", "margin": "10px 0"})]
        return header + [html.P("Hover over a county")]
    else:
        header = [html.H5(f"{feature['properties']['name']} : {feature['properties']['state_name']}",
                          style={"textAlign": "center", "margin": "10px 0"})]
        inbound_value = feature["properties"][flowMap['Inbound']]
        outbound_value = feature["properties"][flowMap['Outbound']]
        within_value = feature["properties"][flowMap['Within']]
        total_value = feature["properties"]["total"]

        inbound_info = "{:.3f} (million tons)".format(inbound_value / 1000) if inbound_value / 1000 < 1 else "{:.1f} (million tons)".format(inbound_value / 1000)
        outbound_info = "{:.3f} (million tons)".format(outbound_value / 1000) if outbound_value / 1000 < 1 else "{:.1f} (million tons)".format(outbound_value / 1000)
        within_info = "{:.3f} (million tons)".format(within_value / 1000) if within_value / 1000 < 1 else "{:.1f} (million tons)".format(within_value / 1000)
        total_info = "{:.3f} (million tons)".format(total_value / 1000) if total_value / 1000 < 1 else "{:.1f} (million tons)".format(total_value / 1000)

        return header + ["Inbound: ", inbound_info,
                         html.Br(),
                         "Outbound: ", outbound_info,
                         html.Br(),
                         "Within: ", within_info,
                         html.Br(),
                         "Total: ", html.B(total_info)]

# ******************************************
#   TRANSLOAD FLOW LINES STYLING
# ******************************************
def get_weighted_flow_lines(filtered_flows_df, selected_region, selected_county, selected_transload_county, transload_county_centroids, cluster_centroids, se_county_centroids):
    """
    Function to get weighted flow lines based on selected filters
    Arguments:
    - OD_flows_df: DataFrame containing origin-destination flows
    - selected_region: List of selected region IDs
    - selected_county: List of selected county IDs
    - selected_transload_county: List of selected transload county IDs
    - transload_county_centroids: Dictionary containing centroids of transload counties
    - cluster_centroids: Dictionary containing centroids of regions
    - se_county_centroids: Dictionary containing centroids of Southeast counties
    Returns:
    - GeoDataFrame containing flow arcs with geometry and styling based on the provided region and county selections
    """
    # all_OD_col_idx = ['orig_reg', 'orig_cnty', 'orig_cnty_name', 'dest_cnty', 'dest_cnty_name']
    all_flow_df_cols = ['dest_cnty', 'dest_cnty_name']
    # quantile_num = 0
    
    # flow_arcs = OD_flows_df.groupby(all_OD_col_idx)['tons'].sum().reset_index() # Sum all the commodities together
    flow_arcs = filtered_flows_df.copy()
    
    MAX_LINE_WEIGHT = 5
    quantile_num = 0.99 if selected_region in ([], None, ['-1']) else  0.7
    if quantile_num > 0:
        threshold = flow_arcs['tons'].quantile(quantile_num)
        flow_arcs = flow_arcs[flow_arcs['tons'] >= threshold]
    
    if len(flow_arcs) == 0:
        return gpd.GeoDataFrame()

    flow_arcs['tons'] = np.round(flow_arcs['tons']*1000)

    # More optimized version
    if selected_county in ([], None, ['-1']):
        all_flow_df_cols = ['orig_reg', 'dest_cnty', 'dest_cnty_name']
        flow_arcs = flow_arcs.groupby(all_flow_df_cols)['tons'].sum().reset_index()
        orig_coords = flow_arcs['orig_reg'].map(cluster_centroids).values
        dest_coords = flow_arcs['dest_cnty'].map(transload_county_centroids).values
    else:
        all_flow_df_cols = ['orig_cnty', 'dest_cnty', 'dest_cnty_name']
        flow_arcs = flow_arcs.groupby(all_flow_df_cols)['tons'].sum().reset_index()
        orig_coords = flow_arcs['orig_cnty'].map(se_county_centroids).values
        dest_coords = flow_arcs['dest_cnty'].map(transload_county_centroids).values
        
    flow_min, flow_max = flow_arcs['tons'].min(), flow_arcs['tons'].max()
    if flow_max > 0:
        flow_arcs['normalized_flow'] = flow_arcs['tons'] / flow_max
        flow_arcs['weight'] = np.clip(flow_arcs['normalized_flow'] * MAX_LINE_WEIGHT, 0.2, MAX_LINE_WEIGHT)
        flow_arcs['opacity'] = np.clip(flow_arcs['normalized_flow'], 0.3, 0.8)

    flow_arcs['geometry'] = [LineString([orig, dest]) for orig, dest in zip(orig_coords, dest_coords)]
    flow_arcs_gdf = gpd.GeoDataFrame(flow_arcs, geometry='geometry')
    
    return flow_arcs_gdf

# ******************************************
#   HEATMAP GRAPH
# ******************************************
def generate_heatmap_graph(OD_flows_df, selected_region):
    """ 
    Generate a heatmap graph for origin-destination flows.
    Arguments:
    - OD_flows_df: DataFrame containing origin-destination flows with columns 'orig_reg', 'dest_cnty_name', and 'tons'.
    - selected_region: List of selected regions to filter the flows.
    Returns:
    - heatmap_fig: A Plotly figure object representing the heatmap.
    """
    filtered_flows = OD_flows_df.copy()
    filtered_flows['tons'] = (filtered_flows['tons'] * 1000).round().astype(int)
    
    if selected_region in (None, [], ['-1']):
        index_col = 'orig_reg'
    else:
        index_col = 'orig_cnty_name'

    heatmap_data = filtered_flows.pivot_table(
        index=index_col,
        columns='dest_cnty_name',
        values='tons',
        aggfunc='sum',
        fill_value=0
    )

    if not selected_region or selected_region == ['-1']:
        y_ticks =[f'Region {index}' for index in heatmap_data.index]
    else:
        y_ticks = heatmap_data.index
    

    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=y_ticks,
            colorscale='reds',
            colorbar=dict(
                title=dict(text="Tons", side="right"),
                titlefont=dict(size=14, family="Roboto, sans-serif"),
                thickness=12  # Reduce colorbar width (default is 30)
            ),    
        )
    )

    heatmap_fig.update_layout(
        title=None,
        # xaxis=dict(title="Destination", tickangle=45, title_font=dict(size=12, weight="bold"), tickfont=dict(size=8)),
        # yaxis=dict(title="Origin", title_font=dict(size=12, weight="bold"), tickfont=dict(size=10)),
        xaxis=dict(title=None, tickangle=45, title_font=dict(size=12, weight="bold", family="Roboto, sans-serif"), tickfont=dict(size=8)),
        yaxis=dict(title=None, title_font=dict(size=12, weight="bold", family="Roboto, sans-serif"), tickfont=dict(size=10)),
        template='mantine_light',
        margin=dict(l=50, r=50, t=20, b=50)
    )

    heatmap_fig.update_traces(hovertemplate="Origin: %{y}<br>Destination: %{x}<br>Tons: %{z}<extra></extra>")

    return heatmap_fig


# ******************************************
#   BAR GRAPHS
# ******************************************
def get_transload_top_few_counties_bar_graph(OD_flows_df, selected_region, index_col = 'orig_cnty_name', color_scale = REGION_COLORSCALE, num=10):
    
    """
    Function to generate a bar graph showing the top few counties based on origin-destination flows.
    Arguments:
    - OD_flows_df: DataFrame containing origin-destination flows with columns 'orig_reg
', 'orig_cnty', 'orig_cnty_name', 'dest_cnty', 'dest_cnty_name', and 'tons'.
    - selected_region: List of regions to filter the flows. If [-1] or [] or None, all regions are included.
    - index_col: Column to use for grouping the data (default is 'orig_cnty_name').
    - color_scale: Color scale to use for the bar graph (default is REGION_COLORSCALE).
    - num: Number of top counties to display 
    Returns:
    - fig: A Plotly figure object representing the bar graph.
    """
    
    filtered_flows = OD_flows_df.copy()
    top_counties = filtered_flows.groupby(index_col, as_index=False)['tons'].sum()
    top_counties = top_counties.sort_values(by='tons', ascending=False).head(num)
    top_counties['tons'] = top_counties['tons'].astype(int)

    colors = pc.sample_colorscale(color_scale, np.linspace(0.3, 1, num))
    fig = go.Figure(
        data=go.Bar(
            y=top_counties[index_col][::-1],  # Reverse for horizontal bar chart
            x=top_counties['tons'][::-1],  # Convert to million tons
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='lightgray', width=1)
            ),
            text=[f"{tons:}" for tons in top_counties['tons'][::-1]],  # Add flow values as text
            textposition='auto',
            textfont=dict(size=10)
        )
    )

    region_text = f'Selected Regions' if (selected_region != ['-1'] or selected_region is None or selected_region == []) else 'Southeast'
    if index_col == 'orig_cnty_name':
        title_header = f'Top Counties within {region_text}'
    else:
        title_header = f'Top Destination Counties'
        
    fig.update_layout(
        title=dict(
            text=f"{title_header}",
            x=0.5,
            y=0.97,
            font=dict(family="Roboto, sans-serif", size=14, color="black", weight="bold"),
        ),
        xaxis_title='Freight Flow (in thousand tons)',
        xaxis_title_font=dict(family="Roboto, sans-serif", size=11, color="black", weight="normal"),
        xaxis=dict(tickfont=dict(size=10)),  # Updated x-axis tick font size
        yaxis=dict(tickfont=dict(size=8)),  # Updated y-axis tick font size
        margin=dict(l=1, r=1, t=30, b=1),
        template='mantine_light'
    )
    
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Flow: %{x:,} tons<extra></extra>"
    )
    return fig


# ******************************************
#   CARD BODY INFO
# ******************************************
def get_transload_card_info(OD_flows_df):
    """ 
    Generate a summary card for transload origin-destination flows.
    Arguments:
    - OD_flows_df: DataFrame containing transload origin-destination flows with columns 'orig_cnty', 'dest_cnty', and 'tons'.
    Returns:
    - card_text: A Dash HTML Div component containing the summary text.
    """
    total_flow = OD_flows_df['tons'].sum()
    orig_counties = OD_flows_df['orig_cnty'].drop_duplicates().tolist()
    dest_counties = OD_flows_df['dest_cnty'].drop_duplicates().tolist()
    card_text = dmc.Text(
        [
            dmc.Text(f"{len(orig_counties)}", span=True, fw="bold", fs="italic", c="black"),
            dmc.Text(" Southeast counties", span=True, fs="italic", c="black"),
            dmc.Text(" has a total freight flow of ~ ", span=True, fs="italic", c="black"),
            dmc.Text(f"{int(np.ceil(total_flow/1000))} million tons", span=True, fw="bold", fs="italic", c="black"),
            dmc.Text(" via trucks to ", span=True, fs="italic", c="black"),
            dmc.Text(f"{len(dest_counties)} counties", span=True, fw="bold", fs="italic", c="black"),
            dmc.Text(" within 50 mile radius of G&W Transload Stations in IL, IN, OH and PA", span=True, fs="italic", c="black"),
        ],
        ta="center",
        size="md"
    )
    
    return card_text

# ******************************************
#   TRANSLOAD PIE CHART
# ******************************************
def get_transload_pie_commodity_mantine(OD_flows_df, selected_region, selected_county, selected_transload_county):
    """ 
    Function to generate a pie chart showing freight flow by commodity using Mantine Pie Chart.
    Arguments:
    - OD_flows_df: DataFrame containing transload origin-destination flows with columns 'orig_reg', 'orig_cnty', 'dest_cnty', 'commodity_code', and 'tons'.
    - selected_region: List of regions to filter the flows. If [-1] or [] or None, all regions are included.
    - selected_county: List of counties to filter the flows. If [-1] or [] or None, all counties are included
    - selected_transload_county: The transload county to filter the flows. If -1 or None, all transload counties are included.
    Returns:
    - fig: A Dash Mantine Components DonutChart object representing the pie chart.
    """
    commodity_df = OD_flows_df.copy()
    grouped_flows = commodity_df.groupby(['commodity_code'], as_index=False)['tons'].sum()
    grouped_flows = grouped_flows.sort_values(by='tons', ascending=False)
    total_flow = grouped_flows['tons'].sum()

    color_list = ['teal','orange','blue','red','purple']
    
    # Calculate percentage for each commodity
    grouped_flows['percent'] = (grouped_flows['tons'] / grouped_flows['tons'].sum()) * 100

    fig = dmc.DonutChart(
        data=[
            {
                "name": f"{grouped_flows['commodity_code'].map(commodity_map).iloc[i]}",
                "color": color_list[i],
                "value": grouped_flows['percent'].iloc[i].round(1)
            }
            for i in range(len(grouped_flows))
        ],
        size=250,
        thickness=20,
        chartLabel="Commodity Share (in %)",
        withLabelsLine=True,
        withLabels=True,
        fz='xs',
        fw='bold',
        withTooltip=True
    )
    return fig

# ******************************************
#   METRIC CARD INFO
# ******************************************

def get_metric_card_info(OD_flows_df, selected_region, selected_county, selected_transload_county, slider_val = 50, boxcar_pallets = BOX_CAR_PALLETS, ltl_percent = 10):
    """
    Function to generate a card with intermodal freight metrics based on selected filters
    Arguments:
    - OD_flows_df: DataFrame containing transload origin-destination flows with columns 'orig_reg', 'orig_cnty', 'dest_cnty', and 'tons'.
    - selected_region: List of regions to filter the flows. If [-1] or [] or None, all regions are included.
    - selected_county: List of counties to filter the flows. If [-1] or [] or None, all counties are included.
    - selected_transload_county: List of transload counties to filter the flows. If [-1] or [] or None, all transload counties are included.
    - slider_val: Slider value representing the percentage of truck pallets (default is 50).
    - boxcar_pallets: Number of pallets in a boxcar (default is 20).
    - ltl_percent: Percentage of LTL (Less Than Truckload) freight (default is 10).
    Returns:
    - card_text: A Dash Mantine Components Table object containing the intermodal freight metrics.
    """
    
    filtered_flows = OD_flows_df.copy()
    filtered_flows['tons'] = (filtered_flows['tons'] * 1000).round().astype(int)

    num_truck_pallets = int(np.ceil((slider_val/100) * (MAX_TRUCK_PALLETS)))
    expected_truck_cap = int(num_truck_pallets * PALLET_CAPACITY) # in lbs
    expected_boxcar_cap = boxcar_pallets * PALLET_CAPACITY
        
    total_tonnage = filtered_flows['tons'].sum()
    ftl_tonnage = int(np.ceil(total_tonnage * (1 - (ltl_percent/100))))  # Assuming 90% of total flow is FTL
    num_ftl_trucks = int(np.ceil(ftl_tonnage * 2000 / expected_truck_cap))  # Assuming each truck carries 20 tons
    num_ftl_box_cars= int(np.ceil(ftl_tonnage * 2000 / expected_boxcar_cap))  # Assuming each box car carries 100 tons
    ltl_tonnage = total_tonnage - ftl_tonnage  # LTL is the remaining tonnage
    num_ltl_trucks = int(np.ceil(total_tonnage*(ltl_percent/100)*2000/expected_truck_cap))  # Assuming each truck carries 20 tons
    num_ltl_box_cars = int(np.ceil(total_tonnage*(ltl_percent/100)*2000/expected_boxcar_cap))  # Assuming each box car carries 100 tons

    card_text = dmc.Table(
        [
            dmc.TableCaption(
                "Intermodal Freight Metrics",
                ta='center',
                fz="md",
                fw=700,
                c="dark"
            ),
            dmc.TableThead(
                dmc.TableTr(
                    [
                        dmc.TableTh("Metric", ta='center', fz='sm'),
                        dmc.TableTh("FTL", ta='center', fz='md'),
                        dmc.TableTh("LTL", ta='center', fz='md'),
                        dmc.TableTh("Total", ta='center', fz='md'),
                    ]
                )
            ),
            dmc.TableTbody(
                [
                    dmc.TableTr(
                        [
                            dmc.TableTd("Tonnage (in tons)", ta='center', fz='xs', fw='bold'),
                            dmc.TableTd(f"{ftl_tonnage:,}", ta='center', fz='xs'),
                            dmc.TableTd(f"{ltl_tonnage:,}", ta='center', fz='xs'),
                            dmc.TableTd(f"{total_tonnage:,}", ta='center', fz='xs')
                        ]
                    ),
                    dmc.TableTr(
                        [
                            dmc.TableTd(f"#Trucks (Cap: ~{expected_truck_cap:,} lbs)", ta='center', fz='xs',  fw='bold'),
                            dmc.TableTd(f"{num_ftl_trucks:,}", ta='center', fz='xs'),
                            dmc.TableTd(f"{num_ltl_trucks:,}", ta='center', fz='xs'),
                            dmc.TableTd(f"{num_ftl_trucks + num_ltl_trucks:,}", ta='center', fz='xs')
                        ]
                    ),
                    dmc.TableTr(
                        [
                            dmc.TableTd(f"#Box Cars (Cap: ~{expected_boxcar_cap:,} lbs)", ta='center', fz='xs',  fw='bold'),
                            dmc.TableTd(f"{num_ftl_box_cars:,}", ta='center', fz='xs'),
                            dmc.TableTd(f"{num_ltl_box_cars:,}", ta='center', fz='xs'),
                            dmc.TableTd(f"{num_ftl_box_cars + num_ltl_box_cars:,}", ta='center', fz='xs'),
                        ]
                    )
                ]
            )
        ],
        verticalSpacing="xs",
        horizontalSpacing="xs",
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        withColumnBorders=True,
        style={"justifyContent": "center", "textAlign": "center"}
    )
    return card_text

def get_flow_grid(row_data):
    
    AgGridColumns = [
        dict(field='orig_reg', headerName='Origin Region'),
        dict(field='orig_cnty_name', headerName='Origin County'),
        dict(field='dest_cnty_name', headerName='Destination County'),
        dict(field='tons', headerName='Tons', 
            valueFormatter={"function": "d3.format(',.0f')(params.value)"},
        )
    ]
    
    flow_grid = dag.AgGrid(
        id='flows-grid',
        rowData=row_data,
        columnDefs=AgGridColumns,
        columnSize='autoSizeAll',  # This will size columns based on both header and values
        dashGridOptions={
            'pagination': True,
            "columnHoverHighlight": True,
            "rowSelection": {'mode': 'multiRow'}
        },
        defaultColDef=dict(filter=True, sortable=True, resizable=True, wrapText=True),
        csvExportParams={"fileName": "origin_dest_flows.csv", 'onlySelected': True},
        style={"height": "100%", "width": "100%"}
    )
    
    return flow_grid