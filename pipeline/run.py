import argparse
import logging
import yaml
import json
import datetime
import os

from triage.experiments import MultiCoreExperiment
from triage.experiments import SingleThreadedExperiment
from triage import create_engine

from sqlalchemy.event import listens_for
from sqlalchemy.pool import Pool
from sqlalchemy.engine.url import URL


def run(config_filename, verbose, replace, predictions, validate_only, sampledb, usefeatureconfigdir):
    # configure logging
    # add logging to a file (it will also go to stdout via triage logging config)
    log_filename = os.path.join(PROJECT_PATH, 'triage_alc.log')
    logger = logging.getLogger('')
    hdlr = logging.FileHandler(log_filename)
    #hdlr.setLevel(15)   # verbose level
    hdlr.setLevel(logging.SPAM)
    hdlr.setFormatter(logging.Formatter('%(name)-30s  %(asctime)s %(levelname)10s %(process)6d  %(filename)-24s  %(lineno)4d: %(message)s', '%d/%m/%Y %I:%M:%S %p'))
    logger.addHandler(hdlr)


    # load main experiment config
    print("Reading:"+str(config_filename))
    with open('{}.yaml'.format(config_filename)) as f:
        experiment_config = yaml.full_load(f)
        
 

    if usefeatureconfigdir:
        feature_group_files = os.listdir(usefeatureconfigdir)
        feature_aggs = list()
        
        logger.info('Reading feature definitions from separate configs')
        for fg in feature_group_files:      
            logger.info(f'Feature group: {fg}')
            with open(f'{usefeatureconfigdir}/{fg}') as f:
                d = yaml.full_load(f)
                feature_aggs.append(d)

        experiment_config['feature_aggregations'] = feature_aggs
            
    keepalive_kwargs = {
    "keepalives": 1,
    "keepalives_idle": 200,
    "keepalives_interval": 10,
    "keepalives_count": 15,
    }

    if sampledb:
        dbconfigfile='sampledb.yaml'
    else:
        dbconfigfile='db.yaml'    
    
    with open(dbconfigfile, 'r') as file:
        dbconfig = yaml.safe_load(file)


    db_url = URL(
              'postgres',
              host=dbconfig['host'],
              username=dbconfig['user'],
              database=dbconfig['db'],
              password=dbconfig['pass'],
              port=dbconfig['port'],
          )

    db_engine = create_engine(db_url, pool_pre_ping=True)


    experiment = MultiCoreExperiment(
        config=experiment_config,
        db_engine=db_engine,
        project_path=PROJECT_PATH,
        replace=replace,
        # create matrix settings
        # n_db_processes=2,
        # n_processes=2,
        # n_bigtrain_processes=1,
        # modeling settings
        n_db_processes=3,
        n_processes=1,
        n_bigtrain_processes=1,
        save_predictions=predictions,
    )

    # experiment = SingleThreadedExperiment(
    #     config=experiment_config,
    #     db_engine=db_engine,
    #     project_path=PROJECT_PATH,
    #     replace=replace,
    #     save_predictions=predictions,
    # )

    
#    experiment.validate()
    if not validate_only:
        experiment.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run triage pipeline')

    parser.add_argument(
        "-c",
        "--config_filename",
        type=str,
        help="Pass the config filename"
    )

    parser.add_argument("-v", "--verbose", help="Enable debug logging",
                        action="store_true")

    parser.add_argument(
        "-r",
        "--replace",
        help="If this flag is set, triage will overwrite existing models, matrices, and results",
        action="store_true"
    )
    parser.add_argument(
        "-p",
        "--predictions",
        help="If this flag is set, triage will write predictions to the database",
        action="store_true"
    )
    parser.add_argument(
        "-a",
        "--validateonly",
        help="If this flag is set, triage will only validate",
        action="store_true"
    )

    parser.add_argument(
        "-s",
        "--sampledb",
        help="If this flag is set, triage will only run on the sample",
        action="store_true"
    )

    parser.add_argument(
        "-f",
        "--usefeatureconfigdir",
        help="If this flag is set, triage will use feature config file directory instead of main config file",
        type=str
    )


    args = parser.parse_args()

    if args.sampledb:
        PROJECT_PATH = '/nafld-data/project/nash_nafld/sampledb_dir/'
    else:
        PROJECT_PATH = '/nafld-data/project/nash_nafld/'

    run(args.config_filename, args.verbose, args.replace, args.predictions, args.validateonly, args.sampledb,args.usefeatureconfigdir)