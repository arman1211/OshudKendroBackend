from ..serializers.category_generic_name import (
    CategorySerializer,
    GenericNameSerializer,
)
from rest_framework import viewsets
from ..models.product import Category, GenericName


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class GeniricNameViewset(viewsets.ModelViewSet):
    queryset = GenericName.objects.all()
    serializer_class = GenericNameSerializer
    pagination_class = None
