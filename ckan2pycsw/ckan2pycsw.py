# inbuilt libraries
import logging
import pathlib
import yaml
from urllib.parse import urljoin
import os
from datetime import datetime, time
import subprocess
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# third-party libraries
import psutil
import requests
import pycsw.core.config
from pycsw.core import admin, metadata, repository, util
from pycsw.core.repository import setup
from pygeometa.core import read_mcf
from pygeometa.schemas.iso19139 import ISO19139OutputSchema
from apscheduler.schedulers.blocking import BlockingScheduler

# custom functions
from config.log import log_file

# custom classes
from model.dataset import Dataset
from schemas.pygeometa.iso19139_inspire import ISO19139_inspireOutputSchema

# debug
import ptvsd

# Ennvars
TZ = os.environ.get("TZ", "TZ")
try:
    PYCSW_CRON_DAYS_INTERVAL = int(os.environ["PYCSW_CRON_DAYS_INTERVAL"])
except (KeyError, ValueError):
    PYCSW_CRON_DAYS_INTERVAL = 3
try:
    PYCSW_CRON_HOUR_START = int(os.environ["PYCSW_CRON_HOUR_START"])
except (KeyError, ValueError):
    PYCSW_CRON_HOUR_START = 4
method = "nightly"
CKAN_PYCSW_VERSION = os.environ.get("CKAN_PYCSW_VERSION", "1.0.0")
URL = os.environ.get("CKAN_URL", 'http://localhost:5000/')
PYCSW_PORT = os.environ.get("PYCSW_PORT", 8000)
PYCSW_SERVER_URL = os.environ.get("PYCSW_SERVER_URL", f'http://localhost:{PYCSW_PORT}')
PYCSW_URL = os.environ.get("PYCSW_URL", f'{PYCSW_SERVER_URL}/csw')
PYCSW_DEV_PORT = os.environ.get("PYCSW_DEV_PORT", 5678)
APP_DIR = os.environ.get("APP_DIR", "/srv/app")
CKAN_API = "api/3/action/package_search"
PYCSW_CKAN_SCHEMA = os.environ.get("PYCSW_CKAN_SCHEMA", "iso19139_geodcatap")
PYCSW_OUTPUT_SCHEMA = os.environ.get("PYCSW_OUTPUT_SCHEMA", "iso19139_inspire")
DEV_MODE = os.environ.get("DEV_MODE", False)
# pycsw 3.0: Use PYCSW_CONFIG environment variable (YAML configuration)
PYCSW_CONF = os.environ.get("PYCSW_CONFIG", f"{APP_DIR}/pycsw.yml")
MAPPINGS_FOLDER = "ckan2pycsw/mappings"
log_module = "[ckan2pycsw]"
OUPUT_SCHEMA = {
    "iso19139_inspire": ISO19139_inspireOutputSchema,
    "iso19139": ISO19139OutputSchema
}
SSL_UNVERIFIED_MODE = os.environ.get("SSL_UNVERIFIED_MODE", False)


session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_datasets(base_url):
    """
    Retrieve a generator of CKAN datasets from the specified CKAN instance.

    Parameters
    ----------
    base_url: str. The base URL of the CKAN instance.

    Returns
    -------
    generator: A generator that yields CKAN datasets.

    Raises
    ------
    requests.exceptions.RequestException: If an error occurs while communicating with the CKAN instance.
    """
    try:
        if not base_url.endswith("/"):
            base_url += "/"
            
        if SSL_UNVERIFIED_MODE in [True, "True"]:
            logging.warning(f"[INSECURE] SSL_UNVERIFIED_MODE:'{SSL_UNVERIFIED_MODE}'. Solo si confías en CKAN_URL: {base_url}.")  
            
        package_search = urljoin(base_url, "api/3/action/package_search")
        
        # Usar la sesión configurada con reintentos y timeout
        res = session.get(package_search, params={"rows": 0}, verify=not SSL_UNVERIFIED_MODE, timeout=10)
        res.raise_for_status()
        end = res.json().get("result", {}).get("count", 0)
        rows = 100  # Number of files
        for start in range(0, end, rows):
            logging.info(f"Fetching datasets with start={start} and rows={rows}")  # Log de progreso
            try:
                res = session.get(package_search, params={"start": start, "rows": rows}, verify=not SSL_UNVERIFIED_MODE, timeout=30)
                res.raise_for_status()
                datasets = res.json()["result"]["results"]
            except ValueError as e:
                logging.error(f"Error al decodificar JSON: {e}")
                continue
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {e}", exc_info=True)
                continue

            for dataset in datasets:
                if dataset.get("type") == "dataset":
                    yield dataset
    except requests.exceptions.Timeout:
        logging.error(f"Timeout error for request starting at {start}", exc_info=True)
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error for request starting at {start}", exc_info=True)
    except Exception as e:
        logging.error(f"Unexpected error at start={start}: {e}", exc_info=True)

