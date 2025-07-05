from django.db.models import Q
from django_filters import rest_framework as filters
from airport.models import Flight


class FlightFilter(filters.FilterSet):
    departure_time = filters.DateFromToRangeFilter(field_name="departure_time")
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    airplane = filters.CharFilter(
        field_name="airplane__name",
        lookup_expr="icontains"
    )
    route = filters.CharFilter(method="filter_route")

    class Meta:
        model = Flight
        fields = ["departure_time", "status", "airplane", "route"]

    def filter_route(self, queryset, name, value):
        return queryset.filter(
            Q(route__source__name__icontains=value) |
            Q(route__destination__name__icontains=value)
        )
