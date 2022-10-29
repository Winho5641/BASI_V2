from django.urls import path
from . import views

urlpatterns = [
    path('search/<str:q>/', views.StockSearch.as_view()),
    path('', views.landing),

]