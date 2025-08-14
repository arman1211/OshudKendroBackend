import random
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


from inventory.models import Inventory, Batch, Medicine
from users.models.organization import (
    Organization,
)  # Make sure this import path is correct


class Command(BaseCommand):
    """
    Django command to populate inventory with a specified number of medicines.

    This command will:
    1. Select 400 random medicines from the database.
    2. Create an Inventory entry for each medicine for a given Organization.
    3. Create two distinct Batch entries for each Inventory item with random data.
    """

    help = "Populates the inventory with 400 medicines, creating two batches for each."

    def add_arguments(self, parser):
        """
        Adds the command-line arguments for the management command.
        """
        parser.add_argument(
            "organization_id",
            type=int,
            help="The ID of the Organization to add inventory to.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """
        The main logic for the management command.
        """
        organization_id = options["organization_id"]
        num_medicines_to_add = 400

        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            raise CommandError(
                f'Organization with ID "{organization_id}" does not exist.'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting to populate inventory for organization: "{organization.name}"'
            )
        )

        # Fetch all medicine IDs and randomly select 400
        medicine_ids = list(Medicine.objects.values_list("id", flat=True))

        if len(medicine_ids) < num_medicines_to_add:
            self.stdout.write(
                self.style.WARNING(
                    f"Found only {len(medicine_ids)} medicines, will populate all of them."
                )
            )
            num_medicines_to_add = len(medicine_ids)

        random_medicine_ids = random.sample(medicine_ids, num_medicines_to_add)
        medicines = Medicine.objects.filter(pk__in=random_medicine_ids)

        count = 0
        for medicine in medicines:
            # Get or create the main inventory entry for the medicine
            inventory, created = Inventory.objects.get_or_create(
                medicine=medicine,
                organization=organization,
                defaults={"stock_alert_qty": random.randint(10, 50)},
            )

            if not created:
                self.stdout.write(
                    self.style.NOTICE(
                        f'Inventory for "{medicine.name}" already exists. Skipping.'
                    )
                )
                continue

            # --- Create the first batch ---
            batch1_qty = random.randint(20, 150)
            buy_price1 = Decimal(random.uniform(15.50, 500.00)).quantize(
                Decimal("0.01")
            )

            Batch.objects.create(
                inventory=inventory,
                buying_price=buy_price1,
                selling_price=buy_price1
                + Decimal(random.uniform(5.0, 50.0)).quantize(Decimal("0.01")),
                batch_number=f"B{random.randint(100000, 999999)}",
                quantity=batch1_qty,
                alert_quantity=random.randint(5, 20),
                expiry_date=datetime.date.today()
                + datetime.timedelta(
                    days=random.randint(180, 730)
                ),  # 6 months to 2 years
            )

            # --- Create the second batch ---
            batch2_qty = random.randint(20, 150)
            buy_price2 = Decimal(random.uniform(15.50, 500.00)).quantize(
                Decimal("0.01")
            )

            Batch.objects.create(
                inventory=inventory,
                buying_price=buy_price2,
                selling_price=buy_price2
                + Decimal(random.uniform(5.0, 50.0)).quantize(Decimal("0.01")),
                batch_number=f"B{random.randint(100000, 999999)}",
                quantity=batch2_qty,
                alert_quantity=random.randint(5, 20),
                expiry_date=datetime.date.today()
                + datetime.timedelta(days=random.randint(731, 1460)),  # 2 to 4 years
            )

            # Update the total quantity in the main inventory record
            inventory.quantity = batch1_qty + batch2_qty
            inventory.save()

            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"({count}/{num_medicines_to_add}) Successfully created inventory and two batches for: {medicine.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully populated the inventory for {count} new medicines in organization "{organization.name}".'
            )
        )
