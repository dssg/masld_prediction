import os 
import yaml
import sqlalchemy

def read_yaml(yaml_file):
    """ load yaml cofigurations """

    config = None
    try: 
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.scanner.ScannerError) as e:
        raise e
    
    return config

def get_db_engine(database_creds=None, service=None):
    """ Get an authenticated db connection, given a credentials file 
        or with environmental variables     

        Args:
            database_creds: Path to the database.yaml file
            conn_type: Whether the connection is psycopg2 or sqlalchemy. 
                Defaults to psycopg2 (any other text would result in a sqlalchemy engine)
                For triage, sqlalchemy engines are useful
    """

    if service is not None:
        return sqlalchemy.create_engine(f"postgresql:///?service={service}")

    if database_creds is None:
        user = os.getenv("PGUSER")
        password = os.getenv("PGPASSWORD")
        host = os.getenv("PGHOST")
        port = os.getenv("PGPORT")
        database = os.getenv("PGDATABASE")

    else:
        creds = read_yaml(database_creds)
        user = creds['user']
        password = creds['pass']
        host = creds['host']
        port = creds['port']
        database = creds['db']

    
    poolclass=sqlalchemy.pool.QueuePool
    dburl = sqlalchemy.engine.url.URL(
        "postgres",
        host=host,
        username=user,
        database=database,
        password=password,
        port=port,
    )

    return sqlalchemy.create_engine(dburl, poolclass=poolclass)