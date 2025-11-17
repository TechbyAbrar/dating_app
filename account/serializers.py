from rest_framework import serializers
from .models import User, MakeYourProfilePop
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.contrib.auth import get_user_model
from .utils import generate_otp, get_otp_expiry, send_otp_email, generate_tokens_for_user, validate_image, generate_username
from .models import User
from rest_framework.exceptions import ValidationError
from rest_framework import serializers



User = get_user_model()
# MakeYourProfilePopSerializer
class MakeYourProfilePopSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MakeYourProfilePop
        fields = ["id", "user", "image", "image_url", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

    def validate(self, attrs):
        user = self.context["request"].user
        if self.instance is None and user.pop_images.count() >= 7:
            raise serializers.ValidationError("You can upload a maximum of 7 pop-up images.")
        return attrs



class UserSerializer(serializers.ModelSerializer):
    pop_images = MakeYourProfilePopSerializer(many=True, read_only=True)
    looking_for = serializers.ListField(
        child=serializers.ChoiceField(choices=User.LOOKING_FOR_CHOICES),
        required=False
    )

    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "phone",
            "username",
            "full_name",
            "profile_pic",
            "profile_pic_url",
            "bio",
            "gender",
            "goal",
            "hoping_to_find",
            "looking_for",
            "height_feet",
            "height_inches",
            "education",
            "hobbies",
            "dob",
            "age",
            "country",
            "state",
            "location",
            "distance",
            "hobbies",
            "is_subscribed",
            "subscription_expiry",
            "is_verified",
            "is_active",
            "is_staff",
            "pop_images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user_id",
            "is_verified",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        """Ensure looking_for renders as list instead of comma string."""
        rep = super().to_representation(instance)
        if isinstance(rep.get("looking_for"), str):
            rep["looking_for"] = rep["looking_for"].split(",") if rep["looking_for"] else []
        return rep

    def validate_looking_for(self, value):
        """Ensure valid selections from predefined choices."""
        valid_choices = [choice[0] for choice in User.LOOKING_FOR_CHOICES]
        for v in value:
            if v not in valid_choices:
                raise serializers.ValidationError(f"Invalid choice: {v}")
        return value




#update profile
class UpdateProfileSerializer(serializers.ModelSerializer):
    hobbies = serializers.ListField(
        child=serializers.ChoiceField(choices=User.HOBBIES_CHOICES),
        required=False
    )
    looking_for = serializers.ListField(
        child=serializers.ChoiceField(choices=User.LOOKING_FOR_CHOICES),
        required=False
    )

    class Meta:
        model = User
        exclude = [
            "email",
            "password",
            "is_subscribed",
            "is_superuser",
            "is_staff",
            "is_active",
            "is_verified",
            "otp",
            "otp_expired",
            "created_at",
            "updated_at",
            "last_login",
            "groups",
            "user_permissions",
        ]

    def validate_dob(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_profile_pic(self, value):
        validate_image(value)
        return value

    def validate_looking_for(self, value):
        valid_choices = [choice[0] for choice in User.LOOKING_FOR_CHOICES]
        for v in value:
            if v not in valid_choices:
                raise serializers.ValidationError(f"Invalid choice: {v}")
        return value
    
    def validate_hobbies(self, value):
        valid_choices = [choice[0] for choice in User.HOBBIES_CHOICES]
        for v in value:
            if v not in valid_choices:
                raise serializers.ValidationError(f"Invalid choice: {v}")
        return value

    def update(self, instance, validated_data):
        # Pop list fields
        hobbies = validated_data.pop("hobbies", None)
        looking_for = validated_data.pop("looking_for", None)

        # Assign normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Assign MultiSelectField values directly
        if hobbies is not None:
            instance.hobbies = hobbies

        if looking_for is not None:
            instance.looking_for = looking_for

        # Auto-calculate age from DOB
        if instance.dob:
            today = timezone.now().date()
            instance.age = (
                today.year
                - instance.dob.year
                - ((today.month, today.day) < (instance.dob.month, instance.dob.day))
            )

        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Ensure lists are returned properly
        for field in ["hobbies", "looking_for"]:
            value = getattr(instance, field)
            if isinstance(value, str):
                rep[field] = value.split(",") if value else []
            elif isinstance(value, list):
                rep[field] = value
            else:
                rep[field] = []
        return rep




        
class SignupSerialzier(serializers.Serializer):
    # full_name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError({"email": "Email already registered."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        if not validated_data.get("username"):
            validated_data["username"] = generate_username(validated_data["email"])

        user = User(**validated_data)
        user.password = make_password(password)

        # Generate OTP
        user.otp = generate_otp()
        user.otp_expired = get_otp_expiry()
        user.save()

        # Send OTP via email/SMS
        message = f"Your verification code is {user.otp}. It expires in 30 minutes."
        send_otp_email(user.email, message)

        return user
    
    
class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(otp=data["otp"], otp_expired__gte=timezone.now())
        except User.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid or expired OTP."})

        if user.is_verified:
            raise serializers.ValidationError({"otp": "User already verified."})

        data["user"] = user
        return data

    def save(self, **kwargs):
        user = self.validated_data["user"]
        from django.db import transaction
        with transaction.atomic():
            user.is_verified = True
            user.otp = None
            user.otp_expired = None
            user.save(update_fields=["is_verified", "otp", "otp_expired"])
        return user
    
    
    
class ResendVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Email not registered."})

        if user.is_verified:
            raise serializers.ValidationError({"email": "User already verified."})

        data["user"] = user
        return data

    def save(self, **kwargs):
        user = self.validated_data["user"]

        # Generate new OTP
        user.otp = generate_otp()
        user.otp_expired = get_otp_expiry()
        user.save(update_fields=["otp", "otp_expired"])

        # Send SMS
        message = f"Your new verification code is {user.otp}. It expires in 30 minutes."
        send_otp_email(user.email, message)

        return user
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError({
                "email": "Email is required.",
                "password": "Password is required."
            })

        user = User.objects.filter(email__iexact=email).first()
        if not user or not user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive."})

        attrs['user'] = user
        return attrs



class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.only('email', 'otp', 'otp_expired').get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("user account not found.")

        self.context['user'] = user
        return value

    def save(self):
        user = self.context['user']
        user.set_otp()
        user.save(update_fields=['otp', 'otp_expired'])
        send_otp_email(user.email, user.otp)
        return user


class VerifyForgetPasswordOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, write_only=True)

    def validate_otp(self, value):
        try:
            user = User.objects.only(
                'user_id', 'email', 'otp', 'otp_expired', 'is_verified'
            ).get(otp=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired OTP.")

        if not user.is_verified:
            raise serializers.ValidationError("user account is not verified. Please, verify your email first.")

        if user.otp_expired is None or user.otp_expired < timezone.now():
            raise serializers.ValidationError("OTP has expired.")

        self.context['user'] = user
        return value

    def create_access_token(self):
        user = self.context['user']
        tokens = generate_tokens_for_user(user)
        return tokens['access']

    def to_representation(self, instance):
        """Custom response after successful OTP verification."""
        user = self.context['user']
        return {
            "success": True,
            "message": "OTP verified successfully.",
            "access_token": self.create_access_token(),
            "user": {
                "user_id": user.user_id,
                "email": user.email,
            },
        }


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new = attrs.get("new_password")
        confirm = attrs.get("confirm_password")

        if new != confirm:
            raise serializers.ValidationError("Passwords do not match.")

        user = self.context["request"].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("otp verification token required.")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
    
    
# who liked user serializer

class WhoLikedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "username", "full_name", "is_online", "hobbies", 'distance']
