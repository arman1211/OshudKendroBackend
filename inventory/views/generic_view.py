from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from inventory.models.product import Category, GenericName
from inventory.serializers.category_generic_name import CategorySerializer, GenericNameSerializer
from rest_framework.permissions import IsAuthenticated

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class=None

class GenericNameViewSet(viewsets.ModelViewSet):
    queryset = GenericName.objects.all()
    serializer_class = GenericNameSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description='Search by generic name (at least 2 characters)',
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        queryset = self.get_queryset()

        if query:
            if len(query) < 2:
                return Response(
                    {"detail": "Please enter at least 2 characters to search."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(Q(name__icontains=query))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
