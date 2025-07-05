from django.conf import settings
from django.db import models
from django.utils.text import slugify
import os
import uuid


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name",]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (f"{self.user.first_name} {self.user.last_name}, "
                f"ordered by {self.created_at}")


class Ticket(models.Model):
    TICKET_CLASS_CHOICES = [
        ("economy", "Economy"),
        ("business", "Business"),
        ("first", "First"),
    ]

    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    ticket_class = models.CharField(
        max_length=10,
        choices=TICKET_CLASS_CHOICES,
        default="economy"
    )
    price = models.PositiveIntegerField()
    flight = models.ForeignKey(
        "Flight",
        on_delete=models.CASCADE,
        related_name="flight_tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_tickets"
    )

    class Meta:
        unique_together = ("row", "seat", "flight")
        ordering = ["price"]

    def __str__(self) -> str:
        return (f"Ticket for flight {self.flight.id}, "
                f"row {self.row}, seat {self.seat}")


def airplane_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/airplane/", filename)


class AirplaneType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, unique=True)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.PROTECT,
        related_name="airplane_type"
    )
    image = models.ImageField(null=True, upload_to=airplane_image_file_path)

    def __str__(self) -> str:
        return f"{self.name}, {self.serial_number}"

    class Meta:
        ordering = ["name"]


class City(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(
        "Country",
        on_delete=models.PROTECT,
        related_name="cities"
    )

    def __str__(self) -> str:
        return f"{self.name}: {self.country.name}"

    class Meta:
        ordering = ["name"]


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]


class Airport(models.Model):
    name = models.CharField(max_length=255, unique=True)
    closest_big_city = models.CharField(max_length=255)
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="airports"
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="source_routes"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="destination_routes"
    )
    distance = models.PositiveIntegerField()

    def __str__(self) -> str:
        return (
            f"{self.source.name} - "
            f"{self.destination.closest_big_city}: "
            f"distance: {self.distance}"
            )

    class Meta:
        unique_together = ("source", "destination")
        ordering = ["distance"]


class Flight(models.Model):
    FLIGHT_STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("delayed", "Delayed"),
        ("cancelled", "Cancelled"),
        ("landed", "Landed"),
    ]
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="route_flight"
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="airplane_flight"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="crew_flights")
    status = models.CharField(max_length=20, choices=FLIGHT_STATUS_CHOICES)

    class Meta:
        ordering = ["-departure_time"]
