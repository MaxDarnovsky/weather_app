from rest_framework import serializers
from .models import SearchHistory

class CityStatsSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField()

    class Meta:
        model = SearchHistory
        fields = ['city', 'count']