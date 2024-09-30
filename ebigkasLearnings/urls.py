from django.urls import path
from .views import (
    learnings_view,
    learn_action,
)

urlpatterns = [
    path('learnings_view/', learnings_view, name='learnings_view'),  
    path('learn_action/<int:id>/', learn_action, name='learn_action'),  


]
