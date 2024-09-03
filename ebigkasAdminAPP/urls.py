from django.urls import path
from .views import(
    ebigkas_admin,
    add_slideshow,
)



urlpatterns = [
    path('ebigkas_admin/', ebigkas_admin, name='ebigkas_admin'),
    path('add_slideshow/', add_slideshow, name='add_slideshow'),


]
