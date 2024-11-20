# Documentation of the Process and Code
## ETL
 - what did we get and where is it
 - what did we do to it
 - how did we load it into the db
 - what additional tables did we create
 - what indices did we create
 - where are the files and how to run etl again?
 - biopsy data load
   ```
   python load_biopsy_data.py ../../../../misc/notes_labeled_11DEC23.csv biopsy_labels postgres://username:password@nashdb.dssg.io:5432/popsdb
   ```

The raw data were given to us in the form of 9 CSV files. We followed the following steps to load and clean the data to be used in the analysis. 

**Step 1: Copy CSVs to the database as is.** We created 9 tables (one for each CSV file) in a database schema named `staging` and copied the contents of the CSVs to their respective tables without any changes. To preserve the data in its rawest form possible, we keep all the datatypes to be `VARCHAR/TEXT`. 
- We use a Python script to programmatically create the staging tables using the structure of the CSV - `etl/creating_staging_tables.py`
- Then, we use a Shell script to copy CSV content into the staging tables - `etl/upload_csvs_to_db.sql`

```
$ python etl/creating_staging_tables.py
$ psql -f etl/upload_csvs_to_db.sql
```

**Step 2: Add appropriate data types.** Once the data is uploaded to the DB, we assign appropriate datatypes to the columns of the data tables and create an intermediate schema `raw`. 
- We use a SQL script to create and populate the tables with the appropriate data types (from `staging`) - `etl/raw/raw_tables.sql`

```
$ psql -f etl/raw/raw_tables.sql
```


**Step 3: Clean data with integer ids and indexes.** Our modeling pipeline requires patients in the cohorts to be identified with integer IDs, and the patient ID included in the raw data is an alphanumeric string. In this stage, we create a table that maps the alphanumerics IDs to integers and add that integer ID to all the data tables. Further, we add index the data tables by the appropriate columns to improve the performance of our SQL queries. The cleaned and indexed table are stored in the `clean` schema. This schema is used as the base for all analyses.  
- SQL script for creating the integer ID mapping - `etl/create_entity_id_mapping.sql`
- SQL script for creating the clean schema tables with indexes and integer IDs - `etl/clean/create_clean_tables.sql`

```
$ psql -f etl/create_entity_id_mapping.sql
$ psql -f etl/clean/create_clean_tables.sql
```

**Step 4: Create helper tables for data analyses.**
We create a set of tables based off of the data in the `clean` schema to support our analyses. The table and the location of the script used to create table table are given below. All the scripts are in `etl/helper/` folder. 
- exclusion dates for patients in cohorts `first_exclusion_date.sql`
- BMI tables `create_bmi_tables.sql`
- FIb4 tables `create_fib4_table.sql`
- Prescription helper table `create_prescribing_helper_table.py`



## EDA
 - queries
 - notebooks
      - [notebook](misc/eda.ipynb)

## Triage files
 - run.py
   ```
   python run.py -c ../triage_config_files/c3y_l3y_upd1y_asof1y_incalc_12m_all_features -f ../triage_config_files/feature_groups_12m_all_only/
   ```
   ```
   python run_pieces.py -c ../triage_config_files/c3y_l3y_upd1y_asof1y_incalc_12m_all_features -f ../triage_config_files/feature_groups_12m_all_only/
   ```
 - config files
 - save predictions: python save_predictions.py -c predictions.yaml -d db.yaml

## Non-triage ML models (called manual models)

 **manual modeling files - model runs, results**
```
python manual_modeling.py --train_matrix f258357f1f7b3f855d16963117c1ed8c --test_matrix 20793ed2d7e5b00be7d2f57e78efef92 -m DT2 --only_use_base_guideline_features_with_age_race;
```

**Bias analysis for manual models** 
Currently lives in a notebook `notebooks/manual_modeling_predictions.ipynb`. 
__TODO__ - This needs better documentation, and probably should move to a .py script


## Guidelines based prioritization (baseline)

**Guideline Model Creation and Results**
We use the triage built features to calculate the guideline models. We use the `.sql` file `baselines/guidelines_table_using_features_fixed.sql`. The existence of guidelines in patients is stored in `anaysis.guideline_conditions_past_all_fixed`. 

The evaluations of the different guideline combination models is calculated using `baselines/run_guideline_performance.py`. The evaluation results are stored in `analysis.guideline_condition_results_fixed`.

__TODO__ Should remove the depracated sql and the related database table. Then update the name of the `_fixed` file and the related db table 

**Bias analysis of guideline models**
Currently the code lives in the notebook at `notebooks/guideline_features_bias.ipynb`. The results are saved to `analysis.guideline_models_bias`. 

__TODO__ The current bias analysis is related to the old guidelines table. So, need to do the following: (1) convert the notebook into a .py script, (2) re-run for the 'fixed' version of the guidelines and store the results on the database


## Post-modeling files
- notebooks
- tableau 

## code and/or excel files used for the report
- on drive
- in repo

## Queries used to different analysis


# Log

1. loaded data into clean schema
2. created augmented columns (ccsr category), helper tables, and pre-computed most recent type features.
3. modeling
 - all features


