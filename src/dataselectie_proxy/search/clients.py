import logging
from urllib.parse import urlparse

import orjson
import requests
from more_ds.network import URL
from rest_framework.exceptions import APIException
from rest_framework.request import Request

from dataselectie_proxy.search.exceptions import BadGateway
from dataselectie_proxy.search.indexes import SearchIndex

logger = logging.getLogger(__name__)

USER_AGENT = "Amsterdam-Dataselectie-Proxy/1.0"


class BaseClient:
    endpoint_url: URL

    def __init__(self, base_url: URL) -> None:
        """Initialize the client configuration.

        :param base_url: Base URL of the Search Backend
        """
        if not base_url:
            raise ValueError(f"Missing {self.__class__.__name__} Base URL")
        self.base_url = base_url
        self._host = urlparse(base_url).netloc
        self._session = requests.Session()

    def call(self, request: Request, index: SearchIndex) -> requests.Response:
        request_args = self._extract_request_args(request)

        request_args = self._transform_request_args(request_args, index)
        response = self._call(request_args, index)

        self._remove_hop_by_hop_headers(response)

        if 200 <= response.status_code < 300:
            return response

        # Raise exception in nicer format, but chain with the original one
        # so the "response" object is still accessible via __cause__.response.
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise self._get_http_error(response) from e

    def _get_http_error(self, response: requests.Response) -> APIException:
        # Translate the remote HTTP error to the proper response.
        #
        # This translates some errors into a 502 "Bad Gateway" or 503 "Gateway Timeout"
        # error to reflect the fact that this API is calling another service as backend.

        # Consider the actual JSON response here,
        # unless the request hit the completely wrong page (it got an HTML page).
        content_type = response.headers.get("content-type", "")
        remote_json = (
            orjson.loads(response.content)
            if content_type in ("application/json", "application/problem+json")
            else None
        )
        detail_message = response.text if not content_type.startswith("text/html") else None

        if not remote_json:
            # Unexpected response, call it a "Bad Gateway"
            logger.error(
                "Proxy call failed, unexpected status code from endpoint: %s %s",
                response.status_code,
                detail_message,
            )
            return BadGateway(
                detail_message or f"Unexpected HTTP {response.status_code} from internal endpoint"
            )

        # Unexpected response, call it a "Bad Gateway"
        logger.error(
            "Proxy call failed, unexpected status code from endpoint: %s %s",
            response.status,
            detail_message,
        )
        return BadGateway(
            detail_message or f"Unexpected HTTP {response.status} from internal endpoint"
        )

    def _call(self, request_args: dict, index: SearchIndex) -> requests.Response:
        raise NotImplementedError

    def _extract_request_args(self, request: Request) -> dict:
        return {
            "headers": dict(request.headers),
            "params": request.GET,
            "data": request.data,
        }

    def _remove_hop_by_hop_headers(self, response: requests.Response) -> requests.Response:
        """
        Remove headers which should not be tunneled through:
        https: // datatracker.ietf.org / doc / html / rfc2616  # section-13.5.1
        """
        excluded_headers = {
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
            "content-encoding",
            "content-length",
        }

        for header in excluded_headers:
            response.headers.pop(header, None)

        return response

    def _transform_request_args(self, request_args: dict, index: SearchIndex) -> dict:
        return request_args


class AzureSearchServiceClient(BaseClient):
    """
    Client for the Azure Search Service
    """

    api_version: str = "2024-07-01"
    page_size: int = 100

    def __init__(self, base_url: URL, api_key) -> None:
        """Initialize the client configuration.

        :param base_url: Base URL of the Azure Search Service
        :param api_key: The API key to use
        """
        super().__init__(base_url)

        self._api_key = api_key

    def _call(self, request_args: dict, index: SearchIndex) -> requests.Response:
        endpoint_url = (
            f"{self.base_url}/{index.index_name}/docs/search?api-version={self.api_version}"
        )

        return self._session.request(
            "POST",
            endpoint_url,
            **request_args,
        )

    def _transform_request_args(self, request_args: dict, index: SearchIndex) -> dict:
        page_number = int(request_args["params"].get("page", 1))
        request_args["data"]["skip"] = (page_number - 1) * self.page_size
        request_args["data"]["top"] = self.page_size

        request_args["data"].update(self._extract_sort_parameters(request_args))
        request_args["data"].update(self._extract_facets_and_filters(request_args, index))

        request_args["json"] = request_args["data"]

        # Set only the required headers
        request_args["headers"] = {
            "Content-Type": "application/json; charset=utf-8",
            "api-key": self._api_key,
        }

        # Remove any url parameters and data since we're using json
        del request_args["params"]
        del request_args["data"]

        return request_args

    def _extract_sort_parameters(self, request_args: dict) -> dict:
        # Get the current sort parameters from the query parameters
        sort_fields = request_args["params"].get("sort", "").split(",")
        sort_parameters = [
            f"{field[1:]} desc" if field.startswith("-") else field for field in sort_fields
        ]

        return {"orderby": ",".join(sort_parameters)}

    def _extract_facets_and_filters(self, request_args: dict, index: SearchIndex) -> dict:
        filter_list = []
        facets = index.facets.copy()

        non_filter_params = ["sort", "page"]

        for param in request_args["params"]:
            if param in non_filter_params:
                continue

            value = request_args["params"][param]
            filter_list.append(f"{param} eq '{value}'")
            if param in facets:
                facets.remove(param)

        facet_list = [f"{facet},count:1400,sort:value" for facet in facets]

        return {
            "facets": facet_list,
            "filter": " and ".join(filter_list),
        }


class DSOExportClient(BaseClient):

    def _call(self, request_args: dict, index: SearchIndex) -> requests.Response:
        endpoint_url = f"{self.base_url}/v1/{index.api_path}"

        return self._session.request(
            "GET",
            endpoint_url,
            **request_args,
        )

    def _transform_request_args(self, request_args: dict, index: SearchIndex) -> dict:
        params = request_args["params"].copy()

        params.pop("export", None)
        params["_format"] = "csv"

        request_args["params"] = params

        return request_args
