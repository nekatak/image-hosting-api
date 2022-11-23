import uuid
from datetime import datetime, timedelta

import django.core.files
from django.core.exceptions import ValidationError
from django.db import models
from PIL import Image as PILImage

from user.models import User
from server import settings


def image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<user_id>/<filename>
    return '{0}/{1}'.format(instance.user.id, filename)


def validate_expiring_link_duration_seconds(value):
    if value and (value <= 300 or value >= 30000):
        raise ValidationError('Invalid expiring_link_duration_seconds value')


class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    image_field = models.ImageField(upload_to='uploads')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    width = models.PositiveIntegerField(null=True)
    height = models.PositiveIntegerField(null=True)
    # separate the thumbnails
    parent_image = models.ForeignKey(
        'Image',
        on_delete=models.CASCADE,
        null=True
    )
    expiring_link_duration_seconds = models.PositiveIntegerField(
        validators=[validate_expiring_link_duration_seconds],
        null=True
    )

    @property
    def links(self):
        """
        return all related links with each Image object.
        """
        thumbs = Image.objects.filter(parent_image=self)

        return Link.objects.filter(image__in=list(thumbs) + [self])

    def resize(self, width, height):
        """
        Resize images with PIL for thumbs.
        """
        try:
            image = PILImage.open(self.image_field.path)
            resized = image.resize((width, height))

            from pathlib import Path
            path = Path(settings.MEDIA_ROOT) / str(uuid.uuid4())
            with open(path, 'w') as imagefile:
                resized.save(imagefile, 'JPEG')

            return path

        except IOError:
            pass

    def store_thumbnails_and_links(self):
        """
        Create resized images (thumbnails) and links for all the items included
        in the user's plan.
        """
        for item in self.user.plan.includes.all():
            # thumbnails should have both dimentions set
            if item.width and item.height:
                # store new image
                path = self.resize(item.width, item.height)
                with open(path, 'rb') as imagefile:
                    obj = Image(
                        user=self.user,
                        width=item.width,
                        height=item.height,
                        parent_image=self,
                        name=self.name,
                        image_field=django.core.files.File(
                            imagefile, name=path.name
                        ),
                    )
                    obj.save()
                path.unlink()
            else:
                # this is to generate link for initial image if in the plan
                obj = self

            if item.link:
                unique_id = uuid.uuid4()
                ln = Link(
                    id=unique_id,
                    uri=f'{settings.BASE_URL}/api/images/links/{unique_id}',
                    image=obj,
                )
                ln.save()
            if item.expiry_link:
                unique_id = uuid.uuid4()
                expiry_secs = (
                    item.expiry_link_seconds or
                    self.expiring_link_duration_seconds
                )
                ln = Link(
                    id=unique_id,
                    uri=f'{settings.BASE_URL}/api/images/links/{unique_id}',
                    image=obj,
                    expiry=datetime.now() + timedelta(seconds=expiry_secs),
                )
                ln.save()


class Link(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uri = models.TextField(unique=True)
    expiry = models.DateTimeField(null=True)
    image = models.ForeignKey(
        Image, on_delete=models.CASCADE
    )
