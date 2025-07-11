from django.contrib import admin
from django.urls import path
from nrc_data.views import ReactorView, ReactorDetailView

urlpatterns = [
    path('reactor/<str:report_date>/', ReactorView.as_view()),
    path('reactor/<str:report_date>/<int:reactor_id>/', ReactorDetailView.as_view()),
]
