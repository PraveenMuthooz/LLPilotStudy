import psycopg2
import io 
from joblib import Parallel, delayed
import io
import pandas as pd

# ****************************************************************************************************************************************************
# DATABASE PARAMETERS
# ****************************************************************************************************************************************************
DB_NAME = 'FAF'
USER_NAME = 'postgres'
PASSWORD = 'Praveen@98'
HOST = 'localhost'
DB_PORT = '5432'

# Function to connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=USER_NAME,
            password=PASSWORD,
            host=HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise
    
# Function to select data from the database
def select_data(query):
    conn = get_db_connection()
    try:
        data = pd.read_sql_query(query, conn)
        return data
    except Exception as e:
        print(f"Error selecting data from database: {e}")
        raise
    finally:
        conn.close()

# Function to read large data from the database       
def read_large_data(table_name):
    conn = get_db_connection()
    cur = conn.cursor()
    output = io.StringIO()
    
    # Get the total number of rows in the table
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cur.fetchone()[0]
    
    # Define the number of chunks for parallel processing
    num_chunks = 4  # Adjust based on your system's resources
    chunk_size = total_rows // num_chunks
    
    def fetch_chunk(start, end):
        chunk_output = io.StringIO()
        cur.copy_expert(
            f"COPY (SELECT * FROM {table_name} OFFSET {start} LIMIT {end - start}) TO STDOUT WITH CSV HEADER",
            chunk_output
        )
        chunk_output.seek(0)
        return pd.read_csv(chunk_output)
    
    # Parallelize the fetching of chunks
    chunks = Parallel(n_jobs=num_chunks)(
        delayed(fetch_chunk)(i * chunk_size, (i + 1) * chunk_size if i < num_chunks - 1 else total_rows)
        for i in range(num_chunks)
    )
    
    # Combine all chunks into a single DataFrame
    df = pd.concat(chunks, ignore_index=True)
    
    cur.close()
    conn.close()
    return df

# Function to insert chunk
def insert_chunk(chunk, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    csv_buffer = io.StringIO()
    chunk.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)
    cursor.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV", csv_buffer)
    conn.commit()
    cursor.close()
    conn.close()

# FUNCTION TO CREATE SQL TABLE
def create_sql_table(create_table_query):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(create_table_query)
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    
    conn.commit()
    cursor.close()
    conn.close()

#------------------------------------------------------------------------------------------------------------
#                                           QUERIES
#------------------------------------------------------------------------------------------------------------
#-----------------------------------
#       STATE-REGION MAPPING
#-----------------------------------
state_region_query = """
SELECT DISTINCT state_name, region
FROM state_region_mapping;
""" 
#-----------------------------------
#       COMMODITY MAPPING
#-----------------------------------
commodity_query = """
SELECT DISTINCT commodity_code, commodity_name
FROM commodity_type_mapping;
"""
#-----------------------------------
#       TRANSPORT MODE MAPPING
#-----------------------------------
transport_mode_query = """
SELECT DISTINCT mode, mode_name
FROM transport_mode_mapping;
"""

#-----------------------------------
#        ALL US COUNTIES  
#-----------------------------------
all_county_shapes_query = """
    SELECT US.*
    FROM us_county_boundaries US
"""


#-----------------------------------
#   US COUNTY SHAPES WITH FLOWS 
#-----------------------------------
us_county_shapes_query = """
WITH county_flows AS (
	SELECT geoid, name, namelsad, intptlat, intptlon, CF.state_name, sum(inter) inter, sum(inbound) inbound, sum(outbound) outbound, geom
	FROM county_level_flows CF
	JOIN state_region_mapping SRM 
		ON CF.state_name = SRM.state_name
	WHERE mode = '11'
		and commodity_code IN ('sctg0109','sctg3499','sctg2033')
		and region = 'Southeast'
	GROUP BY geoid, name, namelsad, intptlat, intptlon, geom, CF.state_name
	)
SELECT geoid, name, namelsad, intptlat, intptlon, state_name, inter, inbound, outbound, (inter + inbound + outbound) total, geom
FROM county_flows;
"""

