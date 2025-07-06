from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from airport.filters import FlightFilter
from airport.models import (
    Crew,
    Order,
    Flight,
    Country,
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane
)
from airport.serializers import (
    CrewSerializer,
    OrderSerializer,
    OrderRetrieveSerializer,
    FlightSerializer,
    CountrySerializer,
    CitySerializer,
    AirportSerializer,
    RouteSerializer,
    RouteRetrieveSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer, FlightRetrieveSerializer
)


class CrewViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        first = self.request.GET.get("first")
        last = self.request.GET.get("last")
        full_name = self.request.GET.get("full_name")
        if full_name:
            queryset = queryset.filter(
                Q(first_name__icontains=full_name) |
                Q(last_name__icontains=full_name)
            )

        if first:
            queryset = queryset.filter(first_name__icontains=first)

        if last:
            queryset = queryset.filter(last_name__icontains=last)
        return queryset

    @extend_schema(
        tags=["Crew"],
        description="List crew with optional filters:"
                    " first_name, last_name, full_name.",
        parameters=[
            OpenApiParameter(
                name="first",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by first name",
            ),
            OpenApiParameter(
                name="last",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by last name",
            ),
            OpenApiParameter(
                name="full_name",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by full name",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Order"],
    description="returns a list of orders for this user and user "
                "can also make an order by creating a ticket, "
                "the admin sees all orders and can CRUD operations",
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    administrator can perform CRUD operations,
    and an ordinary user can only view their orders and create new ones
    """

    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderSerializer
        elif self.action == "retrieve":
            return OrderRetrieveSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("order_tickets")

        if not self.request.user.is_staff:
            if self.request.user.is_authenticated:
                return queryset.filter(user=self.request.user).distinct()
            return queryset.none()
        return queryset.distinct()


class FlightViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """
    queryset = Flight.objects.select_related(
        "route__source",
        "route__destination",
        "airplane",
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = FlightFilter
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return FlightSerializer
        if self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    @extend_schema(
        description="List flights with optional filters: "
                    "departure date range, status, airplane name, "
                    "and route (source/destination).",
        tags=["Flight"],
        parameters=[
            OpenApiParameter(
                name="departure_time_after",
                type=OpenApiTypes.DATE,
                required=False,
                description=("Start of the departure date range (YYYY-MM-DD)")
            ),
            OpenApiParameter(
                name="departure_time_before",
                type=OpenApiTypes.DATE,
                required=False,
                description=("End of the departure date range (YYYY-MM-DD)")
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                required=False,
                description=(
                        "Status of the flight (scheduled, delayed, cancelled)"
                )
            ),
            OpenApiParameter(
                name="airplane",
                type=OpenApiTypes.STR,
                required=False,
                description=("Airplane name (partial match)")
            ),
            OpenApiParameter(
                name="route",
                type=OpenApiTypes.STR,
                required=False,
                description=("Route name (source, destination)")
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Country"],
    description=(
            "returns a list of countries , "
            "ordinary users can do nothing but browse, "
            "and the admin can perform CRUD operations"
    )
)
class CountryViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["City"],
    description=(
            "returns a list of cities , "
            "ordinary users can do nothing but browse, "
            "and the admin can perform CRUD operations"
    )
)
class CityViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = City.objects.select_related("country").prefetch_related(
        "airports"
    )
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["Airport"],
    description=(
            "returns a list of airports , "
            "ordinary users can do nothing but browse, "
            "and the admin can perform CRUD operations"
    )
)
class AirportViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = Airport.objects.select_related("city", "city__country")
    serializer_class = AirportSerializer
    permission_classes = [IsAuthenticated]


class RouteViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = Route.objects.all().select_related("source", "destination")

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteSerializer
        elif self.action == "retrieve":
            return RouteRetrieveSerializer
        return RouteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        destination = self.request.query_params.get("destination")
        source = self.request.query_params.get("source")
        if destination:
            queryset = queryset.filter(
                destination__name__icontains=destination
            )
        if source:
            queryset = queryset.filter(source__name__icontains=source)
        return queryset

    @extend_schema(
        tags=["Route"],
        description="List routes with optional filters "
                    "by source and destination city names.",
        parameters=[
            OpenApiParameter(
                name="source",
                type=OpenApiTypes.STR,
                required=False,
                description=("Source name (partial match)")
            ),
            OpenApiParameter(
                name="destination",
                type=OpenApiTypes.STR,
                required=False,
                description=("Destination name (partial match)")
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["AirplaneType"],
    description=(
        "returns a list of airplane types, "
        "the admin can do CRUD operations, and regular users can only view"
    )
)
class AirplaneTypeViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["Airplane"],
    description=(
        "returns a list of airplanes, "
        "ordinary users can do nothing but browse, "
        "and the admin can perform CRUD operations"
    )
)
class AirplaneViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    admin can perform a CRUD operation through admin panel,
    and a simple authorized user can only view
    """

    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    permission_classes = [IsAuthenticated]
