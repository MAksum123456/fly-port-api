from django.urls import path, include
from rest_framework import routers

from airport.views import (
    CrewViewSet,
    OrderViewSet,
    FlightViewSet,
    CountryViewSet,
    CityViewSet,
    AirportViewSet,
    RouteViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet
)


app_name = "airport"

router = routers.DefaultRouter()
router.register("crew", CrewViewSet)
router.register("order", OrderViewSet)
router.register("flight", FlightViewSet)
router.register("country", CountryViewSet)
router.register("city", CityViewSet)
router.register("airport", AirportViewSet)
router.register("route", RouteViewSet)
router.register("airplane_type", AirplaneTypeViewSet)
router.register("airplane", AirplaneViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
