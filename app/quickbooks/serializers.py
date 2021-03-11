from rest_framework import serializers
from core.models import Account

class QuickbooksSerializer(serializers.ModelSerializer):
    """Serializer for the quickbooks object"""

    class Meta:
        model = Account
        fields = ('id', 'is_authenticated')
        read_only_fields = ('id', 'is_authenticated')

# class QuickbooksAuthResponseSerializer(serializers.Serializer):
#     """Custom Serializer for the quickbooks auth response"""
#     code = serializers.CharField()
#     state = serializers.CharField()
#     realmId = serializers.IntegerField()