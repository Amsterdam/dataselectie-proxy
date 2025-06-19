from django.urls import path

from . import views

urlpatterns = [
    path(
        "dataselectie/<str:dataset_name>/search",
        views.ProxySearchView.as_view(),
        name="dataselectie-index",
    )
]
