from django.urls import path
from .views import(
    ebigkas_admin,
    add_slideshow,
    admin_feedbacks,
    edit_slideshow,
    submit_response,
)



urlpatterns = [
    path('ebigkas_admin/', ebigkas_admin, name='ebigkas_admin'),
    path('add_slideshow/', add_slideshow, name='add_slideshow'),
    path('admin_feedbacks/', admin_feedbacks, name='admin_feedbacks'),
    path('edit_slideshow/<int:id>/', edit_slideshow, name='edit_slideshow'),
    path('submit_response/<int:feedback_id>/', submit_response, name='submit_response'),


]
