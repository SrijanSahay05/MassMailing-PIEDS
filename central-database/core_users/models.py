from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    """
    Extending the default AbstractUser for future scaling.
    """

    pass

    def __str__(self):
        return self.username
