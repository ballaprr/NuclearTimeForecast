from nrc_data.models import ReactorStatus, ReactorForecast, StubOutage, Reactor
from rest_framework import serializers

class ReactorStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReactorStatus
        fields = '__all__'

class ReactorSerializer(serializers.ModelSerializer):
    reactorstatus = serializers.SerializerMethodField()

    class Meta:
        model = Reactor
        fields = ['name', 'region', 'latitude', 'longitude', 'reactorstatus']

    def get_reactorstatus(self, obj):
        date = self.context.get('report_date')
        reactors = obj.reactorstatus.filter(report_date=date)
        return ReactorStatusSerializer(reactors, many=True).data


# Power (ReactorStatus)
# Status (StubOutage)
# Forecast (ReactorForecast)

class StubOutageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StubOutage
        fields = ['date_detected', 'description', 'auto_detected', 'confirmed']

class ReactorForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReactorForecast
        fields = ['df', 'yhat', 'yhat_lower', 'yhat_upper', 'image_url']

class ReactorDetailSerializer(serializers.ModelSerializer):
    reactorforecast_set = ReactorForecastSerializer(many=True)
    stuboutage_set = StubOutageSerializer(many=True)
    class Meta:
        model = ReactorStatus
        fields = ['report_date', 'unit', 'power', 'reactorforecast_set', 'stuboutage_set']