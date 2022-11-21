from django.db import models

from django.core.validators import MinValueValidator, MaxValueValidator


class ImageSpecifications(models.Model):
    """
    Describe images specs to be stored.

    Null width/height means original photo.
    """
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    link = models.BooleanField()
    expiry_link = models.BooleanField()
    expiry_link_seconds = models.PositiveIntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(30000)],
        default=300
    )


class Plan(models.Model):
    name = models.TextField(
        unique=True,
        error_messages={'unique': 'Plan with that name already exists.'}
    )
    includes = models.ManyToManyField(
        ImageSpecifications, through="PlanToImageSpecifications"
    )


class PlanToImageSpecifications(models.Model):
    image_specifications = models.ForeignKey(
        ImageSpecifications,
        on_delete=models.CASCADE
    )
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["image_specifications", "plan"]
