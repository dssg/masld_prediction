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






def create_most_recent_lab_value_table(engine, entity_date_table, lonic_mapping, target_table_name='most_recent_lab', index_cols=[]):

    all_loincs = list()
    lab_case_statement = 'case ' 
    for lab, loinc in lonic_mapping.items():
        lab_case_statement += f'''when lab_loinc in ('{"','".join(loinc)}') then '{lab}'
        '''
        
        all_loincs += loinc

    lab_case_statement += '''else 'other' end as lab_type'''
    
    all_loincs = "','".join(all_loincs)


    q = f'''
        drop table if exists clean.{target_table_name};
        
        create table clean.{target_table_name} as (
            with base as (
                select
                c.entity_id,
                as_of_date,
                lab_loinc,
                specimen_date,
                avg(result_num) as result_num,
                {lab_case_statement}
                from labels_biopsy_1mo_074ad70e4c3298e002716406315bd56d c inner join clean.labs l 
                on c.entity_id = l.entity_id 
                and c.as_of_date > l.specimen_date 
                and lab_loinc in ('{all_loincs}')
                group by 1, 2, 3, 4
            )
            select distinct on (entity_id, as_of_date, lab_type)
                entity_id, as_of_date, specimen_date, lab_type, result_num, as_of_date - specimen_date as days_since_lab
            from base 
            order by entity_id, as_of_date, lab_type, specimen_date desc
        );
    '''
    
    with engine.begin() as conn:
        conn.execute(q)
        
    logging.info(f'Successfully created the clean.{target_table_name} table!')
        
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

    
    create_most_recent_lab_value_table(
        engine=engine,
        entity_date_table='labels_biopsy_1mo_074ad70e4c3298e002716406315bd56d',
        target_table_name='most_recent_labs_biopsy_cohort',
        lonic_mapping=lab_loinc_mapping,
        index_cols=['entity_id', 'as_of_date', 'specimen_date', 'lab_type']
    )