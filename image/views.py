import os
from datetime import datetime

from rest_framework import (
    views, mixins, viewsets, authentication, permissions, status, response
)
import django.http

from user.permissions import HasPlan
from . import serializers
from . import models


class FileRetrieveView(views.APIView):
    # no auth needed. Anyone with the link can get the image.
    permission_classes = []
    authentication_classes = []

    def get(self, request, pk=None):
        def _read_file(path):
            """
            Streaming response file reader
            """
            if not os.path.isfile(path):
                yield b""

            with open(path, "rb") as bytefile:
                for line in bytefile:
                    yield line

        link = models.Link.objects.get(id=pk)
        if not link:
            return response.Response(
                data={"detail": "Link not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
                link.expiry and
                link.expiry.timestamp() < datetime.now().timestamp()
        ):
            return response.Response(
                data={"detail": "Link has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resp = django.http.StreamingHttpResponse(
            _read_file(link.image.image_field.path)
        )
        resp["Content-Disposition"] = (
            f'attachment; filename={str(pk)}.jpg'
        )
        return resp


class PhotoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, HasPlan]
    queryset = models.Image.objects.filter(parent_image=None)

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.ImageCreateSerializer

        return serializers.ImageSerializer

    def create(self, request):
        """
        Upload an image.

        Storing of the images will happen based on the Plan the user has.
        """
        serializer = serializers.ImageCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            serializer.instance.store_thumbnails_and_links()

            headers = self.get_success_headers(serializer.data)
            return response.Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        return response.Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)
