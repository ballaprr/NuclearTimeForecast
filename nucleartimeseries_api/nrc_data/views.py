from django.shortcuts import render
from .serializers import ReactorSerializer
from .models import Reactor
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