# ckan-pycsw

This is a [base container for pycsw](https://github.com/mjanez/ckan-pycsw), an OGC CSW server implementation written in Python. For more information about pycsw got to [pycsw.org](https://pycsw.org). For the source code of pycsw got to [gepython/pycsw](https://github.com/geopython/pycsw) on GitHub.

## Tags

* `*.*.*`, `latest`

## Exposes

* Port `8000` exposes the pycsw service.

## Environment

Copy the `.env.example` template and configure by changing the `.env` file. Change `PYCSW_URL` and `CKAN_URL`,  as well as the published port `PYCSW_PORT`, if needed.

```shell
cp .env.example .env
```