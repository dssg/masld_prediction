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


def create_most_recent_lab_value_table(engine, lonic_mapping, as_of_dates):

    all_loincs = list()
    lab_case_statement = 'case ' 
    for lab, loinc in lonic_mapping.items():
        lab_case_statement += f'''when lab_loinc in ('{"','".join(loinc)}') then '{lab}'
        '''
        
        all_loincs += loinc

    lab_case_statement += '''else 'other' end as lab_type'''
    
    all_loincs = "','".join(all_loincs)

    query_template = '''
        drop table if exists {temp_table_name};
        
        create table {temp_table_name} as ( 
            with date_filtered as (
                select 
                entity_id,
                lab_loinc,
                specimen_date,
                -- In case there are multiple runs of the same test, we take average
                -- todo:verify validity
                avg(result_num) as result_num,
                {lab_case_statement} 
                from clean.labs
                where specimen_date < '{as_of_date}'::date
                and lab_loinc in ('{all_loincs}')
                group by entity_id, specimen_date, lab_loinc
                
            )
            select distinct on (entity_id, lab_type)
                entity_id,
                -- This is a hack to bypass the triage's knowledge_date comparison
                '{as_of_date}'::date as as_of_date,
                specimen_date,
                lab_type,
                result_num,
                '{as_of_date}'::date - specimen_date as days_since_lab
            from date_filtered
            order by entity_id, lab_type, specimen_date desc
        
    ) 
    '''
    temp_tables = list()
    
    for as_of_date in as_of_dates:
        date_str = ''.join(as_of_date.split('-'))
        
        temp_table_name = f'most_recent_labs_{date_str}'
        
        q = query_template.format(
            temp_table_name=temp_table_name,
            as_of_date=as_of_date,
            lab_case_statement=lab_case_statement,
            all_loincs=all_loincs
        )
        
        logger.info(f'Creating the temp table {temp_table_name}:')
        logger.info(q)

        with engine.begin() as conn:
            conn.execute(q)
            temp_tables.append(temp_table_name)

        logger.info('Success!')
        
    logger.info('All temp tables created. Creating the final table...')
    
    target_table = 'clean.most_recent_labs'
    
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
        create index on clean.most_recent_labs(entity_id);
        create index on clean.most_recent_labs(as_of_date);
        create index on clean.most_recent_labs(specimen_date);
        create index on clean.most_recent_labs(lab_type);
        create index on clean.most_recent_labs(days_since_lab);
    '''
    with engine.begin() as conn:
        logger.info('Creating indexes on {target_table}')
        conn.execute(index_query)
        
    
if __name__ == '__main__':

    # engine = get_db_engine('sampledb.yaml')
    engine = get_db_engine('db.yaml')

    lab_loinc_mapping = {
        'platelet': ['777-3', '26515-7', '49497-1', '778-1'],
        'alt': ['1742-6', '1743-4', '1744-2'],
        'ast': ['1920-8','30239-8'],
        'a1c': ['17856-6', '41995-2', '4549-2', '4548-4'],
        'albumin': ['1751-7', '61151-7', '2862-1', '61152-5'],
        'alp': ['6768-6'],
        'ggt': ['2324-2'],
        'tg': ['2571-8'],
        'ldl': ['13457-7', '18262-6', '2089-1', '3046-0'],
        'hdl': ['2085-9'],
        'tot_chol': ['2093-3'],
        'apo_a1': ['1869-7', '55724-9'], 
        'apo_b': ['1884-6', '1871-3', '1881-2'],
        'hscrp': ['30522-7', '35648-5'],
        'lp_a': ['43583-4', '10835-7'],
        'nlr': ['770-8', '23761-0', '26511-6'],
        'non_hdl': ['43396-1'],
        'uacr': ['9318-7', '13705-9', '32294-1', '14585-4'],
        'vldl': ['46986-6', '13458-5', '2091-7'],
        'creatinine': ['2160-0', '38483-4'],
        'uric_acid': ['3084-1', '14933-6'],
        'hemoglobin': ['718-7', '55782-7', '20509-6', '30350-3', '76769-9'],
        'glucose': ['2345-7', '2339-0', '2340-8', '14749-6'],
        'iron_saturation': ['2502-3', '14801-5'],
        'ferritin': ['2276-4', '20567-4'],
        'aat': ['1825-9', '32769-2', '6771-0', '6770-2', '49244-7'],
        'basophils': ['704-7', '26444-0', '705-4'],
        'blratio': ['706-2', '30180-4', '707-0'],
        'el_ratio': ['713-8', '26450-7', '714-6'],
        'eosinophils': ['711-2', '26449-9', '712-0', '20472-7'],
        'erythrocytes': ['789-8', '26453-1'],
        'hematocrit': ['4544-3', '20570-8', '4545-0', '48703-3'],
        'leukocytes': ['6690-2', '26464-8'],
        'lyle_ratio': ['736-9', '26478-8', '737-7'],
        'mlratio': ['5905-5', '26485-3', '744-3'],
        'monocytes': ['742-7', '26484-6', '743-5'],
        'neutrophils': ['751-8', '753-4', '26499-4'],
        'platelet_volume': ['32623-1', '776-5', '28542-9']
    }

    as_of_dates  = _generate_date_series(engine, '2015-05-01', '2023-05-01', '12 month')
    
    create_most_recent_lab_value_table(
        engine=engine,
        lonic_mapping=lab_loinc_mapping,
        as_of_dates=as_of_dates
    )
