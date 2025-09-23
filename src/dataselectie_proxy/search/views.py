from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from dataselectie_proxy.search import permissions
from dataselectie_proxy.search.clients import AzureSearchServiceClient, DSOExportClient
from dataselectie_proxy.search.indexes import INDEX_MAPPING, SearchIndex


class ProxySearchView(APIView):

    needed_scopes: set = None
    client: AzureSearchServiceClient | DSOExportClient

    permission_classes = []

    def initial(self, request: Request, *args, **kwargs):
        """DRF-level initialization for all request types."""

        try:
            index = INDEX_MAPPING[kwargs["dataset_name"]]
        except KeyError:
            raise Http404("Index not found") from None

        self.needed_scopes = index.needed_scopes

        # Perform authorization, permission checks and throttles.
        super().initial(request, *args, **kwargs)

        self.user_scopes = set(request.get_token_scopes)

    def get_client(
        self, is_export_client: bool = False
    ) -> AzureSearchServiceClient | DSOExportClient:
        """Provide the AzureSearchServiceClient. This can be overwritten per view if needed."""

        if is_export_client:
            return DSOExportClient(base_url=settings.DSO_API_BASE_URL)

        return AzureSearchServiceClient(
            base_url=settings.AZURE_SEARCH_BASE_URL,
            api_key=settings.AZURE_SEARCH_API_KEY,
        )

    def get(self, request: Request, *args, **kwargs):
        # Existence of index has already been verified
        index = INDEX_MAPPING[kwargs["dataset_name"]]

        self.client = self.get_client(is_export_client=request.query_params.get("export", False))

        response: Response = self.client.call(
            request=request,
            index=index,
        )

        return HttpResponse(response, headers=response.headers)

    def get_permissions(self):
        """Collect the DRF permission checks.
        DRF checks these in the initial() method, and will block view access
        if these permissions are not satisfied.
        """

        return super().get_permissions() + [
            permissions.IsUserScope(self.needed_scopes),
        ]


class ProxySearchAddressView(APIView):
    client: AzureSearchServiceClient
    index: SearchIndex = INDEX_MAPPING["bag"]

    def get_client(self) -> AzureSearchServiceClient:
        """Provide the AzureSearchServiceClient. This can be overwritten per view if needed."""

        return AzureSearchServiceClient(
            base_url=settings.AZURE_SEARCH_BASE_URL,
            api_key=settings.AZURE_SEARCH_API_KEY,
        )

    def get(self, request: Request, *args, **kwargs):
        self.client = self.get_client()

        response: Response = self.client.search_address(
            request=request,
            index=self.index,
        )

        return HttpResponse(response, headers=response.headers)
