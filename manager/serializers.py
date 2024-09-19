from .models import FAQ, Admin
from rest_framework import serializers


# FAQ Serializer
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
