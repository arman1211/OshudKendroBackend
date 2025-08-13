from rest_framework import serializers
from ..models.product import Category, GenericName

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class GenericNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericName
        fields = ['id', 'name']
