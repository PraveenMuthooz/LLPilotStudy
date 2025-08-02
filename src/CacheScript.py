import warnings
warnings.filterwarnings("ignore")

import pickle
import redis
from typing import Optional, Dict, Any
import hashlib
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
    

def create_cache_key(selected_region, selected_county, selected_transload_county):
    """Create a consistent cache key from filter selections"""
    # Convert lists to tuples for hashing, handle None values
    key_data = {
        'region': tuple(sorted(selected_region)) if selected_region else None,
        'county': tuple(sorted(selected_county)) if selected_county else None,
        'transload': tuple(sorted(selected_transload_county)) if selected_transload_county else None
    }
    
    # Create hash from the key data
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()

class TransloadFlowDataCache:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db,
                decode_responses=False,  # Keep binary for pickle
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except redis.ConnectionError:
            logger.error("❌ Redis connection failed - falling back to memory cache")
            self.redis_client = None
            self.memory_cache = {}

        self.default_expiry = 3600  # Default expiry time in seconds

    def _make_key(self, selected_region, selected_county, selected_transload_county):
        """Create Redis Key"""
        cache_key = create_cache_key(selected_region, selected_county, selected_transload_county)
        return f"flow_data:{cache_key}"
        
    def get(self, selected_region, selected_county, selected_transload_county):
        """Get cached data for the given filters"""
        key = self._make_key(selected_region, selected_county, selected_transload_county)
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"Cache read error: {e}")
            
        return None
        
    def set(self, selected_region, selected_county, selected_transload_county, filtered_flows: pd.DataFrame, expiry: int = None):
        key = self._make_key(selected_region, selected_county, selected_transload_county)
        expiry = expiry or self.default_expiry
        try:
            self.redis_client.setex(key, expiry, pickle.dumps(filtered_flows))
            print(f"Cache set for key: {key}")
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                keys = self.redis_client.keys(f"{self.key_prefix}:*")
                return {
                    'type': 'Redis',
                    'keys_count': len(keys),
                    'memory_usage': info.get('used_memory_human', 'N/A'),
                    'connected': True
                }
            else:
                return {
                    'type': 'Memory',
                    'keys_count': len(self.memory_cache),
                    'memory_usage': 'N/A',
                    'connected': False
                }
        except:
            return {'type': 'Error', 'connected': False}
        
    def clear_pattern(self, pattern="flow_data:*"):
        """Clear cache entries matching pattern"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
            print(f"Cleared {len(keys)} cache entries")
        
transload_flow_cache = TransloadFlowDataCache()


def get_filtered_flows_with_redis(transload_OD_flows_df, selected_region, selected_county, selected_transload_county):
    """
    Function to get filtered flows from Redis cache or compute them if not cached.
    """
    start_time = time.time()
    cached_flows = transload_flow_cache.get(selected_region, selected_county, selected_transload_county)
    if cached_flows is not None:
        print("Redis cache")
        return cached_flows
    print("Cache miss, computing flows...")
    
    computation_time = time.time() - start_time

    filtered_flows = filter_flows_optimized(
        transload_OD_flows_df, selected_region, selected_county, selected_transload_county
    )
    logger.info(f"⏱️ Computation took {computation_time:.2f}s - {len(filtered_flows)} rows")
    
    transload_flow_cache.set(selected_region, selected_county, selected_transload_county, filtered_flows)
    
    return filtered_flows