from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import status
from ..models.user import User
from ..serializers.user import UserSerializer,RegisterSerializer,PasswordResetRequestSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
import random
from django.contrib.auth.hashers import make_password

class RegisterView(CreateAPIView):
    permission_classes=[AllowAny]
    queryset=User.objects.all()
    serializer_class=RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        send_mail(
            subject="Email Verification Code",
            message=f"Your email verification code is: {user.email_verification_code}",
            from_email="promitchowdhury84@gmail.com",
            recipient_list=[user.email],
            fail_silently=False,
        )

    
class LoginView(APIView):
    @swagger_auto_schema(
        operation_description="Login using email and password to obtain tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            },
            required=['email', 'password']
        ),
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user_info': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

class EmailVerifyView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify email with code",
        manual_parameters=[
            openapi.Parameter(
                'email', openapi.IN_QUERY, description="Email address to verify", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'code', openapi.IN_QUERY, description="Verification code sent to the email", type=openapi.TYPE_STRING
            ),
        ],
    )
    def post(self, request):
        email = request.query_params.get('email')
        code = request.query_params.get('code')

        try:
            user = User.objects.get(email=email)
            if user.email_verification_code == code:
                user.is_email_verified = True
                user.is_active=True
                user.email_verification_code = None
                user.save()
                return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Invalid email address"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    @swagger_auto_schema(
        operation_description="Request a password reset code.",
        request_body=PasswordResetRequestSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            reset_code = str(random.randint(100000, 999999))
            user.reset_code = reset_code
            user.save()

            send_mail(
                subject="Password Reset Code",
                message=f"Your password reset code is: {reset_code}",
                from_email="promitchowdhury84@gmail.com",
                recipient_list=[user.email],
            )

            return Response({"detail": "Password reset code sent to email."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class PasswordResetView(APIView):
    @swagger_auto_schema(
        operation_summary="Reset Password",
        operation_description="Reset a user's password using their email, reset code, and new password.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'code', 'new_password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The user's email address.",
                    example="user@example.com",
                ),
                'code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The reset code sent to the user's email.",
                    example="123456",
                ),
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The new password for the user.",
                    example="StrongPassword123!",
                ),
            },
        ),
    )

    def post(self, request):

        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not email or not code or not new_password:
            return Response(
                {"error": "Email, code, and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)

            if user.reset_code != code:
                return Response(
                    {"error": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST
                )

            user.password = make_password(new_password)
            user.reset_code = None
            user.save()

            return Response({"success": "Password reset successfully."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"error": "User with the given email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )