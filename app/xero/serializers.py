from rest_framework import serializers
from core.models import Account

class XeroSerializer(serializers.ModelSerializer):
    """Serializer for the xero object"""

    class Meta:
        model = Account
        fields = ('id', 'is_authenticated')
        read_only_fields = ('id', 'is_authenticated')