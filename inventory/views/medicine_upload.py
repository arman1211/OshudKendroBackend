import json
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from inventory.models import Medicine, GenericName, Category

class MedicineCreateView(APIView):

    def create_medicine(self, name, generic, category, dosage, brand, dosage_form, strips, pieces):
        if Medicine.objects.filter(name=name).exists():
          return None
        return Medicine.objects.create(
            name=name,
            generic_name=generic,
            category=category,
            dosage=dosage,
            brand=brand,
            dosage_form=dosage_form,
            strips_per_box=strips,
            pieces_per_strip=pieces,
            pieces_per_box=strips * pieces,
        )

    def extract_pack_suffix(self, pack_info):
        match = re.search(r"\((\d+)\s*x\s*(\d+)", pack_info)
        return f" {match.group(1)}x{match.group(2)}" if match else ''

    def post(self, request):
        data = request.data
        base_name = data.get('Brand', '').strip() or data.get('Generic', '').strip()
        generic_str = data.get('Generic', '').strip()
        brand = data.get('Brand', '').strip()
        dosage = data.get('Strength', '').strip()
        dosage_form = data.get('Dosage Form', '').strip()

        # Related objects
        generic_name_obj, _ = GenericName.objects.get_or_create(name=generic_str)
        category_obj = None  # Add logic if needed

        # Parse package data
        try:
            packages = json.loads(data.get('Packages', '[]'))
            if not isinstance(packages, list) or not packages:
                raise ValueError("Packages must be a non-empty list")
        except Exception as e:
            return Response({"error": f"Invalid package data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        created_meds = []

        for i, pkg in enumerate(packages):
            strips = int(pkg.get('strips_per_box') or 0)
            pieces = int(pkg.get('pieces_per_strip') or 0)
            pack_info = pkg.get('pack_info', '')

            # Append pack info only if multiple packages
            suffix = self.extract_pack_suffix(pack_info) if len(packages) > 1 else ''
            full_name = f"{base_name}{suffix}"

            medicine = self.create_medicine(
                name=full_name,
                generic=generic_name_obj,
                category=category_obj,
                dosage=dosage,
                brand=brand,
                dosage_form=dosage_form,
                strips=strips,
                pieces=pieces
            )
            created_meds.append(medicine)

        return Response(None, status=status.HTTP_201_CREATED)