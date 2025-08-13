from drf_yasg import openapi

search_param = openapi.Parameter(
    'q',
    openapi.IN_QUERY,
    description="Filter medicines by name (case-insensitive)",
    type=openapi.TYPE_STRING,
)

inventory_id = openapi.Parameter(
    'inventory_id',
    openapi.IN_QUERY,
    description="Filter batches by inventory ID",
    type=openapi.TYPE_INTEGER
)