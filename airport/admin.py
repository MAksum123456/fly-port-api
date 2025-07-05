from django.contrib import admin

from airport.models import (
    Order,
    Crew,
    Airport,
    AirplaneType,
    Airplane,
    Ticket,
    Flight,
    City,
    Country,
    Route
)


admin.site.register(Crew)
admin.site.register(Order)
admin.site.register(Ticket)
admin.site.register(AirplaneType)
admin.site.register(Airplane)
admin.site.register(City)
admin.site.register(Country)
admin.site.register(Route)
admin.site.register(Flight)
admin.site.register(Airport)