#-----------------------------------
#   ALL COUNTY SHAPES WITH FLOWS 
#-----------------------------------
us_county_shapes_query = """
WITH county_flows AS (
	SELECT geoid, name, namelsad, intptlat, intptlon, CF.state_name, sum(inter) inter, sum(inbound) inbound, sum(outbound) outbound, geom
	FROM county_level_flows CF
	JOIN state_region_mapping SRM 
		ON CF.state_name = SRM.state_name
	WHERE mode = '11'
		and commodity_code IN ('sctg0109','sctg3499','sctg2033')
		and region = 'Southeast'
	GROUP BY geoid, name, namelsad, intptlat, intptlon, geom, CF.state_name
	)
SELECT geoid, name, namelsad, intptlat, intptlon, state_name, inter, inbound, outbound, (inter + inbound + outbound) total, geom
FROM county_flows;
"""

#-----------------------------------
#       SOUTHEAST USA COUNTY
#-----------------------------------
US_SE_county_query = """
SELECT US.*
FROM us_county_boundaries US
JOIN state_region_mapping REG
    ON US.state_name = REG.state_name
WHERE REG.region = 'Southeast'
""" 

#-----------------------------------
#   SOUTHEAST USA REGION CLUSTERS
#-----------------------------------
US_SE_region_query = """
SELECT CS.*
FROM cluster_shapes CS
""" 

#-------------------------------------
#   CLUSTER COUNTY MAPPING 
#-------------------------------------
region_cluster_county_mapping_query = """
SELECT * FROM county_region_cluster_mapping;
"""
        

#-----------------------------------
#   TRANSLOAD COUNTIES
#-----------------------------------
transload_read_query = """
    SELECT CS.*, (CS.inter + CS.inbound + CS.outbound) total
    FROM county_shapes_with_flows CS
    WHERE CS.geoid IN (SELECT geoid FROM transload_counties)
"""
#-----------------------------------
#   TRANSLOAD COUNTY O-D FLOWS
#-----------------------------------
transload_flows_query = """
SELECT * FROM get_se_cluster_transload_flows()
"""

#-------------------------------------
#   TRANSLOAD COUNTIES TABLE 
#-------------------------------------
transload_counties_table_query = """
DROP TABLE IF EXISTS public.transload_counties;
CREATE TABLE IF NOT EXISTS public.transload_counties
(
    geoid integer
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.transload_counties
OWNER to postgres;

DROP INDEX IF EXISTS public.idx_transload_counties;

CREATE INDEX IF NOT EXISTS idx_transload_counties
    ON public.transload_counties USING btree
    (geoid ASC NULLS LAST)
    TABLESPACE pg_default;
"""


#--------------------------------------------------------
#   LIVING LAB ORIGIN SE COUNTIES TABLE
#--------------------------------------------------------
ll_se_counties_table_query = """
DROP TABLE IF EXISTS public.ll_se_counties;
CREATE TABLE IF NOT EXISTS public.ll_se_counties
(
    geoid integer
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.ll_se_counties
OWNER to postgres;

DROP INDEX IF EXISTS public.idx_ll_se_counties;

CREATE INDEX IF NOT EXISTS idx_ll_se_counties
    ON public.ll_se_counties USING btree
    (geoid ASC NULLS LAST)
    TABLESPACE pg_default;
"""

#-------------------------------------
#   LIVING LAB ORIGIN SE COUNTIES 
#-------------------------------------
ll_se_counties_read_query = """
SELECT DISTINCT geoid from ll_se_counties
"""

#-------------------------------------
#   INTERMODAL COUNTY SHAPES
#-------------------------------------
im_county_read_query = """
SELECT CS.*, (CS.inter + CS.inbound + CS.outbound) total
FROM county_shapes_with_flows CS
WHERE CS.geoid IN (SELECT geoid FROM intermodal_counties)
"""

#-------------------------------------
#   INTERMODAL FLOWS 
#-------------------------------------
im_flows_query = """
SELECT * FROM get_intermodal_county_flows();
"""
#-------------------------------------
#   INTERMODAL COUNTIES TABLE 
#-------------------------------------
im_counties_table_query = """
    DROP TABLE IF EXISTS public.intermodal_counties;
    CREATE TABLE IF NOT EXISTS public.intermodal_counties
    (
        geoid integer
    )
    TABLESPACE pg_default;

    ALTER TABLE IF EXISTS public.intermodal_counties
    OWNER to postgres;
    
    DROP INDEX IF EXISTS public.idx_intermodal_counties;

    CREATE INDEX IF NOT EXISTS idx_intermodal_counties
        ON public.intermodal_counties USING btree
        (geoid ASC NULLS LAST)
        TABLESPACE pg_default;
    """
    
#-------------------------------------
#   INTERMODAL COUNTIES TABLE 
#-------------------------------------
county_OD_container_flows_query = """
SELECT * FROM get_within_se_containers()
"""