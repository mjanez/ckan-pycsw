# inbuilt libraries
import logging
import pathlib
import yaml
from urllib.parse import urljoin
from typing import Generator, Dict, Any, Tuple, Optional, List
import os
from datetime import datetime, time
import subprocess
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import shutil
from collections import defaultdict

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


def get_datasets(base_url: str, dcat_types: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Retrieve a generator of CKAN datasets from the specified CKAN instance.

    Parameters
    ----------
    base_url : str
        The base URL of the CKAN instance.
    dcat_types : Optional[List[str]]
        List of DCAT types to filter (e.g., ['dataset', 'series', 'service']).
        If None, filters by type='dataset' only.

    Yields
    ------
    Dict[str, Any]
        CKAN dataset dictionary.

    Raises
    ------
    requests.exceptions.RequestException
        If an error occurs while communicating with the CKAN instance.
    """
    if not base_url.endswith("/"):
        base_url += "/"
        
    if SSL_UNVERIFIED_MODE in [True, "True"]:
        logging.warning(f"[INSECURE] SSL_UNVERIFIED_MODE:'{SSL_UNVERIFIED_MODE}'. Solo si confías en CKAN_URL: {base_url}.")  
        
    package_search = urljoin(base_url, "api/3/action/package_search")
    
    try:
        # Get total count
        res = session.get(package_search, params={"rows": 0}, verify=not SSL_UNVERIFIED_MODE, timeout=10)
        res.raise_for_status()
        total_count = res.json().get("result", {}).get("count", 0)
        
        if total_count == 0:
            logging.warning(f"{log_module}:get_datasets | No datasets found in CKAN instance")
            return
            
        logging.info(f"{log_module}:get_datasets | Found {total_count} total datasets in CKAN")
        
        rows = 100  # Batch size
        datasets_yielded = 0
        
        for start in range(0, total_count, rows):
            try:
                res = session.get(
                    package_search, 
                    params={"start": start, "rows": rows}, 
                    verify=not SSL_UNVERIFIED_MODE, 
                    timeout=30
                )
                res.raise_for_status()
                datasets = res.json()["result"]["results"]
                
                logging.debug(f"{log_module}:get_datasets | Fetched batch: start={start}, rows={rows}, received={len(datasets)}")
                
                for dataset in datasets:
                    # Filter by type and dcat_type
                    if dataset.get("type") != "dataset":
                        continue
                        
                    if dcat_types:
                        dcat_type = dataset.get("dcat_type", "").rsplit("/", 1)[-1]
                        if dcat_type not in dcat_types:
                            continue
                    
                    datasets_yielded += 1
                    yield dataset
                    
            except ValueError as e:
                logging.error(f"{log_module}:get_datasets | JSON decode error at start={start}: {e}")
                continue
            except requests.exceptions.RequestException as e:
                logging.error(f"{log_module}:get_datasets | Request error at start={start}: {e}", exc_info=True)
                continue
        
        logging.info(f"{log_module}:get_datasets | Yielded {datasets_yielded} datasets (filtered from {total_count} total)")
        
    except requests.exceptions.Timeout as e:
        logging.error(f"{log_module}:get_datasets | Timeout error: {e}", exc_info=True)
    except requests.exceptions.ConnectionError as e:
        logging.error(f"{log_module}:get_datasets | Connection error: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"{log_module}:get_datasets | Unexpected error: {e}", exc_info=True)

def transform_dataset_to_xml(
    dataset: Dict[str, Any], 
    base_url: str, 
    mappings_folder: str, 
    csw_schema: str, 
    output_schema: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Transform a CKAN dataset to ISO19139 XML string.

    Parameters
    ----------
    dataset : Dict[str, Any]
        CKAN dataset dictionary.
    base_url : str
        Base URL of the CKAN instance.
    mappings_folder : str
        Path to the mappings folder.
    csw_schema : str
        CSW schema to use (e.g., 'iso19139_geodcatap').
    output_schema : str
        Output schema to use (e.g., 'iso19139_inspire').

    Returns
    -------
    Tuple[Optional[str], Optional[str], Optional[str]]
        Tuple of (xml_string, dataset_id, dataset_name) or (None, id, name) on error.
    """
    try:
        dataset_id = dataset.get('id', 'unknown')
        dataset_name = dataset.get('name', 'unknown')
        dcat_type = dataset.get("dcat_type", "").rsplit("/", 1)[-1].capitalize()
        
        # Transform CKAN dataset to MCF
        dataset_metadata = Dataset(
            dataset_raw=dataset, 
            base_url=base_url, 
            mappings_folder=mappings_folder,  
            csw_schema=csw_schema
        )
        mcf_dict = read_mcf(dataset_metadata.render_template)
        
        # Select output schema
        if output_schema in OUPUT_SCHEMA:
            iso_os = OUPUT_SCHEMA[output_schema]()
            xml_string = iso_os.write(mcf=mcf_dict, mappings_folder=mappings_folder)
        else:
            logging.warning(f"{log_module}:transform_dataset | Unknown output schema '{output_schema}', using iso19139")
            iso_os = ISO19139OutputSchema()
            xml_string = iso_os.write(mcf=mcf_dict)
        
        return xml_string, dataset_id, dataset_name
        
    except Exception as e:
        import traceback
        dataset_id = dataset.get('id', 'unknown')
        dataset_name = dataset.get('name', 'unknown')
        dcat_type = dataset.get("dcat_type", "").rsplit("/", 1)[-1].capitalize()
        
        logging.error(
            f"{log_module}:transform_dataset | Failed to transform '{dataset_name}' "
            f"[ID: {dataset_id}] [DCAT Type: {dcat_type}] | Error: {e}"
        )
        logging.debug(f"{log_module}:transform_dataset | Traceback:\n{traceback.format_exc()}")
        
        return None, dataset_id, dataset_name


def save_xml_files(
    datasets: Generator[Dict[str, Any], None, None],
    metadata_dir: pathlib.Path,
    base_url: str,
    mappings_folder: str,
    csw_schema: str,
    output_schema: str,
    clean_dir: bool = False
) -> Dict[str, Any]:
    """
    Transform CKAN datasets to ISO19139 XML and save to metadata directory.

    Parameters
    ----------
    datasets : Generator[Dict[str, Any], None, None]
        Generator of CKAN datasets.
    metadata_dir : pathlib.Path
        Directory to save XML files.
    base_url : str
        Base URL of the CKAN instance.
    mappings_folder : str
        Path to the mappings folder.
    csw_schema : str
        CSW schema to use.
    output_schema : str
        Output schema to use.
    clean_dir : bool, optional
        Whether to clean the metadata directory before saving (default: False).

    Returns
    -------
    Dict[str, Any]
        Statistics dictionary with keys: 'success', 'failed', 'total', 'failed_ids'.
    """
    # Prepare metadata directory
    metadata_dir.mkdir(exist_ok=True)
    
    if clean_dir and metadata_dir.exists():
        logging.info(f"{log_module}:save_xml_files | Cleaning metadata directory: {metadata_dir}")
        # Remove only files, not the directory itself (may be mounted as volume)
        for item in metadata_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                logging.warning(f"{log_module}:save_xml_files | Failed to remove {item}: {e}")
    
    # Statistics
    stats = {
        'success': 0,
        'failed': 0,
        'total': 0,
        'failed_ids': [],
        'by_dcat_type': defaultdict(int)
    }
    
    logging.info(f"{log_module}:save_xml_files | Starting dataset transformation to ISO19139 XML")
    
    for dataset in datasets:
        stats['total'] += 1
        dataset_name = dataset.get('name', 'unknown')
        dataset_id = dataset.get('id', 'unknown')
        dcat_type = dataset.get("dcat_type", "").rsplit("/", 1)[-1].capitalize()
        
        logging.info(
            f"{log_module}:save_xml_files | [{stats['total']}] Processing '{dataset_name}' "
            f"[ID: {dataset_id}] [DCAT Type: {dcat_type}]"
        )
        
        # Transform to XML
        xml_string, xml_id, xml_name = transform_dataset_to_xml(
            dataset=dataset,
            base_url=base_url,
            mappings_folder=mappings_folder,
            csw_schema=csw_schema,
            output_schema=output_schema
        )
        
        if xml_string is None:
            stats['failed'] += 1
            stats['failed_ids'].append({'id': xml_id, 'name': xml_name})
            continue
        
        # Save XML to file
        try:
            xml_filename = f"{dataset_id}.xml"
            xml_filepath = metadata_dir / xml_filename
            
            with open(xml_filepath, "w", encoding="utf-8") as f:
                f.write(xml_string)
            
            stats['success'] += 1
            stats['by_dcat_type'][dcat_type] += 1
            
            logging.debug(f"{log_module}:save_xml_files | Saved XML to {xml_filepath}")
            
        except IOError as e:
            logging.error(f"{log_module}:save_xml_files | Failed to save XML for '{dataset_name}': {e}")
            stats['failed'] += 1
            stats['failed_ids'].append({'id': dataset_id, 'name': dataset_name})
    
    # Log summary
    logging.info(
        f"{log_module}:save_xml_files | Transformation complete: "
        f"{stats['success']} succeeded, {stats['failed']} failed, {stats['total']} total"
    )
    
    if stats['by_dcat_type']:
        dcat_summary = ", ".join([f"{k}: {v}" for k, v in stats['by_dcat_type'].items()])
        logging.info(f"{log_module}:save_xml_files | By DCAT Type: {dcat_summary}")
    
    if stats['failed_ids']:
        logging.warning(
            f"{log_module}:save_xml_files | Failed datasets: " +
            ", ".join([f"{item['name']} ({item['id']})" for item in stats['failed_ids'][:10]])
        )
        if len(stats['failed_ids']) > 10:
            logging.warning(f"{log_module}:save_xml_files | ... and {len(stats['failed_ids']) - 10} more")
    
    return stats


def load_xml_records(
    metadata_dir: pathlib.Path,
    context: pycsw.core.config.StaticContext,
    database: str,
    table_name: str
) -> Dict[str, Any]:
    """
    Load ISO19139 XML records from metadata directory into pycsw database.

    Parameters
    ----------
    metadata_dir : pathlib.Path
        Directory containing XML files to load.
    context : pycsw.core.config.StaticContext
        pycsw context object.
    database : str
        Database connection string.
    table_name : str
        Table name for records.

    Returns
    -------
    Dict[str, Any]
        Statistics dictionary with keys: 'loaded', 'failed', 'total'.
    """
    stats = {
        'loaded': 0,
        'failed': 0,
        'total': 0
    }
    
    if not metadata_dir.exists():
        logging.error(f"{log_module}:load_xml_records | Metadata directory does not exist: {metadata_dir}")
        return stats
    
    xml_files = list(metadata_dir.glob("*.xml"))
    
    if not xml_files:
        logging.warning(f"{log_module}:load_xml_records | No XML files found in {metadata_dir}")
        return stats
    
    stats['total'] = len(xml_files)
    
    logging.info(
        f"{log_module}:load_xml_records | Loading {stats['total']} records from {metadata_dir} "
        f"into database '{database}', table '{table_name}'"
    )
    
    try:
        # pycsw 3.0: load_records with force_update=True to overwrite existing records
        admin.load_records(
            context=context,
            database=database,
            table=table_name,
            xml_dirpath=str(metadata_dir),
            recursive=False,
            force_update=True
        )
        
        stats['loaded'] = stats['total']
        
        logging.info(
            f"{log_module}:load_xml_records | Successfully loaded {stats['loaded']} records into database"
        )
        
    except Exception as e:
        import traceback
        logging.error(f"{log_module}:load_xml_records | Failed to load records: {e}")
        logging.debug(f"{log_module}:load_xml_records | Traceback:\n{traceback.format_exc()}")
        stats['failed'] = stats['total']
        stats['loaded'] = 0
    
    return stats


def initialize_pycsw_database(
    pycsw_config: Dict[str, Any],
    dev_mode: bool = False
) -> Tuple[str, str, pycsw.core.config.StaticContext]:
    """
    Initialize pycsw database and return connection details.

    Parameters
    ----------
    pycsw_config : Dict[str, Any]
        pycsw configuration dictionary.
    dev_mode : bool, optional
        Whether running in development mode (default: False).

    Returns
    -------
    Tuple[str, str, pycsw.core.config.StaticContext]
        Tuple of (database, table_name, context).
    """
    database_raw = pycsw_config['repository']['database']
    database = database_raw.replace("${PWD}", os.getcwd()) if dev_mode else database_raw
    table_name = pycsw_config['repository'].get('table', 'records')
    context = pycsw.core.config.StaticContext()
    
    # Check and delete existing database
    database_path = "/" + database.split("//")[-1]
    
    if pathlib.Path(database_path).exists():
        logging.info(f"{log_module}:initialize_db | Removing existing database: {database_path}")
        os.remove(database_path)
    
    # Initialize database structure
    logging.info(f"{log_module}:initialize_db | Creating database: {database}")
    setup(database, table_name)
    
    return database, table_name, context


def main():
    """
    Convert metadata from CKAN to ISO19139 and store the records in a pycsw endpoint.

    This function orchestrates the complete workflow:
    1. Initialize logging and configuration
    2. Set up pycsw database
    3. Fetch datasets from CKAN
    4. Transform datasets to ISO19139 XML
    5. Load XML records into pycsw database

    The function uses modular helper functions for each step and provides
    comprehensive logging and statistics.

    Returns
    -------
    None
    """
    # Initialize logging
    log_file(APP_DIR + "/log")
    logging.info(f"{log_module}:main | ========================================")
    logging.info(f"{log_module}:main | ckan2pycsw Version: {CKAN_PYCSW_VERSION}")
    logging.info(f"{log_module}:main | ========================================")
    
    start_time = datetime.now()
    
    try:
        # Load pycsw configuration
        logging.info(f"{log_module}:main | Loading pycsw configuration from {PYCSW_CONF}")
        with open(PYCSW_CONF, 'r') as f:
            pycsw_config = yaml.safe_load(f)
        
        # Initialize database
        database, table_name, context = initialize_pycsw_database(
            pycsw_config=pycsw_config,
            dev_mode=(DEV_MODE == "True")
        )
        
        # Define DCAT types to process
        dcat_types = ["dataset", "series", "service"]
        
        logging.info(f"{log_module}:main | CKAN URL: {URL}")
        logging.info(f"{log_module}:main | CSW Schema: {PYCSW_CKAN_SCHEMA}")
        logging.info(f"{log_module}:main | Output Schema: {PYCSW_OUTPUT_SCHEMA}")
        logging.info(f"{log_module}:main | DCAT Types: {', '.join(dcat_types)}")
        
        # Step 1: Fetch datasets from CKAN
        logging.info(f"{log_module}:main | Step 1/3: Fetching datasets from CKAN")
        datasets_generator = get_datasets(base_url=URL, dcat_types=dcat_types)
        
        # Step 2: Transform datasets to XML and save to disk
        logging.info(f"{log_module}:main | Step 2/3: Transforming datasets to ISO19139 XML")
        metadata_dir = pathlib.Path(APP_DIR) / "metadata"
        
        transform_stats = save_xml_files(
            datasets=datasets_generator,
            metadata_dir=metadata_dir,
            base_url=URL,
            mappings_folder=MAPPINGS_FOLDER,
            csw_schema=PYCSW_CKAN_SCHEMA,
            output_schema=PYCSW_OUTPUT_SCHEMA,
            clean_dir=True  # Clean directory before saving new XMLs
        )
        
        # Step 3: Load XML records into pycsw database
        logging.info(f"{log_module}:main | Step 3/3: Loading XML records into pycsw database")
        
        if transform_stats['success'] > 0:
            load_stats = load_xml_records(
                metadata_dir=metadata_dir,
                context=context,
                database=database,
                table_name=table_name
            )
        else:
            logging.error(f"{log_module}:main | No XML files to load (transformation failed for all datasets)")
            load_stats = {'loaded': 0, 'failed': 0, 'total': 0}
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info(f"{log_module}:main | ========================================")
        logging.info(f"{log_module}:main | EXECUTION SUMMARY")
        logging.info(f"{log_module}:main | ========================================")
        logging.info(f"{log_module}:main | Duration: {duration:.2f} seconds")
        logging.info(f"{log_module}:main | Datasets processed: {transform_stats['total']}")
        logging.info(f"{log_module}:main | XML files created: {transform_stats['success']}")
        logging.info(f"{log_module}:main | Transformation failures: {transform_stats['failed']}")
        logging.info(f"{log_module}:main | Records loaded to database: {load_stats['loaded']}")
        logging.info(f"{log_module}:main | Loading failures: {load_stats['failed']}")
        logging.info(f"{log_module}:main | ========================================")
        logging.info(f"{log_module}:main | CSW Endpoint: {PYCSW_URL}")
        logging.info(f"{log_module}:main | OGC API - Records: {PYCSW_SERVER_URL}/")
        logging.info(f"{log_module}:main | ========================================")
        
        # Warning if there were failures
        if transform_stats['failed'] > 0 or load_stats['failed'] > 0:
            logging.warning(
                f"{log_module}:main | Process completed with errors. "
                f"Check logs for details."
            )
        else:
            logging.info(f"{log_module}:main | Process completed successfully!")
            
    except FileNotFoundError as e:
        logging.error(f"{log_module}:main | Configuration file not found: {e}")
        raise
    except Exception as e:
        import traceback
        logging.error(f"{log_module}:main | Fatal error during execution: {e}")
        logging.error(f"{log_module}:main | Traceback:\n{traceback.format_exc()}")
        raise


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
    else:
        # Launch a cronjob 
        run_tasks()
        run_scheduler()
