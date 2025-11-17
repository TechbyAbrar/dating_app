from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import PrivacyPolicy, AboutUs, TermsConditions, SubmitQuerry, ShareThoughts
from .serializers import (PrivacyPolicySerializer, AboutUsSerializer, TermsConditionsSerializer, SubmitQuerrySerializer, ShareThoughtsSerializer )
from account.permissions import IsSuperUserOrReadOnly
from core.utils import ResponseHandler
from django.db import transaction

class SingleObjectViewMixin:
    """Always returns the first object in the queryset"""
    def get_object(self):
        return self.queryset.first()
    
    
class BaseSingleObjectView(SingleObjectViewMixin, generics.RetrieveUpdateAPIView):

    permission_classes = [IsSuperUserOrReadOnly]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return ResponseHandler.not_found(message="No content found.")
        serializer = self.get_serializer(instance)
        return ResponseHandler.success(
            message="Content retrieved successfully.",
            data=serializer.data,
        )

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            # Update existing object
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHandler.updated(
                    message="Content updated successfully.",
                    data=serializer.data,
                )
            return ResponseHandler.bad_request(
                message="Validation failed.",
                errors=serializer.errors,
            )
        else:
            # Create new object
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHandler.created(
                    message="Content created successfully.",
                    data=serializer.data,
                )
            return ResponseHandler.bad_request(
                message="Validation failed.",
                errors=serializer.errors,
            )

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            # Partial update existing object
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return ResponseHandler.updated(
                    message="Content partially updated successfully.",
                    data=serializer.data,
                )
            return ResponseHandler.bad_request(
                message="Validation failed.",
                errors=serializer.errors,
            )
        else:
            # Create new object since none exists
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHandler.created(
                    message="Content created successfully.",
                    data=serializer.data,
                )
            return ResponseHandler.bad_request(
                message="Validation failed.",
                errors=serializer.errors,
            )



class PrivacyPolicyView(BaseSingleObjectView):
    queryset = PrivacyPolicy.objects.all()
    serializer_class = PrivacyPolicySerializer
    # permission_classes = [IsSuperUserOrReadOnly]

class AboutUsView(BaseSingleObjectView):
    queryset =AboutUs.objects.all()
    serializer_class = AboutUsSerializer
    # permission_classes = [IsSuperUserOrReadOnly]

class TermsConditionsView(BaseSingleObjectView):
    queryset = TermsConditions.objects.all()
    serializer_class = TermsConditionsSerializer
    # permission_classes = [IsSuperUserOrReadOnly]


from rest_framework.views import APIView

class SubmitQuerryView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SubmitQuerrySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return ResponseHandler.created(
                message="user querry submitted successfully!",
                data= serializer.data
            )
            
    def get(self, request):
        # Use .only to fetch only necessary fields, minimizing DB load
        queries = SubmitQuerry.objects.all().only('id', 'name', 'email', 'message', 'created_at')
        serializer = SubmitQuerrySerializer(queries, many=True)
        return ResponseHandler.success(
            message="All queries retrieved successfully.",
            data=serializer.data
        )
        

# ------------------ Retrieve Single Query ------------------ #
class SubmitQuerryDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """
        Retrieve a single query by ID.
        """
        try:
            # Fetch only required fields
            query = SubmitQuerry.objects.only('id', 'name', 'email', 'message', 'created_at').get(pk=pk)
        except SubmitQuerry.DoesNotExist:
            return ResponseHandler.not_found(message="Query not found.")

        serializer = SubmitQuerrySerializer(query)
        return ResponseHandler.success(
            message="Query retrieved successfully.",
            data=serializer.data
        )

from rest_framework.permissions import IsAuthenticated

class ShareThoughtsView(APIView):
    permission_classes = [IsAuthenticated]  # only logged-in users can post/get

    def get(self, request):
        thoughts = ShareThoughts.objects.select_related('user').only('id', 'thoughts', 'created_at', 'user__username').order_by('-created_at')
        serializer = ShareThoughtsSerializer(thoughts, many=True)
        return ResponseHandler.success(
            message="Retrived successfully!",
            data= serializer.data
        )

    def post(self, request):
        serializer = ShareThoughtsSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return ResponseHandler.created(
                message="created successfully!",
                data= serializer.data
            )