from operator import index
import os 
import yaml
import logging
import pandas as pd

from utils import get_db_engine

from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger.addHandler(logging.StreamHandler())

engine = get_db_engine('db.yaml')


def create_most_recent_vitals_table(engine, entity_date_table, target_table_name='most_recent_vitals', index_cols=[]):
    
    ''' This is a process that can happen only after the cohort/labels table is created '''
    
    q = f'''
    
        drtop table if exists clean.{target_table_name};
        
        create table clean.{target_table_name} as (
            with base as (
                select
                    l.entity_id, as_of_date, measure_date, avg(wt) as value, 'weight' as measure_type
                from {entity_date_table} l inner join clean.vitals v
                on l.entity_id = v.entity_id 
                and l.as_of_date > v.measure_date 
                group by l.entity_id, as_of_date, measure_date 
                union all 
                select
                    l.entity_id, as_of_date, max(measure_date) as measure_date, avg(ht) as value, 'height' as measure_type
                from {entity_date_table} l inner join clean.vitals v
                on l.entity_id = v.entity_id 
                and l.as_of_date > v.measure_date 
                group by l.entity_id, as_of_date
                union all 
                select
                    l.entity_id, as_of_date, measure_date, avg(systolic) as value, 'systolic' as measure_type
                from {entity_date_table} l inner join clean.vitals v
                on l.entity_id = v.entity_id 
                and l.as_of_date > v.measure_date 
                group by l.entity_id, as_of_date, measure_date
                union all 
                select
                    l.entity_id, as_of_date, measure_date, avg(diastolic) as value , 'diastolic' as measure_type
                from {entity_date_table} l inner join clean.vitals v
                on l.entity_id = v.entity_id 
                and l.as_of_date > v.measure_date 
                group by l.entity_id, as_of_date, measure_date
                union all
                select
                    l.entity_id, as_of_date, measure_date, 703 * avg(wt) / (avg(ht) * avg(ht)) as value, 'bmi' as measure_type
                from {entity_date_table} l inner join clean.vitals v
                on l.entity_id = v.entity_id 
                and l.as_of_date > v.measure_date 
                group by l.entity_id, as_of_date, measure_date
            )
            select distinct on (entity_id, as_of_date, measure_type) 
                entity_id, as_of_date, measure_date, measure_type, value, as_of_date::date - measure_date::date as days_since_measurement
            from base 
            order by entity_id, as_of_date, measure_type, measure_date desc
        );
    '''
    
    with engine.begin() as conn:
        conn.execute(q)
        
    for col in index_cols:
        index_query = f'''
            create index on clean.{target_table_name}({col});
        '''
        with engine.begin() as conn:
            logger.info(f'Creating index on {target_table_name}({col})')
            conn.execute(index_query)
        
    logger.info(f'{target_table_name} and indexes created!')
    
    
if __name__ == '__main__':
    engine = get_db_engine('db.yaml')
    
    create_most_recent_vitals_table(
        engine=engine,
        entity_date_table='labels_biopsy_1mo_074ad70e4c3298e002716406315bd56d',
        target_table_name='most_recent_vitals_biopsy_cohort',
        index_cols=['entity_id', 'as_of_date', 'measure_date', 'measure_type']
    )