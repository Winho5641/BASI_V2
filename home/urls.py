from django.urls import path
from . import views

urlpatterns = [
    ## path('search/<str:q>/', views.PosrtSearch.as_view()),
    path('', views.landing),
]