def main():
    """
    Convert metadata from CKAN to ISO19139 and store the records in a pycsw endpoint.

    The function first sets up logging and reads the pycsw configuration from the specified file. It then checks if the pycsw database file exists and deletes it if it does.
    
    The database is then initialized using `pycsw.core.admin.setup_db()`. pycsw records are created and inserted into the database for each CKAN dataset that has a DCAT type of 'dataset', 'series', or 'service'.
    
    The records are created by rendering the CKAN metadata using a Jinja2 template and then transforming the resulting MCF dictionary into an XML string using a pycsw output schema.
    
    The function logs any errors that occur during this process and continues processing any remaining datasets.
    
    After all records have been inserted, the function exports them to the specified XML directory using
    `pycsw.core.admin.export_records()`.

    Returns
    -------
    None
    """
    log_file(APP_DIR + "/log")
    logging.info(f"{log_module}:ckan2pycsw | Version: {CKAN_PYCSW_VERSION}")
    
    # pycsw 3.0: Read YAML configuration instead of ConfigParser
    with open(PYCSW_CONF, 'r') as f:
        pycsw_config = yaml.safe_load(f)
    
    database_raw = pycsw_config['repository']['database']
    database = database_raw.replace("${PWD}", os.getcwd()) if DEV_MODE == "True" else database_raw
    table_name = pycsw_config['repository'].get('table', 'records')
    context = pycsw.core.config.StaticContext()

    # check if cite.db exists in folder, and delete it if it does
    database_path =  "/" + database.split("//")[-1]
    
    if pathlib.Path(database_path).exists():
        os.remove(database_path)
    # pycsw 3.0: setup_db moved to repository.setup
    setup(
        database,
        table_name,
    )

    repo = repository.Repository(database, context, table=table_name)

    dcat_type = [
         "dataset", 
         "series", 
         "service"
         ]
    
    # Only iterate over dataset if dataset["dcat_type"] in dcat_type
    for dataset in (d for d in get_datasets(URL) if d["dcat_type"].rsplit("/", 1)[-1] in dcat_type):
                # Add a counter of errors and valids datasets

                d_dcat_type = dataset["dcat_type"].rsplit("/", 1)[-1]
                logging.info(f"{log_module}:ckan2pycsw | Metadata: {dataset['name']} [DCAT Type: {d_dcat_type.capitalize()}]")
                try:
                    dataset_metadata =  Dataset(dataset_raw=dataset, base_url=URL, mappings_folder=MAPPINGS_FOLDER,  csw_schema=PYCSW_CKAN_SCHEMA)
                    mcf_dict = read_mcf(dataset_metadata.render_template)
                    
                    # Select an output schema based on OUPUT_SCHEMA if not exists use ISO19139
                    if PYCSW_OUTPUT_SCHEMA in OUPUT_SCHEMA:
                        iso_os = OUPUT_SCHEMA[PYCSW_OUTPUT_SCHEMA]()
                        xml_string = iso_os.write(mcf=mcf_dict, mappings_folder=MAPPINGS_FOLDER)
                    else:
                        iso_os = ISO19139OutputSchema()
                        xml_string = iso_os.write(mcf=mcf_dict)


                    #TODO: DELETE Dumps to log
                    #print(xml_string,  file=open(APP_DIR + "/log/demo.xml", "w", encoding="utf-8"))

                    # parse xml
                    record = metadata.parse_record(context, xml_string, repo)[0]
                    repo.insert(record, "local", util.get_today_and_now())
                except Exception as e:
                    logging.error(f"{log_module}:ckan2pycsw | Fail when transform record from CKAN for: {dataset['name']} [DCAT Type: {d_dcat_type.capitalize()}] Error: {e}")
                    continue

    logging.info(f"{log_module}:ckan2pycsw | Create a CSW Endpoint at: {PYCSW_URL}")

    # Export records to Folder
    # pycsw 3.0: export_records signature changed
    admin.export_records(
         context, 
         database, 
         table_name, 
         APP_DIR + "/metadata/")


def run_scheduler():
    """
    Schedule a recurring task to run at a specific time interval.

    The task will run every `PYCSW_CRON_DAYS_INTERVAL` days, starting at 4:00 a.m.
    The task consists of checking if a gunicorn process is running, killing it if necessary,
    running the `main()` function, and restarting gunicorn afterwards.

    Returns
    -------
    None
    """
    scheduler = BlockingScheduler(timezone=TZ)
    scheduler_start_date = datetime.now().replace(hour=PYCSW_CRON_HOUR_START, minute=0).strftime('%Y-%m-%d %H:%M:%S')
    scheduler.add_job(run_tasks, "interval", days=PYCSW_CRON_DAYS_INTERVAL, start_date=scheduler_start_date)
    scheduler.start()

def run_tasks():
    """
    Check if gunicorn is running. Kill any gunicorn process with "gunicorn" or "pycsw.wsgi_flask:APP" in its name or command line.
    Execute the main function. Restart gunicorn after the main function finishes.

    pycsw 3.0: Uses Flask-based wsgi_flask.py instead of wsgi.py
    - Default endpoint "/" is now OGC API - Records
    - CSW endpoint is now "/csw"
    - OAI-PMH endpoint is now "/oaipmh"
    - OpenSearch endpoint is now "/opensearch"
    - SRU endpoint is now "/sru"

    Returns
    -------
    None
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        if "gunicorn" in proc.info["name"] or "pycsw.wsgi_flask:APP" in ' '.join(proc.info["cmdline"]):
            print(f"Stopping gunicorn process with PID {proc.info['pid']}...")
            proc.kill()
            time.sleep(5)  # Wait for the gunicorn process to fully stop

    # Execute the main function
    main()

    # Restart gunicorn after the main function finishes
    # pycsw 3.0: Use Flask-based endpoint (wsgi_flask.py)
    try:
        subprocess.Popen(["pdm", "run", "python3", "-m", "gunicorn", "pycsw.wsgi_flask:APP", "-b", f"0.0.0.0:{PYCSW_PORT}"])
    except Exception as e:
        logging.error(f"{log_module}:ckan2pycsw | Error starting gunicorn: {e}")

if __name__ == "__main__":
    if str(DEV_MODE).lower() == "true":
        # Allow other computers to attach to ptvsd at this IP address and port.
        ptvsd.enable_attach(address=("0.0.0.0", PYCSW_DEV_PORT), redirect_output=True)

        # Pause the program until a remote debugger is attached
        ptvsd.wait_for_attach()
        main()
    # Launch a cronjob 
    else:
        run_tasks()
        run_scheduler()