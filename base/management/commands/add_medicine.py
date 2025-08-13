from django.core.management.base import BaseCommand
from inventory.models import Medicine, Category, GenericName
from base.management.commands.med_scraper import scrape_all_pages, save_to_json
from django.db import transaction
import json
import os
from django.conf import settings
import re


class Command(BaseCommand):
    help = "Import scraped MedEasy products into the Medicine model"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        json_path = os.path.join(settings.BASE_DIR, "medeasy_products.json")

        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"JSON file not found: {json_path}"))
            return

        with open(json_path, "r", encoding="utf-8") as f:
            products = json.load(f)

        self.stdout.write(f"Loaded {len(products)} products from JSON.")

        added = 0
        skipped = 0

        for product in products:
            name = product.get("medicine_name")
            generic_name = product.get("generic_name")

            if not name or not generic_name:
                skipped += 1
                continue

            generic_name_clean = generic_name.strip()[:100]  # Truncate to 100 chars
            generic_obj, _ = GenericName.objects.get_or_create(name=generic_name_clean)

            category_name = product.get("category_name")
            category_obj = None
            if category_name:
                category_obj, _ = Category.objects.get_or_create(
                    name=category_name.strip()
                )

            dosage = product.get("strength") or ""
            unit_prices = product.get("unit_prices", [])
            dosage_form = None
            if dosage:
                parts = dosage.split(" ", 1)
                if len(parts) == 2:
                    dosage, dosage_form = parts[0], parts[1]

            pieces_per_strip, strips_per_box, pieces_per_box = parse_packaging_info(
                unit_prices
            )
            print(
                f"Final pieces info for {name}: {pieces_per_strip} pieces/strip, {strips_per_box} strips/box, {pieces_per_box} pieces/box"
            )

            med_obj, created = Medicine.objects.update_or_create(
                name=name.strip(),
                generic_name=generic_obj,
                defaults={
                    "category": category_obj,
                    "dosage": dosage,
                    "dosage_form": dosage_form,
                    "brand": product.get("manufacturer_name"),
                    "pieces_per_strip": pieces_per_strip,
                    "strips_per_box": strips_per_box,
                    "pieces_per_box": pieces_per_box,
                },
            )
            added += 1 if created else 0

        self.stdout.write(
            self.style.SUCCESS(f"Imported {added} new medicines. Skipped {skipped}.")
        )


def parse_packaging_info(unit_prices):
    if not unit_prices or not isinstance(unit_prices, list):
        return 0, 0, 0

    # Sort units by size to process from smallest to largest package
    sorted_units = sorted(unit_prices, key=lambda x: x.get("unit_size", 0))

    # --- Case 1: Only one packaging option is available ---
    if len(sorted_units) == 1:
        unit = sorted_units[0]
        unit_name = unit.get("unit", "").lower()
        unit_size = unit.get("unit_size", 0)

        # Check for quantity in the name, e.g., "75's Box", which implies 75 pieces.
        match = re.search(r"(\d+)\'s", unit_name)
        if match and ("pack" in unit_name or "box" in unit_name):
            return 0, 0, int(match.group(1))

        # Check if it's a strip sold individually.
        if "strip" in unit_name:
            return unit_size, 0, 0  # Pcs/Strip, no strips/box, no pcs/box

        # Otherwise, assume it's a single item (tube, bottle, inhaler).
        return 0, 0, 1

    # --- Case 2: Multiple packaging options exist ---
    piece_info = None
    strip_info = None
    box_info = None

    # Identify the role of each unit based on keywords.
    # The largest pack/box will be assigned last due to sorting.
    for unit in sorted_units:
        unit_name = unit.get("unit", "").lower()
        if "strip" in unit_name:
            strip_info = unit
        elif "pack" in unit_name or "box" in unit_name:
            box_info = unit
        elif unit.get("unit_size") == 1:
            piece_info = unit

    pieces_per_strip = 0
    strips_per_box = 0
    pieces_per_box = 0

    # Determine the packaging structure based on what was found.
    if strip_info and box_info:
        # Structure: Strip -> Box (Standard for tablets/capsules).
        pps = strip_info.get("unit_size", 0)
        ppb = box_info.get("unit_size", 0)

        if pps > 0 and ppb > 0 and ppb % pps == 0:
            pieces_per_strip = pps
            pieces_per_box = ppb
            strips_per_box = ppb // pps
        else:
            # Data is inconsistent, treat as a box of loose pieces.
            pieces_per_box = ppb

    elif piece_info and box_info and not strip_info:
        # Structure: Piece -> Box (Box of loose items like sachets or drops).
        pieces_per_box = box_info.get("unit_size", 0)

    elif box_info:
        # Fallback if only a box is identified.
        pieces_per_box = box_info.get("unit_size", 0)

    return pieces_per_strip, strips_per_box, pieces_per_box


