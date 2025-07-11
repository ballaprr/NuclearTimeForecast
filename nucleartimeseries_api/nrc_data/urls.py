from django.contrib import admin
from django.urls import path
from nrc_data.views import ReactorView

urlpatterns = [
    path('reactor/<str:report_date>/', ReactorView.as_view(), name='reactor-detail'),
]
