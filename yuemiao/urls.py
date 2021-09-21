from django.urls import include, path
from . import views

urlpatterns = [
    path('hospital/', views.queryHospital, name='queryHospital'),
    path('hospital/vac/', views.queryVacOfHospital, name='queryVacOfHospital'),
    path('hospital/vac/sub/', views.subscribe, name='subscribe'),
    path('hospital/vac/timed-sub/', views.timedSub, name='timed-sub'),
]