# def parse_packaging_info(unit_prices):
#     """
#     Improved packaging parser that handles various unit price structures
#     """
#     pieces_per_strip = 0
#     strips_per_box = 0
#     pieces_per_box = 0

#     if not unit_prices or not isinstance(unit_prices, list):
#         return pieces_per_strip, strips_per_box, pieces_per_box

#     # print("Processing unit_prices:", unit_prices)

#     # Sort by unit_size for consistent processing
#     sorted_units = sorted(unit_prices, key=lambda x: x.get("unit_size", 0))

#     # Find different unit types
#     piece_price = None
#     strip_info = None
#     pack_info = None

#     for unit in sorted_units:
#         unit_size = unit.get("unit_size", 0)
#         unit_name = unit.get("unit", "").lower()
#         price = unit.get("price", 0)

#         # print(f"Processing: {unit_name} - Size: {unit_size} - Price: {price}")

#         # Identify piece price (size = 1)
#         if unit_size == 1 and ("piece" in unit_name or "pcs" in unit_name):
#             piece_price = price
#             # print(f"Found piece price: {piece_price}")

#         # Identify strip information
#         elif "strip" in unit_name and unit_size > 1:
#             strip_info = {"size": unit_size, "price": price, "unit": unit_name}
#             # print(f"Found strip info: {strip_info}")

#         # Identify pack/box information
#         elif ("pack" in unit_name or "box" in unit_name) and unit_size > 1:
#             if not pack_info or unit_size > pack_info["size"]:
#                 pack_info = {"size": unit_size, "price": price, "unit": unit_name}
#                 # print(f"Found pack info: {pack_info}")

#     # Calculate pieces_per_strip
#     if strip_info:
#         pieces_per_strip = strip_info["size"]
#         # print(f"Pieces per strip from strip info: {pieces_per_strip}")
#     elif piece_price and len(sorted_units) > 1:
#         # If no explicit strip, use the next smallest unit
#         next_unit = next((u for u in sorted_units if u.get("unit_size", 0) > 1), None)
#         if next_unit and not (
#             "pack" in next_unit.get("unit", "").lower()
#             and next_unit.get("unit_size", 0) > 50
#         ):
#             pieces_per_strip = next_unit.get("unit_size", 0)
#             # print(f"Pieces per strip inferred from next unit: {pieces_per_strip}")

#     # Calculate pieces_per_box
#     if pack_info:
#         pieces_per_box = pack_info["size"]
#         # print(f"Pieces per box from pack info: {pieces_per_box}")

#     # Calculate strips_per_box
#     if pieces_per_strip > 0 and pieces_per_box > 0:
#         strips_per_box = pieces_per_box // pieces_per_strip
#         # print(f"Strips per box calculated: {strips_per_box}")
#     elif pieces_per_strip > 0 and not pack_info and len(sorted_units) > 2:
#         # Check if there's a larger unit that could be a box
#         largest_unit = sorted_units[-1]
#         if largest_unit.get("unit_size", 0) > pieces_per_strip:
#             pieces_per_box = largest_unit.get("unit_size", 0)
#             strips_per_box = pieces_per_box // pieces_per_strip
#             # print(
#             #     f"Inferred box from largest unit: {pieces_per_box} pieces, {strips_per_box} strips"
#             # )

#     # Handle medicines without strips (loose packaging)
#     if pieces_per_strip == 0 and pieces_per_box > 0:
#         # This is loose packaging - no strips, just pieces in a box
#         strips_per_box = 0  # No strips
#         # print("Detected loose packaging - no strips")

#     return pieces_per_strip, strips_per_box, pieces_per_box
