import warnings
warnings.filterwarnings("ignore")

import pickle
from typing import Optional, Dict, Any
import logging
from functools import lru_cache
import json
import pandas as pd 
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_flows_with_commodity_optimized(OD_flows_df, selected_region, selected_county, selected_transload_county):
    """Optimized filtering using boolean masks"""
    mask = pd.Series(True, index=OD_flows_df.index)
        
    if selected_transload_county not in (None, [], ['-1']):
        transload_list = [int(t) for t in selected_transload_county if t != '-1']
        mask &= OD_flows_df['dest_cnty'].isin(transload_list)
    
    if selected_region not in (None, [], ['-1']):
        region_list = [int(r) for r in selected_region if r != '-1']
        mask &= OD_flows_df['orig_reg'].isin(region_list)
    
    if selected_county not in (None, [], ['-1']):
        county_list = [int(c) for c in selected_county if c != '-1']
        mask &= OD_flows_df['orig_cnty'].isin(county_list)
    
    return OD_flows_df[mask]

def filter_flows_optimized(OD_flows_df, selected_region, selected_county, selected_transload_county):
    """Optimized filtering using boolean masks"""
    all_OD_col_idx = ['orig_reg', 'orig_cnty', 'orig_cnty_name', 'dest_cnty', 'dest_cnty_name']
    OD_flows_df = OD_flows_df.groupby(all_OD_col_idx)['tons'].sum().reset_index()
    
    mask = pd.Series(True, index=OD_flows_df.index)
    
    if selected_transload_county not in (None, [], ['-1']):
        transload_list = [int(t) for t in selected_transload_county if t != '-1']
        mask &= OD_flows_df['dest_cnty'].isin(transload_list)
    
    if selected_region not in (None, [], ['-1']):
        region_list = [int(r) for r in selected_region if r != '-1']
        mask &= OD_flows_df['orig_reg'].isin(region_list)
    
    if selected_county not in (None, [], ['-1']):
        county_list = [int(c) for c in selected_county if c != '-1']
        mask &= OD_flows_df['orig_cnty'].isin(county_list)
    
    return OD_flows_df[mask]


def filter_flows_region(OD_flows_df, selected_region):
    all_OD_col_idx = ['orig_reg', 'orig_cnty', 'orig_cnty_name', 'dest_cnty', 'dest_cnty_name']
    OD_flows_df = OD_flows_df.groupby(all_OD_col_idx)['tons'].sum().reset_index() 
    mask = pd.Series(True, index=OD_flows_df.index)
    
    if selected_region and selected_region != ['-1']:
        region_list = [int(r) for r in selected_region if r != '-1']
        mask &= OD_flows_df['orig_reg'].isin(region_list)
    
    return OD_flows_df[mask]
    