from rest_framework import serializers

from ..models import *


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    slug = serializers.SlugField()

    class Meta:
        model = Categories
        fields = ['id','name', 'slug']
