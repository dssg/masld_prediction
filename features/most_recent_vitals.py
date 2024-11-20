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


def _generate_date_series(engine, start_date, end_date, interval):

    q = f"""
        select generate_series(
            '{start_date}'::date,
            '{end_date}'::date,
            '{interval}'::interval
        )::date::varchar as as_of_dates
    """

    return pd.read_sql(q, engine).as_of_dates.tolist()


def create_most_recent_vitals_table(engine, as_of_dates):
    
    query_template = '''
        drop table if exists {temp_table_name};

        create table {temp_table_name} as ( 
            -- converting this to a 
            with date_filtered as (
                -- we assume that height is pretty constant
                select 
                    entity_id,
                    max(measure_date) as measure_date,
                    'height' as measure_type,
                    avg(ht) as value
                from clean.vitals
                where measure_date < '{as_of_date}'::date
                group by entity_id
                UNION ALL
                select 
                    entity_id,
                    measure_date,
                    'weight' as measure_type,
                    avg(wt) as value
                from clean.vitals
                where measure_date < '{as_of_date}'::date
                group by entity_id, measure_date
                UNION ALL
                select 
                    entity_id,
                    measure_date,
                    'systolic' as measure_type,
                    avg(systolic) as value
                from clean.vitals
                where measure_date < '{as_of_date}'::date
                group by entity_id, measure_date
                UNION ALL
                select 
                    entity_id,
                    measure_date,
                    'diastolic' as measure_type,
                    avg(diastolic) as value
                from clean.vitals
                where measure_date < '{as_of_date}'::date
                group by entity_id, measure_date
                UNION ALL
                -- currently calculating BMI only when both height and weight are known
                -- We coud do something smarter here
                select 
                    entity_id,
                    measure_date,
                    'bmi' as measure_type,
                    703 * avg(wt) / (avg(ht) * avg(ht)) as value
                from clean.vitals
                where measure_date < '{as_of_date}'::date
                and wt is not null
                and ht is not null 
                and ht > 0
                and wt > 0
                group by entity_id, measure_date
            )
            select distinct on (entity_id, measure_type)
                entity_id,
                -- This is a hack to bypass the triage's knowledge_date comparison
                '{as_of_date}'::date as as_of_date,
                measure_date,
                measure_type,
                value,
                '{as_of_date}'::date - measure_date as days_since_measurement
            from date_filtered
            where value is not null
            order by entity_id, measure_type, measure_date desc
        
        ) 
    '''
    
    temp_tables = list()
    
    for as_of_date in as_of_dates:
        date_str = ''.join(as_of_date.split('-'))
        
        temp_table_name = f'most_recent_vitals_{date_str}'
        
        q = query_template.format(
            temp_table_name=temp_table_name,
            as_of_date=as_of_date
        )
        
        logger.info(f'Creating the temp table {temp_table_name}:')
        logger.info(q)

        with engine.begin() as conn:
            conn.execute(q)
            temp_tables.append(temp_table_name)

        logger.info('Success!')
        
    logger.info('All temp tables created. Creating the final table...')
    
    target_table = 'clean.most_recent_vitals'
    
    q = f'''
    DROP TABLE IF EXISTS {target_table};

    CREATE TABLE {target_table} as (
    '''

    for i, tt in enumerate(temp_tables):
        if i > 0 :
            q+= 'UNION ALL'
        
        q += f'''
        select * from {tt}
        '''
    
    q += ');'

    logger.info(q)

    with engine.begin() as conn:
        conn.execute(q)
        
    logger.info('Dropping the temp tables')
    for tt in temp_tables:
        q = f'drop table {tt}'

        with engine.begin() as conn:
            conn.execute(q)

        logger.info(f'Dropped {tt}')
        
    index_query = '''
        create index on clean.most_recent_vitals(entity_id);
        create index on clean.most_recent_vitals(as_of_date);
        create index on clean.most_recent_vitals(measure_date);
        create index on clean.most_recent_vitals(measure_type);
        create index on clean.most_recent_vitals(days_since_measurement);
    '''
    with engine.begin() as conn:
        logger.info('Creating indexes on {target_table}')
        conn.execute(index_query)
        
if __name__ == '__main__':
    # engine = get_db_engine('sampledb.yaml')
    engine = get_db_engine('db.yaml')
    
    as_of_dates  = _generate_date_series(engine, '2015-05-01', '2023-05-01', '12 month')
    
    create_most_recent_vitals_table(
        engine=engine,
        as_of_dates=as_of_dates
    )