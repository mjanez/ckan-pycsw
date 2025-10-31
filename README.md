<h1 align="center">pycsw CKAN harvester ISO19139</h1>
<p align="center">
<a href="https://github.dev/mjanez/ckan-pycsw"><img src="https://img.shields.io/badge/%20pycsw-2.6.1-brightgreen" alt="pycsw ersion"></a><a href="https://opensource.org/licenses/MIT"> <img src="https://img.shields.io/badge/license-Unlicense-brightgreen" alt="License: Unlicense"></a> <a href="https://github.com/mjanez/ckan-pycsw/actions/workflows/docker/badge.svg" alt="License: Unlicense"></a>


<p align="center">
    <a href="#overview">Overview</a> •
    <a href="#containers">Containers</a> •
    <a href="#quick-start">Quick start</a> •
    <a href="#schema-development">Schema development</a> •
    <a href="#test">Test</a> •
    <a href="#debug">Debug</a>
</p>

**Requirements**:
* [Docker](https://docs.docker.com/get-docker/)

## Overview
Docker compose environment (based on [pycsw](https://github.com/geopython/pycsw)) for development and testing with CKAN Open Data portals.[^1]

> [!TIP]
> It can be easily tested with a CKAN-type Open Data portal deployment: [mjanez/ckan-docker](https://github.com/mjanez/ckan-docker)[^2].

Available components:
* **pycsw**: The pycsw app. An [OARec](https://ogcapi.ogc.org/records) and [OGC CSW](https://opengeospatial.org/standards/cat) server implementation written in Python.
* **ckan2pycsw**: Software to achieve interoperability with the open data portals based on CKAN. To do this, `ckan2pycsw` reads data from an instance using the CKAN API, generates INSPIRE ISO-19115/ISO-19139 [^3] metadata using [pygeometa](https://geopython.github.io/pygeometa/), or another custom schema, and populates a [pycsw](https://pycsw.org/) instance that exposes the metadata using CSW and OAI-PMH.

## Containers
List of *containers*:
* [ckan-pycsw](ckan-pycsw/README.md)

#### Built images
| Repository | pycsw version | Type | Docker tag | Size | Notes |
| --- | --- | --- | --- | --- | --- |
| ckan-pycsw | 3.0-dev | base image | `mjanez/ckan-pycsw:latest` | ~535 MB | Development & test latest version |
| ckan-pycsw | 3.0-dev | base image | `mjanez/ckan-pycsw:3.0-dev` | ~535 MB | Last stable release according to [pycsw master (3.0-dev)](https://github.com/geopython/pycsw/tree/master) |
| ckan-pycsw | 2.6.2 | base image | `mjanez/ckan-pycsw:2.6.2` | ~346 MB | Last stable release according to [pycsw 2.6.2](https://github.com/geopython/pycsw/tree/2.6.2) |
| ckan-pycsw | 2.6.1 | base image | `mjanez/ckan-pycsw:2.6.1` | ~346 MB | Stable release according to [pycsw 2.6.1](https://github.com/geopython/pycsw/tree/2.6.1) |
| ckan-pycsw | 2.6.1 | base image | `mjanez/ckan-pycsw:main` | ~442 MB | Deprecated and only maintained for legacy systems (pin to version `ckan-pycsw:2.6.1`). |

#### Base images
| Repository | Type | Docker tag | Size | Notes |
| --- | --- | --- | --- | --- |
| Python | base image | `python:3.11-slim-bullseye` | ~45 MB | Slim variant for reduced footprint |

> [!NOTE]
> GHCR and Dev `Dockerfiles` using latest stable tag images as base.

### Network ports settings
| Ports | Container |
| --- | --- |
| 0.0.0.0:8000->8000/tcp | pycsw |
| 0.0.0.0:5678->5678/tcp | ckan-pycsw debug (debugpy) |

## Quick start
### With docker compose
Copy the `.env.example` template and configure by changing the `.env` file. Configure the following variables:

- `PYCSW_SERVER_URL`: Base server URL for pycsw configuration (e.g., `http://localhost:8000`)
- `CKAN_URL`: Your CKAN instance URL
- `PYCSW_PORT`: Published port for pycsw service

```shell
cp .env.example .env
```

>**Note**
> In pycsw 3.0, `PYCSW_SERVER_URL` is used for server configuration (`server.url` in `pycsw.yml`), while `PYCSW_URL` points to the CSW endpoint (`/csw`) for client requests.

Select the CKAN Schema (`PYCSW_CKAN_SCHEMA`), and the pycsw output schema (`PYCSW_OUTPUT_SCHEMA`):

- Default: 
    ```ini
    PYCSW_CKAN_SCHEMA=iso19139_geodcatap
    PYCSW_OUTPUT_SCHEMA=iso19139_inspire

    ...

    SSL_UNVERIFIED_MODE=True
    ```
- Avalaible:
  * CKAN metadata schema (`PYCSW_CKAN_SCHEMA`):
    * `iso19139_geodcatap`, **default**: [WIP] Schema based on [GeoDCAT-AP custom dataset schema](https://github.com/mjanez/ckanext-scheming).
    * `iso19139_base`: [WIP] Base schema.

  * pycsw metadata schema (`PYCSW_OUTPUT_SCHEMA`):
    * `iso19139_inspire`, **default**: Customised schema based on ISO 19139 INSPIRE metadata schema. [^4]
    * `iso19139`: Standard pycsw schema based on ISO 19139.

Change `SSL_UNVERIFIED_MODE` to avoid SSL errors when using a self-signed certificate in CKAN `development`. 

- Default: 
    ```ini
    SSL_UNVERIFIED_MODE=True
    ```
> [!WARNING] 
> Enabling `SSL_UNVERIFIED_MODE` can expose your application to security risks by allowing unverified SSL certificates. Use this setting only in a trusted development environment and never in production.

To deploy the environment, `docker compose` will build the latest source in the repo.

If you can deploy a `5 minutes` image, use the stable image ([`ghcr.io/mjanez/ckan-pycsw:main`](https://github.com/mjanez/ckan-pycsw/pkgs/container/ckan-pycsw)) with [`docker-compose.ghcr.yml`](/docker-compose.ghcr.yml)

```bash
git clone https://github.com/mjanez/ckan-pycsw
cd ckan-pycsw

docker compose up --build

# Github main registry image
docker compose -f docker-compose.ghcr.yml --build

# Or detached mode
docker compose up -d --build
```

> [!TIP]
> Deploy the dev (multistage build) `docker-compose.dev.yml` with:
>
>```bash
> docker compose -f docker-compose.dev.yml up --build
>```
>
>If needed, to build a specific container simply run:
>
>```bash
>  docker build -t target_name xxxx/
>```


### Without Docker
Requirements:
- `>=` [Python 3.9](./pyproject.toml)

Dependencies:
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath --force

# You will need to open a new terminal or re-login for the PATH changes to take effect.
pipx install pdm
pdm install --no-self
```

Configuration:
```bash
# pycsw 3.0 uses YAML configuration
# PYCSW_SERVER_URL is the server base (no /csw), PYCSW_URL is the CSW endpoint
PYCSW_SERVER_URL=http://localhost:8000 PYCSW_URL=http://localhost:8000/csw envsubst < ckan-pycsw/conf/pycsw.yml.template > pycsw.yml

# Or update pycsw.yml vars manually
vi pycsw.yml
```

Generate database and add:
```bash
rm -f cite.db

# Remember create and update .env vars. Next add to .env environment:
bash doc/scripts/00_ennvars.sh
```

Run ckan2pycsw:
```bash
PYCSW_CONFIG=pycsw.yml pdm run python3 ckan2pycsw/ckan2pycsw.py
```

## Schema development
User-defined metadata schemas can be added, both for CKAN metadata input: `ckan2pycsw/schemas/ckan/*` and for output schemas in pycsw: `ckan2pycsw/schemas/pygeometa/*`.

### New input Metadata schema (CKAN)
You can customise and extend the metadata schemas that serve as templates to import as many metadata elements as possible from a custom schema into CKAN. e.g. Based on a custom schema from [`ckanext-scheming`](https://github.com/ckan/ckanext-scheming).

#### Sample workflow
1. Create a new folder in [`schemas/ckan/`](./ckan2pycsw/schemas/pygeometa/) with the name intended for the schema. e.g. `iso19139_spain`.

2. Create the `main.j2` with the Jinja template to render the metadata.Examples in: [`schemas/ckan/iso19139_geodcatap](/ckan2pycsw/schemas/ckan/iso19139_geodcatap/)

3. Add all needed mappings (`.yaml`) to a new folder in [`ckan2pycsw/mappings/`](./ckan2pycsw/mappings/). e.g. `iso19139_spain`

4. Update [`ckan2pycsw/mappings/ckan-pycsw_assigments.yaml`](/ckan2pycsw/mappings/ckan-pycsw_assigments.yaml) to include the pycsw and ckan schema mapping. e.g.
    ```yaml
    iso19139_geodcatap: ckan_geodcatap
    iso19139_base: ckan_base
    iso19139_inspire: inspire
    ...
    iso19139_spain: iso19139_spain
    ```

5. Modify `.env` to select the new `PYCSW_CKAN_SCHEMA`:

    ```ini
    PYCSW_CKAN_SCHEMA=iso19139_spain
    PYCSW_OUTPUT_SCHEMA=iso19139
    ```


### New ouput CSW Metadata schema (pycsw/pygeometa)
New metadata schemas can be extended or added to convert elements extracted from CKAN into standard metadata profiles that can be exposed in the pycsw CSW Catalogue.

#### Sample workflow
1. Create a new folder in [`schemas/pygeometa/`](./ckan2pycsw/schemas/pygeometa/) with the name intended for the schema. e.g. `iso19139_spain`.

2. Add a `__init__.py` file with the extended pygeometa schema class. e.g. 
    ```python
    import ast
    import logging
    import os
    from typing import Union

    from lxml import etree
    from owslib.iso import CI_OnlineResource, CI_ResponsibleParty, MD_Metadata

    from pygeometa.schemas.base import BaseOutputSchema
    from model.template import render_j2_template

    LOGGER = logging.getLogger(__name__)
    THISDIR = os.path.dirname(os.path.realpath(__file__))


    class ISO19139_spainOutputSchema(BaseOutputSchema):
        """ISO 19139 - Spain output schema"""

        def __init__(self):
            """
            Initialize object

            :returns: pygeometa.schemas.base.BaseOutputSchema
            """

            super().__init__('iso19139_spain', 'xml', THISDIR)
    ...
    ```

3. Create the `main.j2` with the Jinja template to render the metadata, macros can be added for more specific templates, for example: `iso19139_inspire-regulation.j2`, or `contact.j2`, more examples in: [`schemas/pygeometa/iso19139_inspire`](./ckan2pycsw/schemas/iso19139_inspire)

4. Add the Python class and the schema identifier to [`ckan2pycsw.py`](./ckan2pycsw/ckan2pycsw.py), e.g.
    ```python

    from schemas.pygeometa.iso19139_inspire import ISO19139_inspireOutputSchema, ISO19139_spainOutputSchema

    ...

    OUPUT_SCHEMA = {
        'iso19139_inspire': ISO19139_inspireOutputSchema,
        'iso19139': ISO19139OutputSchema,
        'iso19139_spain: ISO19139_spainOutputSchema
    }
    ```

5. Add all mappings (`.yaml`) to a new folder in [`ckan2pycsw/mappings/`](./ckan2pycsw/mappings/). e.g. `iso19139_spain`

6. Update [`ckan2pycsw/mappings/ckan-pycsw_assigments.yaml`](/ckan2pycsw/mappings/ckan-pycsw_assigments.yaml) to include the pycsw and ckan schema mapping. e.g.
    ```yaml
    iso19139_geodcatap: ckan_geodcatap
    iso19139_base: ckan_base
    iso19139_inspire: inspire
    ...
    iso19139_spain: iso19139_spain
    ```

7. Modify `.env` to select the new `PYCSW_OUTPUT_SCHEMA`:

    ```ini
    PYCSW_CKAN_SCHEMA=iso19139_geodcatap
    PYCSW_OUTPUT_SCHEMA=iso19139_spain
    ```

## Test
### Automated Testing
The project includes a comprehensive test suite using pytest. Tests validate:

- CKAN to ISO19139 XML transformation
- pycsw 3.0 compatibility with OWSLib ≥0.29.0
- None value handling in Service datasets
- All DCAT types (Dataset, Series, Service)

#### Run tests with Docker (Recommended)
```bash
# Run all tests in isolated environment
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

#### Run tests with PDM (Development)
```bash
cd ckan-pycsw

# Install dev dependencies
pdm install -d

# Run all tests
pdm run pytest tests/ -v

# Run with coverage
pdm run pytest tests/ --cov=ckan2pycsw --cov-report=html
```

For detailed testing documentation, see [`tests/README.md`](tests/README.md).

### pycsw 3.0 Endpoints
pycsw 3.0 provides multiple API endpoints:

- **OGC API - Records** (default): `http://localhost:8000/`
- **CSW 2.0/3.0**: `http://localhost:8000/csw`
- **OAI-PMH**: `http://localhost:8000/oaipmh`
- **OpenSearch**: `http://localhost:8000/opensearch`
- **SRU**: `http://localhost:8000/sru`

>**Note**
> `PYCSW_URL` is configured to point to the CSW endpoint (`/csw`) by default, as it's the primary endpoint for catalog services.

### CSW GetRecords Request
Perform a `GetRecords` request and return all:

    {PYCSW_URL}?request=GetRecords&service=CSW&version=3.0.0&typeNames=gmd:MD_Metadata&outputSchema=http://www.isotc211.org/2005/gmd&elementSetName=full


- The `ckan-pycsw` logs will be created in the [`/log`](/log/) folder.
- Metadata records in `XML` format ([ISO 19139](https://www.iso.org/standard/67253.html)) are stored in the [`/metadata`](/metadata/) folder.

>**Note**
> The `GetRecords` operation allows clients to discover resources (datasets). The response is an `XML` document and the output schema can be specified.

## Debug
### VSCode with debugpy
The development environment uses **debugpy** (Microsoft's Python debugger) for remote debugging.

#### Python debugger with Docker (Remote Attach)
1. Build and run dev container:

    ```bash
    docker compose -f docker-compose.dev.yml up -d --build
    ```

2. In VS Code, use the **"Python: Remote Attach (debugpy)"** configuration (`.vscode/launch.json`):
   - Connects to `localhost:5678`
   - Path mappings configured for `/srv/app/ckan2pycsw`

3. Set breakpoints in your code and start debugging

4. The container will wait for debugger to attach before running

> [!NOTE]
> We upgraded from deprecated `ptvsd` to `debugpy` for better compatibility and performance.

#### Python debugger without Docker (Local)
1. Install dev dependencies:
   ```bash
   cd ckan-pycsw
   pdm install -d
   ```

2. Use one of these VS Code debug configurations:
   - **"Python: Current File"**: Debug the active Python file
   - **"Python: Pytest Current File"**: Debug tests in active file
   - **"Python: Pytest All Tests"**: Debug all tests

3. Set breakpoints and press F5 to start debugging

> [!NOTE]
> By default, the Python extension looks for and loads a file named `.env` in the current workspace folder. More info about Python debugger and [Environment variables use](https://code.visualstudio.com/docs/python/environments#_environment-variables).

### Debugging Configuration
VS Code launch configurations are provided in `.vscode/launch.json`:

- **Remote Attach**: Attach to Docker container debugger (port 5678)
- **Current File**: Debug any Python file locally
- **Pytest Current File**: Debug tests in active file
- **Pytest All Tests**: Debug entire test suite

For detailed debugging information, see [`tests/README.md`](tests/README.md).


[^1]: Extends the @frafra [coat2pycsw](https://github.com/COATnor/coat2pycsw) package.
[^2]: A custom installation of Docker Compose with specific extensions for spatial data and [GeoDCAT-AP](https://github.com/SEMICeu/GeoDCAT-AP)/[INSPIRE](https://github.com/INSPIRE-MIF/technical-guidelines) metadata [profiles](https://en.wikipedia.org/wiki/Geospatial_metadata).
[^3]: [INSPIRE dataset and service metadata](https://inspire.ec.europa.eu/id/document/tg/metadata-iso19139) based on ISO/TS 19139:2007. 
[^4]: The output pycsw schema (`iso19139_inspire`), to comply with INSPIRE ISO 19139 is WIP. The validation of the dataset/series is complete and conforms to the [INSPIRE reference validator](https://inspire.ec.europa.eu/validator/home/index.html) datasets and dataset series (Conformance Class 1, 2, 2b and 2c). In contrast, spatial data services still fail in only 1 dimension [WIP].
