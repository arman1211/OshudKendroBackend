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
    3. Create two distinct Batch entries for each Inventory item.
    4. Set expiry dates within the next 6 months to simulate near-expiry alerts.
    5. Set prices based on a per-piece cost between 3 and 50 BDT.
    """

    help = "Populates inventory with 400 medicines, with batches expiring in the next 6 months."

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

            # Generate two unique expiry day offsets to ensure batches have different dates
            expiry_days = random.sample(range(1, 181), 2)

            # --- Create the first batch ---
            batch1_qty = random.randint(5, 150)
            # UPDATED: Price set between 3 and 50
            buy_price1 = Decimal(random.uniform(3.0, 50.0)).quantize(Decimal("0.01"))

            Batch.objects.create(
                inventory=inventory,
                buying_price=buy_price1,
                selling_price=buy_price1
                + Decimal(random.uniform(2.0, 15.0)).quantize(Decimal("0.01")),
                batch_number="BATCH-A",
                quantity=batch1_qty,
                alert_quantity=random.randint(5, 20),
                # UPDATED: Expiry set to 1-180 days from now
                expiry_date=datetime.date.today()
                + datetime.timedelta(days=expiry_days[0]),
            )

            # --- Create the second batch ---
            batch2_qty = random.randint(5, 150)
            # UPDATED: Price set between 3 and 50
            buy_price2 = Decimal(random.uniform(3.0, 50.0)).quantize(Decimal("0.01"))

            Batch.objects.create(
                inventory=inventory,
                buying_price=buy_price2,
                selling_price=buy_price2
                + Decimal(random.uniform(2.0, 15.0)).quantize(Decimal("0.01")),
                batch_number="BATCH-B",
                quantity=batch2_qty,
                alert_quantity=random.randint(5, 20),
                # UPDATED: Expiry set to 1-180 days from now, different from the first batch
                expiry_date=datetime.date.today()
                + datetime.timedelta(days=expiry_days[1]),
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
