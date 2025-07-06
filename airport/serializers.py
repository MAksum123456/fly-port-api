from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from .models import (
    Country,
    City,
    Airport,
    AirplaneType,
    Airplane,
    Crew,
    Route,
    Flight,
    Ticket,
    Order,
)


class CrewSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Crew
        fields = (
            "id",
            "full_name",
            "experience_years",
            "first_name",
            "last_name"
        )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class TicketSerializer(serializers.ModelSerializer):
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "ticket_class",
            "price",
            "flight",
            "order"
        )
        read_only_fields = ("id", "order", "price")

    def validate(self, data):
        flight = data.get("flight")
        row = data.get("row")
        seat = data.get("seat")

        if not all([flight, row, seat]):
            raise serializers.ValidationError(
                "Flight, row, and seat must be provided."
            )

        if Ticket.objects.filter(flight=flight, row=row, seat=seat).exists():
            raise serializers.ValidationError({
                "seat": "This seat is already taken for the selected flight."
            })

        airplane = flight.airplane
        if row < 1 or row > airplane.rows:
            raise serializers.ValidationError(
                f"Row number must be between 1 and {airplane.rows}."
            )
        if seat < 1 or seat > airplane.seats_in_row:
            raise serializers.ValidationError(
                f"Seat number must be between 1 and {airplane.seats_in_row}."
            )

        return data


class FlightSerializer(serializers.ModelSerializer):
    route = serializers.SerializerMethodField()
    airplane = serializers.CharField(source="airplane.name", read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "status"
        )

    def validate(self, data):
        departure_time = data.get("departure_time")
        arrival_time = data.get("arrival_time")
        if departure_time and arrival_time and departure_time >= arrival_time:
            raise serializers.ValidationError(
                "Arrival time must be after departure time."
            )
        if departure_time < timezone.now():
            raise serializers.ValidationError(
                "The time of departure cannot be in the past"
            )
        return data

    def get_route(self, obj):
        return f"{obj.route.source.name} -> {obj.route.destination.name}"


class FlightRetrieveSerializer(FlightSerializer):
    crew_details = CrewSerializer(many=True, read_only=True, source="crew")

    class Meta(FlightSerializer.Meta):
        fields = FlightSerializer.Meta.fields + ("crew_details",)


class OrderSerializer(serializers.ModelSerializer):
    order_tickets = TicketSerializer(
        many=True,
        allow_empty=False,
        read_only=True
    )
    tickets = TicketSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "order_tickets", "tickets")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user

        price_mapping = {
            "economy": 100,
            "business": 200,
            "first": 300,
        }

        with transaction.atomic():
            order = Order.objects.create(user=user, **validated_data)
            for ticket_data in tickets_data:
                ticket_class = ticket_data.get("ticket_class", "economy")
                ticket_data["price"] = price_mapping.get(ticket_class, 100)
                Ticket.objects.create(order=order, **ticket_data)

        return order

    def validate(self, data):
        tickets_data = data.get("tickets")
        if tickets_data:
            flight_ids = {ticket["flight"] for ticket in tickets_data}
            if len(flight_ids) > 1:
                raise serializers.ValidationError(
                    "All tickets must be in the same flight."
                )
        return data


class TicketRetrieveSerializer(serializers.ModelSerializer):
    flight_details = SerializerMethodField()
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "ticket_class",
            "price",
            "order",
            "flight_details"
        )

    def get_flight_details(self, obj):
        flight = obj.flight
        crew_members = flight.crew.all()
        return {
            "route": f"{flight.route.source.name} -> "
                     f"{flight.route.destination.name}",
            "departure_time": flight.departure_time,
            "arrival_time": flight.arrival_time,
            "airplane": flight.airplane.name,
            "status": flight.status,
            "crew": [
                f"{member.first_name} {member.last_name}"
                for member in crew_members
            ],
        }


class OrderRetrieveSerializer(serializers.ModelSerializer):
    order_tickets = TicketRetrieveSerializer(many=True, allow_empty=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "order_tickets")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name")


class CitySerializer(serializers.ModelSerializer):
    country = serializers.CharField(source="country.name", read_only=True)
    airports = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ("id", "name", "country", "airports")

    def get_airports(self, obj):
        return [airport.name for airport in obj.airports.all()]


class AirportSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source="city.name", read_only=True)
    country = serializers.CharField(source="city.country.name", read_only=True)

    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city", "city", "country")


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(queryset=Airport.objects.all())
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all()
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

    def validate(self, data):
        source = data.get("source", getattr(self.instance, "source", None))
        destination = data.get(
            "destination",
            getattr(self.instance, "destination", None)
        )
        if destination and source and source == destination:
            raise serializers.ValidationError(
                "Source and destination must differ."
            )
        return data


class CrewMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Crew
        fields = ("full_name", )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class FlightMiniSerializer(serializers.ModelSerializer):
    airplane = serializers.CharField(source="airplane.name", read_only=True)
    crew = CrewMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = (
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
            "status"
        )


class RouteRetrieveSerializer(RouteSerializer):
    flights = FlightMiniSerializer(
        many=True,
        read_only=True,
        source="route_flight"
    )

    class Meta(RouteSerializer.Meta):
        fields = RouteSerializer.Meta.fields + ("flights",)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = serializers.SerializerMethodField()

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "serial_number",
            "rows",
            "seats_in_row",
            "airplane_type",
            "image"
        )

    def get_airplane_type(self, obj):
        return obj.airplane_type.name
