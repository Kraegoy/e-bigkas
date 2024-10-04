from django.urls import path
from .views import (
    learnings_view,
    learn_action,
    recognize_action,
    save_user_learning
)

urlpatterns = [
    path('learnings_view/', learnings_view, name='learnings_view'),  
    path('learn_action/<int:id>/', learn_action, name='learn_action'),  
    path('recognize_action/<int:id>/', recognize_action, name='recognize_action'),
    path('save_learning/<int:learning_id>/', save_user_learning, name='save_user_learning'),

]
