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
