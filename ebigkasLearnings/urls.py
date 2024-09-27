from django.urls import path
from .views import (
    learnings_view
)

urlpatterns = [
    path('learnings_view/', learnings_view, name='learnings_view'),  

]
