from django.urls import path

from . import views

urlpatterns = [
    path(
        "dataselectie/v2/bag/search/adres",
        views.ProxySearchAddressView.as_view(),
        name="dataselectie-search-address",
    ),
    path(
        "dataselectie/v2/<str:dataset_name>/search",
        views.ProxySearchView.as_view(),
        name="dataselectie-search",
    ),
]
