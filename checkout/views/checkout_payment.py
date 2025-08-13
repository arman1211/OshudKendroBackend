from rest_framework import generics, status
from rest_framework.response import Response
from ..serializers.checkout_payment import MakePaymentSerializer, PaymentSerializer
from ..serializers.ordercheck import CheckoutOrderSerializer


class MakePaymentView(generics.CreateAPIView):
    """Make a payment for a customer's due order"""

    serializer_class = MakePaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        # Return payment details with updated order info
        payment_data = PaymentSerializer(payment).data
        order_data = CheckoutOrderSerializer(payment.checkout_order).data

        return Response(
            {
                "payment": payment_data,
                "updated_order": order_data,
                "message": "Payment recorded successfully",
            },
            status=status.HTTP_201_CREATED,
        )
