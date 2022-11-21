from django.db import models
from django.contrib.auth.models import AbstractUser

from plan.models import Plan


class User(AbstractUser):
    email = models.EmailField(unique=True)
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name='user', null=True,
    )
