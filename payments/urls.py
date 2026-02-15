from django.urls import path
from .views import invoice

app_name = 'payments'

urlpatterns = [
    path('<uuid:uuid>/', invoice, name='invoice'),
]
