from rest_framework import serializers
from .order import OrderSerializer
from ..models.checkout_order import CheckoutOrder, StatusChoice
from ..models.order import Order
from inventory.models.batch import Batch
from users.models import User
from ..models.customer_details import CustomerDetails
from ..serializers.customer_details import CustomerDetailsSerializer
from ..serializers.checkout_payment import PaymentSerializer
from ..models.checkout_payment import Payment


class CheckoutOrderSerializer(serializers.ModelSerializer):
    orders = serializers.SerializerMethodField(read_only=True)
    items = serializers.ListField(write_only=True)
    amount = serializers.DictField(write_only=True)
    pharmacy_name = serializers.CharField(source="pharmacy_shop.name", read_only=True)
    pharmacy_address = serializers.CharField(
        source="pharmacy_shop.address", read_only=True
    )
    employee_first_name = serializers.CharField(
        source="employee.first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee.last_name", read_only=True
    )

    employee_email = serializers.CharField(source="employee.email", read_only=True)

    customer_details = CustomerDetailsSerializer(source="customer", read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CheckoutOrder
        fields = "__all__"
        read_only_fields = ["checkout_price", "created_at", "orders"]

    def get_orders(self, obj):
        return obj.get_orders()

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        amount = validated_data.pop("amount")
        customer_name = validated_data.get("customer_name")
        customer_contact = validated_data.get("customer_contact")
        organization = self.context["request"].user.organization

        # Extract payment details
        final_amount = round(float(amount.get("finalAmount", 0)), 2)
        cash_received = round(float(amount.get("cashReceived", 0)), 2)
        change_amount = round(float(amount.get("changeAmount", 0)), 2)

        # Calculate actual paid amount (cash received minus change)
        actual_paid = cash_received - max(change_amount, 0)
        due_amount = final_amount - actual_paid

        print(
            f"Final Amount: {final_amount}, Cash Received: {cash_received}, Change Amount: {change_amount}, Actual Paid: {actual_paid}, Due Amount: {due_amount}"
        )

        # Determine payment status
        if due_amount <= 0:
            order_status = StatusChoice.COMPLETED
        elif actual_paid > 0:
            order_status = StatusChoice.PARTIALLY_PAID
        else:
            order_status = StatusChoice.PENDING

        # Handle customer details for due/partial payments
        customer_details = None
        if customer_name and customer_contact:
            customer_details, created = CustomerDetails.objects.get_or_create(
                name=customer_name, contact=customer_contact, organization=organization
            )

        # For due payments, customer details are required
        if due_amount > 0 and not customer_details:
            raise serializers.ValidationError(
                "Customer name and contact are required for due payments."
            )

        discount_percentage = float(amount.get("discountPercentage", 0))

        # Create checkout order
        checkout = CheckoutOrder.objects.create(
            **{
                k: v
                for k, v in validated_data.items()
                if k not in ["customer_name", "customer_contact"]
            },
            customer=customer_details,
            customer_name=customer_name,
            customer_contact=customer_contact,
            discount_percentage=discount_percentage,
            status=order_status,
            checkout_price=final_amount,
            paid_amount=actual_paid,
            due_amount=due_amount,
        )

        # Create order items
        for item in items_data:
            batch_id = item.get("selectedBatchId")
            quantity = item.get("selectedUnitItem", 1)
            price_per_unit = float(item.get("selling_price"))
            price_per_piece = float(item.get("per_piece_price"))
            pieces_quantity = item.get("selectedUnitQuantity")

            try:
                batch = Batch.objects.get(id=batch_id)
            except Batch.DoesNotExist:
                raise serializers.ValidationError(
                    f"Batch with id {batch_id} not found."
                )

            # Calculate prices
            subtotal = price_per_unit * quantity
            discount_amount = (discount_percentage / 100) * subtotal
            total_price = subtotal - discount_amount

            # Create order
            Order.objects.create(
                checkout=checkout,
                batch=batch,
                inventory=batch.inventory if hasattr(batch, "inventory") else None,
                quantity=pieces_quantity * quantity,
                price_per_unit=price_per_piece,
                discount=discount_percentage,
                total_price=total_price,
            )

            # Reduce batch quantity
            total_pieces_ordered = pieces_quantity * quantity
            if batch.quantity >= total_pieces_ordered:
                batch.quantity -= total_pieces_ordered
                batch.save()

                # Also update the main inventory quantity if needed
                if batch.inventory:
                    batch.inventory.quantity = sum(
                        b.quantity for b in batch.inventory.batches.all()
                    )
                    batch.inventory.save()
            else:
                raise serializers.ValidationError(
                    f"Insufficient stock for batch {batch_id}. "
                    f"Available: {batch.quantity}, Required: {total_pieces_ordered}"
                )

        # Update total price
        # checkout.update_total_price()

        # Create initial payment record if any payment made
        if actual_paid > 0 and customer_details:
            Payment.objects.create(
                checkout_order=checkout,
                customer=customer_details,
                amount=actual_paid,
                payment_method="cash",
                notes="Initial payment during checkout",
            )

        return checkout
