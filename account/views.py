import logging
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Prefetch
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import User, MakeYourProfilePop
from .serializers import (
    SignupSerialzier,
    VerifyOTPSerializer,
    ResendVerifyOTPSerializer,
    LoginSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    VerifyForgetPasswordOTPSerializer,
    UpdateProfileSerializer,
    MakeYourProfilePopSerializer,
    UserSerializer,
    WhoLikedUserSerializer,
)
from .services import UserLikeService
from account.utils import generate_tokens_for_user
from core.utils import ResponseHandler

logger = logging.getLogger(__name__)

# Create your views here.
class RegisterAPIView(APIView):

    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = SignupSerialzier(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return ResponseHandler.created(
            message="Registration successful. OTP sent via SMS.",
            data={
                "user_id": user.user_id,
                "email": user.email,
                "phone": user.phone,
                'username': user.username,
                "is_verified": user.is_verified
            }
        )



class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = generate_tokens_for_user(user)
        return ResponseHandler.success(
            message="Email verified successfully.",
            data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": {
                    "id": user.user_id,
                    "email": user.email,
                    "full_name": user.get_full_name() if hasattr(user, "get_full_name") else None,
                },
            },
            status_code=status.HTTP_200_OK,
        )


class ResendVerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendVerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ResponseHandler.success(
            message="A new OTP has been sent to your email."
            
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = generate_tokens_for_user(user)

        user_data = UserSerializer(user).data

        return ResponseHandler.success(
            message="Login successful",
            data={
                "user": user_data,
                "tokens": tokens
            }
        )



class ForgetPasswordView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        """Send OTP to admin email."""
        serializer = ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseHandler.success(
                message="OTP sent to user email successfully."
            )
        return ResponseHandler.bad_request(
            message="Failed to send OTP.",
            errors=serializer.errors
        )


class VerifyForgetPasswordOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify OTP and return access token."""
        serializer = VerifyForgetPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            response_data = serializer.to_representation(serializer.validated_data)
            return ResponseHandler.success(
                message="OTP verified successfully.",
                data=response_data
            )
        return ResponseHandler.bad_request(
            message="OTP verification failed.",
            errors=serializer.errors
        )


class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Reset password after verifying OTP (requires token)."""
        serializer = ResetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return ResponseHandler.success(
                message="Password reset successfully."
            )
        return ResponseHandler.bad_request(
            message="Password reset failed.",
            errors=serializer.errors
        )


# Update Profile

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def put(self, request):
        """Full update of user profile."""
        try:
            user = request.user
            serializer = UpdateProfileSerializer(user, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return ResponseHandler.updated(
                message="Profile fully updated successfully.",
                data=serializer.data,
            )

        except ValidationError as e:
            return ResponseHandler.bad_request(
                message="Invalid data provided.",
                errors=e.detail
            )
        except User.DoesNotExist:
            return ResponseHandler.not_found("User not found.")
        except Exception as e:
            return ResponseHandler.generic_error(
                message="Unexpected error occurred while updating profile.",
                exception=e
            )

    @transaction.atomic
    def patch(self, request):
        """Partial update of user profile."""
        try:
            user = request.user
            serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            user_data = UserSerializer(user).data

            return ResponseHandler.updated(
                message="Profile partially updated successfully.",
                data={
                    "user": user_data
                }
            )

        except ValidationError as e:
            return ResponseHandler.bad_request(
                message="Invalid data provided.",
                errors=e.detail
            )
        except User.DoesNotExist:
            return ResponseHandler.not_found("User not found.")
        except Exception as e:
            return ResponseHandler.generic_error(
                message="Unexpected error occurred while updating profile.",
                exception=e
            )
    
    
    # def patch(self, request):
    #     try:
    #         user = request.user
    #         serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
            
    #         from .serializers import UserSerializer
    #         full_serializer = UserSerializer(user)

    #         return ResponseHandler.updated(
    #             message="Profile partially updated successfully.",
    #             data=full_serializer.data,
    #         )

    #     except ValidationError as e:
    #         return ResponseHandler.bad_request(
    #             message="Invalid data provided.",
    #             errors=e.detail
    #         )
    #     except User.DoesNotExist:
    #         return ResponseHandler.not_found("User not found.")
    #     except Exception as e:
    #         return ResponseHandler.generic_error(
    #             message="Unexpected error occurred while updating profile.",
    #             exception=e
    #         )



# Pop Image Views

class PopImageListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        images = MakeYourProfilePop.objects.filter(user=request.user)
        serializer = MakeYourProfilePopSerializer(images, many=True)
        return ResponseHandler.success(data=serializer.data, message="Pop images fetched successfully")

    def post(self, request):
        images = request.FILES.getlist("image")  # getlist for multiple files
        saved_images = []

        if request.user.pop_images.count() + len(images) > 7:
            return ResponseHandler.bad_request(
                message="You can upload a maximum of 7 pop-up images."
            )

        for img in images:
            serializer = MakeYourProfilePopSerializer(
                data={"image": img}, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            saved_images.append(serializer.data)

        return ResponseHandler.created(
            data=saved_images, message=f"{len(saved_images)} pop images uploaded successfully"
        )


class PopImageRetrieveUpdateDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(MakeYourProfilePop, pk=pk, user=user)

    def get(self, request, pk):
        image = self.get_object(pk, request.user)
        serializer = MakeYourProfilePopSerializer(image)
        return ResponseHandler.success(data=serializer.data, message="Pop image fetched successfully")

    def put(self, request, pk):
        image = self.get_object(pk, request.user)
        serializer = MakeYourProfilePopSerializer(
            image, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ResponseHandler.updated(data=serializer.data, message="Pop image updated successfully")

    def delete(self, request, pk):
        image = self.get_object(pk, request.user)
        image.delete()
        return ResponseHandler.deleted(message="Pop image deleted successfully")




# Global Feed View

class GlobalFeedPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

class GlobalFeedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user

            users_qs = User.objects.filter(is_active=True).exclude(pk=current_user.pk).only(
                "user_id", "username", "full_name", "is_online", "hobbies"
            )

            paginator = GlobalFeedPagination()
            page = paginator.paginate_queryset(users_qs, request)

            feed_data = []
            for user in page:
                # Only last updated pop image
                last_image = user.pop_images.order_by("-updated_at").first()
                pop_images_serialized = MakeYourProfilePopSerializer(
                    [last_image], many=True, context={"request": request}
                ).data if last_image else []

                feed_data.append({
                    "user_id": user.user_id,
                    "username": user.username or "",
                    "full_name": user.full_name or "",
                    "is_online": user.is_online,
                    "hobbies": user.hobbies or [],
                    "pop_images": pop_images_serialized,
                })

            return ResponseHandler.success(
                message="Global feed fetched successfully.",
                data=paginator.get_paginated_response(feed_data).data
            )

        except Exception as exc:
            return ResponseHandler.server_error(
                message="Failed to fetch global feed.",
                errors=str(exc)
            )
            
            
# get a user profile by username
class UserDetailsProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, identifier):
        """
        Fetch user by username (str) or user_id (int).
        """
        try:
            # Determine if identifier is numeric (user_id) or string (username)
            if identifier.isdigit():
                user = get_object_or_404(User, user_id=int(identifier), is_active=True)
            else:
                user = get_object_or_404(User, username=identifier, is_active=True)

            serializer = UserSerializer(user, context={"request": request})
            return ResponseHandler.success(
                message="User profile fetched successfully.",
                data=serializer.data
            )

        except Exception as exc:
            return ResponseHandler.server_error(
                message="Failed to fetch user profile.",
                errors=str(exc)
            )


# Like/Unlike Views using UserLikeService



class LikeUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            UserLikeService.like_user(request.user, user_id)
            return ResponseHandler.success(message="User liked.", data={"liked": True})
        except ValueError as e:
            return ResponseHandler.bad_request(message=str(e))
        except Exception as e:
            logger.exception("Error liking user")
            return ResponseHandler.generic_error(exception=e)

class UnlikeUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            UserLikeService.unlike_user(request.user, user_id)
            return ResponseHandler.success(message="User unliked.", data={"liked": False})
        except ValueError as e:
            return ResponseHandler.bad_request(message=str(e))
        except Exception as e:
            logger.exception("Error unliking user")
            return ResponseHandler.generic_error(exception=e)


# who liked
from .serializers import WhoLikedUserSerializer
from rest_framework.pagination import PageNumberPagination

CACHE_TTL = 60 * 0.5  # 30 seconds

class WhoLikedUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        user = request.user
        user_id = user.user_id  # FIXED: your PK

        paginator = self.pagination_class()

        try:
            page_number = request.query_params.get(paginator.page_query_param, "1")
            page_size = paginator.get_page_size(request) or paginator.page_size or 20

            cache_key = f"who_liked:{user_id}:page:{page_number}:size:{page_size}"
            cached_payload = cache.get(cache_key)

            if cached_payload:
                logger.info("who-liked-me cache hit", extra={"user_id": user_id})
                return ResponseHandler.success(
                    message=f"{cached_payload['pagination']['count']} users liked your profile.",
                    data=cached_payload["results"],
                    extra={"pagination": cached_payload["pagination"]},
                )

            qs = UserLikeService.who_liked_user(user_id)

            # DRF safely paginates
            page = paginator.paginate_queryset(qs, request, view=self)

            # If paginated -> `page` is a list of results
            serialized = WhoLikedUserSerializer(page, many=True).data

            # SAFELY get total count (works even if paginator.page does not exist)
            try:
                total_count = qs.count()
            except Exception:
                total_count = len(qs)

            pagination = {
                "count": total_count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "page": int(page_number),
                "page_size": page_size,
            }

            payload = {
                "results": serialized,
                "pagination": pagination,
            }

            try:
                cache.set(cache_key, payload, CACHE_TTL)
            except Exception:
                logger.warning("Failed to set cache", extra={"user_id": user_id})

            logger.info(
                "who-liked-me fetched",
                extra={"user_id": user_id, "count": total_count},
            )

            return ResponseHandler.success(
                message=f"{total_count} users liked your profile.",
                data=serialized,
                extra={"pagination": pagination},
            )

        except Exception as exc:
            logger.exception("Error fetching who-liked-me", extra={"user_id": user_id})
            return ResponseHandler.generic_error(exception=exc)





# search and filter apis

CACHE_TTL = 60  # seconds

class UserSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            query = request.query_params.get("q", "").strip()
            if not query:
                return ResponseHandler.bad_request(message="Query param 'q' is required.")

            cache_key = f"user_search:{query}"
            users = cache.get(cache_key)

            if not users:
                users = User.objects.filter(
                    Q(username__icontains=query) |
                    Q(full_name__icontains=query) |
                    Q(email__icontains=query)
                ).order_by("-created_at")[:50]
                cache.set(cache_key, users, CACHE_TTL)

            serializer = WhoLikedUserSerializer(users, many=True, context={"request": request})
            return ResponseHandler.success(data=serializer.data)

        except Exception as e:
            return ResponseHandler.generic_error(exception=e)


class UserFilterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            gender = request.query_params.get("gender")
            min_age = request.query_params.get("min_age")
            max_age = request.query_params.get("max_age")
            max_distance = request.query_params.get("max_distance")

            filters = Q()
            if gender:
                filters &= Q(gender=gender)
            if min_age and max_age:
                filters &= Q(age__gte=int(min_age), age__lte=int(max_age))
            elif min_age:
                filters &= Q(age__gte=int(min_age))
            elif max_age:
                filters &= Q(age__lte=int(max_age))
            if max_distance:
                filters &= Q(distance__lte=int(max_distance))

            cache_key = f"user_filter:{gender}:{min_age}:{max_age}:{max_distance}"
            users = cache.get(cache_key)

            if not users:
                users = User.objects.filter(filters).order_by("-created_at")[:50]
                cache.set(cache_key, users, CACHE_TTL)

            serializer = WhoLikedUserSerializer(users, many=True, context={"request": request})
            return ResponseHandler.success(data=serializer.data)

        except Exception as e:
            return ResponseHandler.generic_error(exception=e)
