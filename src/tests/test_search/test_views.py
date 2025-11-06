import pytest
from django.urls import reverse

from tests.utils import build_jwt_token


class TestProxyView:
    """Prove that the generic view offers the login check logic.
    This is tested through the concrete implementations though.
    """

    AZURE_SEARCH_RESPONSE = {
        "@odata.context": "https://test-bbn1-search.search.windows.net/indexes('benkagg_adresseerbareobjecten')/$metadata#docs(*)",
        "@odata.count": 13656,
        "@search.facets": {},
    }

    def test_bag_index(self, api_client, requests_mock):
        """Prove the BAG dataselectie points to the correct index."""
        requests_mock.post("/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01")

        # Expect bag to be mapped to the index benkagg_adresseerbareobjecten
        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        api_client.get(url)
        assert "benkagg_adresseerbareobjecten" in requests_mock.last_request.url

    def test_bearer_token_present(self, api_client, requests_mock):
        """Prove the bearer token is added to the Authorization header."""
        requests_mock.post("/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01")

        # Expect bag to be mapped to the index benkagg_adresseerbareobjecten
        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        api_client.get(url)
        assert "Bearer oauth_token" in requests_mock.last_request.headers["Authorization"]

    def test_non_existing_index(self, api_client):
        """Prove non-existing index returns 404."""
        url = reverse("dataselectie-search", kwargs={"dataset_name": "non-existent"})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_brk_requires_token(self, api_client, requests_mock):
        """
        Prove the BRK dataselectie points to the correct index and is only
        accessible with the correct scope.
        """
        # Expect brk to require a token with the correct scope
        url = reverse("dataselectie-search", kwargs={"dataset_name": "brk"})
        response = api_client.get(url)
        assert response.status_code == 403
        assert response.data == {"detail": "Required scopes not given."}

        requests_mock.post(
            "/benkagg_brkbasisdataselectie/docs/search?api-version=2024-07-01",
        )

        token = build_jwt_token(["BRK/RSN"])
        api_client.get(url, headers={"Authorization": f"Bearer {token}"})

        assert "benkagg_brkbasisdataselectie" in requests_mock.last_request.url

    def test_page_numbers(self, api_client, requests_mock):
        """Prove page numbers are parsed correctly"""
        requests_mock.post(
            "/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01",
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        api_client.get(url, data={"page": 4})
        assert "skip" in requests_mock.last_request.json()
        assert requests_mock.last_request.json()["skip"] == 300

    def test_sort_parameters(self, api_client, requests_mock):
        """Prove sort parameters are parsed correctly"""
        requests_mock.post(
            "/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01",
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        api_client.get(url, data={"sort": "param1,-param2"})
        assert "orderby" in requests_mock.last_request.json()
        assert requests_mock.last_request.json()["orderby"] == "param1,param2 desc"

    def test_filters_and_facets(self, api_client, requests_mock):
        """Prove filters and facets parameters are parsed correctly"""
        requests_mock.post(
            "/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01",
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        api_client.get(
            url,
            data={
                "postcode": "1000AA",
                "woonplaatsNaam": "Amsterdam",
                "huisnummer": 10,
                "huisnummerToevoeging": "A",
                "openbareruimteNaam": "'s-Gravelandse Veer",
            },
        )
        assert "facets" in requests_mock.last_request.json()
        assert "filter" in requests_mock.last_request.json()
        assert all(
            facet not in requests_mock.last_request.json()["facets"]
            for facet in ["postcode,count:1400", "woonplaatsNaam,count:1400"]
        )
        assert (
            requests_mock.last_request.json()["filter"]
            == "postcode eq '1000AA' and woonplaatsNaam eq 'Amsterdam' "
            "and huisnummer eq '10' and huisnummerToevoeging eq 'A' "
            "and openbareruimteNaam eq '''s-Gravelandse Veer'"
        )

    @pytest.mark.parametrize("true_value", ["True", "true", "1", "on", "t"])
    def test_boolean_filters(self, api_client, requests_mock, true_value):
        """Prove boolean filters are parsed correctly"""
        requests_mock.post(
            "/benkagg_brkbasisdataselectie/docs/search?api-version=2024-07-01",
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "brk"})

        token = build_jwt_token(["BRK/RSN"])
        api_client.get(
            url, data={"grondeigenaar": true_value}, headers={"Authorization": f"Bearer {token}"}
        )

        assert "filter" in requests_mock.last_request.json()
        assert requests_mock.last_request.json()["filter"] == "grondeigenaar eq true"

    def test_odata_context_replaced(self, api_client, requests_mock):
        """Prove page numbers are parsed correctly"""
        requests_mock.post(
            "/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01",
            json=self.AZURE_SEARCH_RESPONSE,
            headers={"content-type": "application/json"},
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        response = api_client.get(url)

        assert "@odata.context" in response.json()
        assert response.json()["@odata.context"] == "http://testserver/dataselectie/v2/bag/search"

    def test_search_address(self, api_client, requests_mock):
        """Prove boolean filters are parsed correctly"""
        requests_mock.post(
            "/benkagg_adresseerbareobjecten/docs/search?api-version=2024-07-01",
        )

        url = reverse("dataselectie-search-address")

        api_client.get(url, data={"q": "oude"})

        last_request = requests_mock.last_request.json()

        assert "search" in last_request
        assert last_request["search"] == "oude*"
        # Make sure the correct search profile is used and we order by score
        assert "scoringProfile" in last_request
        assert last_request["scoringProfile"] == "search_address"
        assert last_request["orderby"].startswith("search.score()")

    def test_export_uses_dso_client(self, api_client, requests_mock):
        """Prove export uses a GET request to the DSO API"""
        requests_mock.get(
            "https://dso.api/v1/benkagg/adresseerbareobjecten?_format=csv",
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "bag"})
        api_client.get(url, data={"export": "true"})

        assert requests_mock.call_count == 1

    def test_export_passes_along_authorization(self, api_client, requests_mock):
        """Prove export uses a GET request to the DSO API with authorization header"""
        requests_mock.get(
            "https://dso.api/v1/benkagg/brkbasisdataselectie?_format=csv",
        )

        url = reverse("dataselectie-search", kwargs={"dataset_name": "brk"})

        token = build_jwt_token(["BRK/RSN"])
        api_client.get(url, data={"export": "true"}, headers={"Authorization": f"Bearer {token}"})

        assert "authorization" in requests_mock.last_request.headers
