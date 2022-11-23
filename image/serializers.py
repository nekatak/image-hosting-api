from rest_framework import serializers

from . import models


class LinkSerializer(serializers.ModelSerializer):
    uri = serializers.CharField()
    expiry = serializers.DateTimeField()

    class Meta:
        model = models.Link
        fields = ('uri', 'expiry')


class ImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Image
        fields = (
            'id', 'name', 'image_field', 'expiring_link_duration_seconds'
        )


class ImageSerializer(serializers.ModelSerializer):
    links = LinkSerializer(many=True)

    class Meta:
        model = models.Image
        fields = ('id', 'name', 'links')
