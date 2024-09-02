from django.urls import path
from .views import(
    ebigkas_admin
)



urlpatterns = [
    path('ebigkas_admin/', ebigkas_admin, name='ebigkas_admin'),

]
