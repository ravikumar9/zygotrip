from django.urls import path
from .views import cab_list

app_name = "cabs"

urlpatterns = [
	path("", cab_list, name="list"),
]
