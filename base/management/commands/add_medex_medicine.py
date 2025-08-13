import os
import csv
import ast
from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Medicine, Category, GenericName
from django.db import transaction


class Command(BaseCommand):
    help = "Imports medicines from a CSV file and saves to the Medicine model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", type=str, help="Path to the CSV file (relative to BASE_DIR)"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options["file"]
        if not file_path:
            self.stdout.write(self.style.ERROR("Please provide the --file argument."))
            return

        full_path = os.path.join(settings.BASE_DIR, file_path)

        if not os.path.exists(full_path):
            self.stdout.write(self.style.ERROR(f"File not found: {full_path}"))
            return

        with open(full_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            skipped = 0

            for row in reader:
                try:
                    name = row.get("Brand", "").strip()
                    if not name:
                        skipped += 1
                        continue

                    generic_text = row.get("Generic", "").strip()
                    if not generic_text:
                        skipped += 1
                        continue

                    # Get or create GenericName
                    generic_obj, _ = GenericName.objects.get_or_create(
                        name=generic_text
                    )

                    # Get category from 'Dosage Form'
                    category_name = row.get("Dosage Form", "").strip()
                    category_obj = None
                    if category_name:
                        category_obj, _ = Category.objects.get_or_create(
                            name=category_name
                        )

                    # dosage = Strength
                    dosage = row.get("Strength", "").strip()
                    dosage_form = dosage  # Strength → dosage_form field

                    # Parse Packages
                    packages_str = row.get("Packages", "")
                    strips_per_box = 0
                    pieces_per_strip = 0

                    try:
                        package_data = ast.literal_eval(packages_str)
                        if isinstance(package_data, list) and len(package_data) > 0:
                            package = package_data[0]
                            strips_per_box = int(package.get("strips_per_box", 0))
                            pieces_per_strip = int(package.get("pieces_per_strip", 0))
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"Invalid package data for {name}: {e}")
                        )

                    pieces_per_box = strips_per_box * pieces_per_strip

                    Medicine.objects.create(
                        name=name,
                        generic_name=generic_obj,
                        category=category_obj,
                        dosage=dosage,
                        brand=name,
                        dosage_form=dosage_form,
                        strips_per_box=strips_per_box,
                        pieces_per_strip=pieces_per_strip,
                        pieces_per_box=pieces_per_box,
                        is_verified=True,
                    )

                    count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to import row: {row}\nError: {e}")
                    )
                    skipped += 1

            self.stdout.write(
                self.style.SUCCESS(f"✅ Imported {count} medicines successfully.")
            )
            if skipped:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Skipped {skipped} rows due to errors or missing data."
                    )
                )
