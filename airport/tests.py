from django.test import TestCase, RequestFactory
from airport.serializers import (
    RouteSerializer,
    TicketSerializer,
    FlightSerializer, OrderSerializer,
)
from django.utils import timezone
from datetime import timedelta
from airport.models import (
    Airplane,
    AirplaneType,
    Route,
    Flight,
    Airport,
    City,
    Country,
    Crew,
)
from user.models import User


class OrderSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="12345"
        )
        country = Country.objects.create(name="Ukraine")
        city = City.objects.create(name="Kyiv", country=country)
        airport1 = Airport.objects.create(name="Boryspil", city=city)
        airport2 = Airport.objects.create(name="Zhuliany", city=city)
        route = Route.objects.create(
            source=airport1,
            destination=airport2,
            distance=300
        )
        airplane_type = AirplaneType.objects.create(name="Boeing 737")
        airplane = Airplane.objects.create(
            name="Boeing 737-800",
            rows=30,
            seats_in_row=6,
            airplane_type=airplane_type,
            serial_number="TEST123"
        )
        crew = Crew.objects.create(
            first_name="John",
            last_name="Doe",
            experience_years=5
        )
        self.flight = Flight.objects.create(
            route=route,
            airplane=airplane,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=2)
        )
        self.flight2 = Flight.objects.create(
            route=route,
            airplane=airplane,
            departure_time=timezone.now() + timedelta(days=2),
            arrival_time=timezone.now() + timedelta(days=2, hours=3)
        )
        self.flight.crew.add(crew)
        self.flight2.crew.add(crew)

    def test_order_serializer_create_tickets(self):
        request = RequestFactory().get("/")
        request.user = self.user
        data = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 6,
                    "ticket_class": "first",
                    "flight": self.flight.id,
                },
                {
                    "row": 3,
                    "seat": 6,
                    "ticket_class": "economy",
                    "flight": self.flight.id,
                }
            ]
        }

        serializer = OrderSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        assert order.order_tickets.count() == 2
        first_class_ticket = order.order_tickets.get(ticket_class="first")
        economy_class_ticket = order.order_tickets.get(ticket_class="economy")

        self.assertIsNotNone(first_class_ticket.price)
        self.assertIsNotNone(economy_class_ticket.price)

        self.assertEqual(first_class_ticket.price, 300)
        self.assertEqual(economy_class_ticket.price, 100)

    def test_order_serializer_validate(self):
        request = RequestFactory().get("/")
        request.user = self.user
        data = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 6,
                    "ticket_class": "first",
                    "flight": self.flight.id,
                },
                {
                    "row": 3,
                    "seat": 6,
                    "ticket_class": "economy",
                    "flight": self.flight2.id,
                }
            ]
        }
        serializer = OrderSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn(
            str(serializer.errors["non_field_errors"][0]),
            "All tickets must be in the same flight. "
        )


class RouteSerializerTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(name="Ukraine")
        self.city = City.objects.create(name="Kyiv", country=self.country)
        self.airport1 = Airport.objects.create(name="Boryspil", city=self.city)
        self.airport2 = Airport.objects.create(name="Zhuliany", city=self.city)

    def test_valid_route(self):
        data = {
            "source": self.airport1.id,
            "destination": self.airport2.id,
            "distance": 300,
        }
        serializer = RouteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_route(self):
        data = {
            "source": self.airport1.id,
            "destination": self.airport1.id,
            "distance": 300,
        }
        serializer = RouteSerializer(data=data)
        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "Source and destination must differ."
        )


class FlightSerializerTest(TestCase):
    def setUp(self):
        country = Country.objects.create(name="Ukraine")
        city = City.objects.create(name="Kyiv", country=country)
        airport1 = Airport.objects.create(name="Boryspil", city=city)
        airport2 = Airport.objects.create(name="Zhuliany", city=city)
        self.route = Route.objects.create(
            source=airport1,
            destination=airport2,
            distance=300
        )
        self.airplane_type = AirplaneType.objects.create(name="Boeing 737")
        self.airplane = Airplane.objects.create(
            name="Boeing 737-800",
            rows=30,
            seats_in_row=6,
            airplane_type=self.airplane_type
        )
        self.crew = Crew.objects.create(
            first_name="John",
            last_name="Lee",
            experience_years=5
        )

    def test_valid_flight(self):
        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=2)
        data = {
            "route": self.route,
            "airplane": self.airplane,
            "departure_time": departure,
            "arrival_time": arrival,
            "status": "scheduled"
        }
        serializer = FlightSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_departure_time_in_past(self):
        departure = timezone.now() - timedelta(days=1)
        arrival = departure + timedelta(hours=2)
        data = {
            "route": self.route,
            "airplane": self.airplane,
            "departure_time": departure,
            "arrival_time": arrival,
            "status": "scheduled"
        }
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "The time of departure cannot be in the past"
        )

    def test_invalid_flight(self):
        departure = timezone.now() + timedelta(days=1)
        arrival = departure
        data = {
            "route": self.route,
            "airplane": self.airplane,
            "departure_time": departure,
            "arrival_time": arrival,
            "status": "scheduled"
        }
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid(), serializer.errors)


class TicketSerializerTest(TestCase):
    def setUp(self):
        country = Country.objects.create(name="Ukraine")
        city = City.objects.create(name="Kyiv", country=country)
        airport1 = Airport.objects.create(name="Boryspil", city=city)
        airport2 = Airport.objects.create(name="Zhuliany", city=city)
        route = Route.objects.create(
            source=airport1,
            destination=airport2,
            distance=300)

        airplane_type = AirplaneType.objects.create(name="Boeing 737")
        airplane = Airplane.objects.create(
            name="Boeing 737-800",
            rows=30,
            seats_in_row=6,
            airplane_type=airplane_type
        )
        self.flight = Flight.objects.create(
            route=route,
            airplane=airplane,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=2),
        )

    def test_valid_ticket(self):
        data = {
            "row": 10,
            "seat": 6,
            "ticket_class": "first",
            "flight": self.flight.id,
        }
        serializer = TicketSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_row_ticket(self):
        data = {
            "row": 31,
            "seat": 6,
            "ticket_class": "first",
            "flight": self.flight.id,
        }

        serializer = TicketSerializer(data=data)
        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            str(serializer.errors["non_field_errors"][0]),
            "Row number must be between 1 and 30."
        )

    def test_invalid_seat_ticket(self):
        data = {
            "row": 30,
            "seat": 7,
            "ticket_class": "first",
            "flight": self.flight.id,
        }

        serializer = TicketSerializer(data=data)
        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            str(serializer.errors["non_field_errors"][0]),
            "Seat number must be between 1 and 6."
        )
