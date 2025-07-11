from django.shortcuts import render
from .serializers import ReactorSerializer, ReactorDetailSerializer
from .models import Reactor, ReactorStatus, ReactorForecast, StubOutage
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# Create your views here.
class ReactorView(APIView):
    def get(self, request, report_date):
        if not report_date:
            return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        reactors = Reactor.objects.filter(reactorstatus__report_date=report_date).distinct()

        serializer = ReactorSerializer(reactors, many=True, context={'report_date': report_date})
        return Response(serializer.data)

class ReactorDetailView(APIView):
    def get(self, request, report_date, reactor_id):
        if not report_date:
            return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        reactor = Reactor.objects.get(id=reactor_id)
        reactorstatus = ReactorStatus.objects.get(reactor=reactor, report_date=report_date)
        serializer = ReactorDetailSerializer(reactorstatus)
        return Response(serializer.data)