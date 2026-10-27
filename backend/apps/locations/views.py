from typing import ClassVar

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView

from apps.users.permissions import IsClient, IsTrader
from common.responses import success_response

from . import services
from .models import Location, SavedAddress
from .serializers import LocationSerializer, SavedAddressSerializer


class _OwnedList(ListCreateAPIView):
    """Own rows only, paginated. Creation goes through a service (limits, default)."""

    model = None
    create_service = None

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = type(self).create_service(request.user, **serializer.validated_data)
        return success_response(
            {self.item_key: self.get_serializer(obj).data},
            message=_("Saved."),
            status=201,
        )


class _OwnedDetail(APIView):
    model = None
    serializer_class = None

    def obj(self, request, pk):
        # Another user's row is a 404, never a 403, so ids do not leak.
        return get_object_or_404(self.model.objects, pk=pk, owner=request.user)

    def get(self, request, pk):
        return success_response(
            {self.item_key: self.serializer_class(self.obj(request, pk)).data}
        )


class LocationListView(_OwnedList):
    permission_classes: ClassVar[list] = [IsTrader]
    serializer_class = LocationSerializer
    model = Location
    item_key = "location"
    create_service = staticmethod(services.create_location)

    @extend_schema(tags=["locations"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=LocationSerializer, tags=["locations"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LocationDetailView(_OwnedDetail):
    permission_classes: ClassVar[list] = [IsTrader]
    model = Location
    serializer_class = LocationSerializer
    item_key = "location"

    @extend_schema(tags=["locations"])
    def get(self, request, pk):
        return super().get(request, pk)

    @extend_schema(request=LocationSerializer, tags=["locations"])
    def patch(self, request, pk):
        location = self.obj(request, pk)
        serializer = LocationSerializer(location, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        location = services.update_location(location, **serializer.validated_data)
        return success_response(
            {"location": LocationSerializer(location).data}, message=_("Saved.")
        )

    @extend_schema(request=None, tags=["locations"])
    def delete(self, request, pk):
        services.delete_location(self.obj(request, pk))
        return success_response({}, message=_("Deleted."))


class AddressListView(_OwnedList):
    permission_classes: ClassVar[list] = [IsClient]
    serializer_class = SavedAddressSerializer
    model = SavedAddress
    item_key = "address"
    create_service = staticmethod(services.create_address)

    @extend_schema(tags=["addresses"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=SavedAddressSerializer, tags=["addresses"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AddressDetailView(_OwnedDetail):
    permission_classes: ClassVar[list] = [IsClient]
    model = SavedAddress
    serializer_class = SavedAddressSerializer
    item_key = "address"

    @extend_schema(tags=["addresses"])
    def get(self, request, pk):
        return super().get(request, pk)

    @extend_schema(request=SavedAddressSerializer, tags=["addresses"])
    def patch(self, request, pk):
        address = self.obj(request, pk)
        serializer = SavedAddressSerializer(address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(address, key, value)
        address.save()
        return success_response(
            {"address": SavedAddressSerializer(address).data}, message=_("Saved.")
        )

    @extend_schema(request=None, tags=["addresses"])
    def delete(self, request, pk):
        self.obj(request, pk).soft_delete()
        return success_response({}, message=_("Deleted."))
