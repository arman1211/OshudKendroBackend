# # inventory/documents.py

# from django_elasticsearch_dsl import Document, fields
# from django_elasticsearch_dsl.registries import registry
# from .models import Inventory, Medicine, GenericName


# @registry.register_document
# class InventoryDocument(Document):

#     # Nested fields for the related models
#     medicine = fields.ObjectField(
#         properties={
#             "id": fields.IntegerField(),
#             "name": fields.TextField(analyzer="standard"),
#             "brand": fields.TextField(analyzer="standard"),
#             "dosage": fields.TextField(analyzer="standard"),
#             "dosage_form": fields.TextField(analyzer="standard"),
#             "generic_name": fields.ObjectField(
#                 properties={
#                     "id": fields.IntegerField(),
#                     "name": fields.TextField(analyzer="standard"),
#                 }
#             ),
#         }
#     )
#     organization_id = fields.IntegerField(attr="organization_id")

#     class Index:
#         name = "inventories"
#         settings = {"number_of_shards": 1, "number_of_replicas": 0}

#     class Django:
#         model = Inventory

#         # The fields that should be indexed from the Inventory model
#         fields = [
#             "id",
#             "quantity",
#             "selling_price",
#             "stock_alert_qty",
#         ]

#         # A list of related models that should be indexed
#         related_models = [Medicine, GenericName]

#         # This hook is crucial for updating the index when a related model changes
#         def get_queryset(self):
#             return (
#                 super()
#                 .get_queryset()
#                 .select_related("medicine", "medicine__generic_name", "organization")
#             )
