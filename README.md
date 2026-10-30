# Dataselectie Proxy

Proxy service and token-based authorization for our Azure Search Service or DSO-API when exporting to CSV.

## Installation

Requirements:

* Python >= 3.12
* [uv](https://docs.astral.sh/uv/)
* Recommended: Docker/Docker Compose (or pyenv for local installs)

### Using Docker Compose

Run docker compose:
```shell
docker compose up
```

Navigate to `localhost:8000`.

The base configuration uses default build networking and is also used by CI.
To opt into host networking during local development builds, for local development authentication,
add the development override explicitly:

```shell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Use the same two `-f` options for subsequent commands such as `down`.

### Using Local Python

Install the project and its development dependencies:

```shell
uv sync --group dev
```

Set the required environment variables and start the Django application:

```shell
export PUB_JWKS="$(cat src/jwks_test.json)"
export DJANGO_DEBUG=true
export CLOUD_ENV=local
export AZURE_SEARCH_BASE_URL={AZURE_SEARCH_API_KEY}
export DSO_API_BASE_URL={DSO_API_BASE_URL}
export ACCESS_TOKEN=$(az account get-access-token --resource=https://search.azure.com/)

uv run --project . python src/manage.py runserver localhost:8000
```

From the repository root, the Makefile also provides common developer commands:

```shell
make -C src install
make -C src test
make -C src lint
make -C src typecheck
```

## Example Requests

Search BAG for a specific postcode:

    curl http://localhost:8000/dataselectie/v2/bag/search?postcode=1012AB

Order results by housenumber:

    curl http://localhost:8000/dataselectie/v2/bag/search?postcode=1012AB&sort=huisnummer

## Available Parameters

| Name   | Possible Values                                | Details                                             |
|--------|------------------------------------------------|-----------------------------------------------------|
| page   | Integer e.g. `1`, `2` etc.                     | Current page size is 100                            |
| sort   | Field name, e.g. `huisnummer` or `-huisnummer` | Add a dash in front of the value to reverse order   |
| export | `true`                                         | Request the results in a CSV file. Uses the DSO-API |

To narrow down results, use the available fields to filter for values. Facets, filterable and sortable fields are
defined on an index level.

## Search for address

To provide functionality for an address search an extra endpoint is added. This allows a search on parts of a
postcode or 'openbareruimteNaam'

    curl http://localhost:8000/dataselectie/v2/bag/search/adres?q=1012
    curl http://localhost:8000/dataselectie/v2/bag/search/adres?q=oude


## Environment Settings

The following environment variables are useful for configuring a local development environment:

* `DJANGO_DEBUG` to enable debugging (true/false).
* `LOG_LEVEL` log level for application code (default is `DEBUG` for debug, `INFO` otherwise).
* `AUDIT_LOG_LEVEL` log level for audit messages (default is `INFO`).
* `DJANGO_LOG_LEVEL` log level for Django internals (default is `INFO`).
* `PUB_JWKS` allows to give publically readable JSON Web Key Sets in JSON format (good default: `jq -c < src/jwks_test.json`).

Connections:

* `AZURE_SEARCH_BASE_URL` endpoint for the Azure Search Service.
* `DSO_API_BASE_URL` endpoint for DSO API.

Deployment:

* `ALLOWED_HOSTS` will limit which domain names can connect.
* `AZURE_APPI_CONNECTION_STRING` Azure Insights configuration.
* `AZURE_APPI_AUDIT_CONNECTION_STRING` Same, for a special audit logging.
* `CLOUD_ENV=azure` will enable Azure-specific telemetry.
* `OAUTH_JWKS_URL` point to a public JSON Web Key Set, e.g. `https://login.microsoftonline.com/{tenant_uuid or 'common'}/discovery/v2.0/keys`.
* `OAUTH_CHECK_CLAIMS` should be `aud=AUDIENCE-IN-TOKEN,iss=ISSUER-IN-TOKEN`.

Hardening deployment:

* `SESSION_COOKIE_SECURE` is already true in production.
* `CSRF_COOKIE_SECURE` is already true in production.
* `SECRET_KEY` is used for various encryption code.
* `CORS_ALLOW_ALL_ORIGINS` can be true/false to allow all websites to connect.
* `CORS_ALLOWED_ORIGINS` allows a list of origin URLs to use.
* `CORS_ALLOWED_ORIGIN_REGEXES` supports a list of regex patterns fow allowed origins.

## Developer Notes

Run `make` in the `src` folder to have a help-overview of all common developer tasks.

## Package Management

The packages are managed with uv and locked in `uv.lock`.

To add a runtime package, update `project.dependencies` in `pyproject.toml`.
To add a development or test package, update the `dev` dependency group.
Run `uv lock` (or `make -C src lock`) to update `uv.lock`.

To upgrade locked packages, run `make -C src upgrade`, followed by
`make -C src sync test`.

## Environment Settings

Consider using *direnv* for automatic activation of environment variables.
It automatically sources an ``.envrc`` file when you enter the directory.
This file should contain all lines in the `export VAR=value` format.

In a similar way, *pyenv* helps to install the exact Python version,
and will automatically activate the virtualenv when a `.python-version` file is found:

```shell
pyenv install 3.12.4
pyenv virtualenv 3.12.4 dataselectie-proxy
echo dataselectie-proxy > .python-version
```
