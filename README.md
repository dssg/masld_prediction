# MASLD Risk Prediction Project

# Early Warning Tool for prioritizing individuals for screenings based on risk of MASLD related liver complications)

## Documentation
[Documentation of steps and code](documentation.md)


## Formulation
For every patient 
1. who has *had at least one clinical visit* in the past 3 years
2. is 18+ years of age (and alive)
3. has not been diagnosed yet with MASLD related liver_complications or hepatitis or alcohol related or other liver complications

Predict the top k individuals (based on intervention capacity) who are at risk of having MASLD related liver complications in the *next 3 years*


## Analysis to be done
- Predict risk of having MASLD related liver complications in the next 3 years
- Define Baselines:
     - age, most recent fib4, co-morbidities
     - clinical guidelines - t2dm, obesity, high tg, glucose, hdl, bp, ast or alt
- Metric(s):
   - Primary: Precision (PPV) or Recall (sensitivity) at top k (
     [!WARNING]
     need to determine k based on capacity)
   - AUC (if capacity is TBD)
- Fairness metric: TPR disparity by Race, Gender

## Methodology
1. **Define cohort based on formulation**: All patients > 18 years, at least one outpatient visit in the past 3 years, no previous diagnosis of liver-related complications or other liver-related diagnosis exclusions. [sql file used in config](triage_config_files/cohort_label_query_CTE.sql)
2. **Define Outcome/Label based on formulation (will get diagnosed with X in the next z months)**:  Liver complications (defined as development of cirrhosis or liver-related complications) developed in the next 3 years following prediction date [sql file used in config](triage_config_files/cohort_label_query_CTE.sql)
3. **Define Training and Validation sets over time** 
4. **Define and generate predictors**: All features defined in [these config files](triage_config_files
/feature_groups/)
5. **Train Models on each training set and score all patients in the corresponding validation set** 
6. **Evaluate all models for each validation time according to each metric (PPV at top k)**
7. **Select "Best" model based on results over time**
8. **Explore the high performing models to understand who they rank high, how they compare to the cohort, and important predictors**
9. **Check and/or correct for bias issues**

## Triage background
We are using [Triage](https://github.com/dssg/triage) to build and select models. Some background and tutorials on Triage:
- [Tutorial on Google Colab](https://colab.research.google.com/github/dssg/triage/blob/master/example/colab/colab_triage.ipynb) - Are you completely new to Triage? Run through a quick tutorial hosted on google colab (no setup necessary) to see what triage can do!
- [Dirty Duck Tutorial](https://dssg.github.io/triage/dirtyduck/) - Want a more in-depth walk through of triage's functionality and concepts? Go through the dirty duck tutorial here with sample data
- [QuickStart Guide](https://dssg.github.io/triage/quickstart/) - Try Triage out with your own project and data
- [Suggested workflow](https://dssg.github.io/triage/triage_project_workflow/)
- [Understanding the configuration file](https://dssg.github.io/triage/experiments/experiment-config/#experiment-configuration)
- Installation: install triage in a python virtual environment

## Running models and triage
Assuming Triage is installed and the data is in a postgres database. To run,
1. activate virtual environment source env/bin/activate
2. python run.py -c configfilename
   - if running on sample database add --sampledb flag
   
**Triage running - choices to Make**
1. replace flag (set to false until we want to nuke everything)
2. save predictions (don't for the beginning)
3. number of processors to use

## Config files, Model Selection, and Bias Analysis 

### current config file
1. The current one is [here](triage_config_files/c3y_l3y_upd1y_asof1y_nofeatures_nomodels.yaml)
2. File with design choices: [google doc](https://docs.google.com/spreadsheets/d/1DQU7vKe4vfZpDn5JPFf7yCaRJwSQR197hkte_gQ6QFc/edit#gid=724583270)
### Config file choices to make: [example config file](https://github.com/dssg/triage/blob/master/example/config/experiment.yaml)
1. cohort and label query: need to write a query that takes two parameters {as_of_date} and {label_timespan} and returns data in two columns (entity_id, outcome) specifying all the patients in the cohort as of {as_of_date} and outcomes can be 1 (got diagnosed with NASH/NAFLD related liver complications within the time period {label_timespan) from the {as_of_date}, 0 (did not get diagnosed), null (don't know or not sure). We can later turn nulls into 0s or ignore them. 
3. temporal config parameters
4. features and imputation
5. subsets to analyze: prior NASH or NAFLD diagnosis
7. attributes to do bias audits for: sex, race

## FIB-4 related analysis
1. Of all the patients who have FIB-4 components, how many should be in our cohort (don't have nash/nafld related complications yet), and what % of them end up having them in the next 3 years?

## Variations Tested
The following feature sets were tested using [manual_modeling.py](pipeline/manual_modeling.py). Takes 4 parameters:
 - training matrix
 - test matrix
 - model to build and test
 - feature set

### All Features

### Only using features for 12 months and all history (without 1,3,6 month features)

### based on guidelines only

### without liver-related labs and diagnosis

### using top x features from the xgboost model


