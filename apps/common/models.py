import uuid

from django.db import models
from .managers import GetOrNoneManager


class BaseModel(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GetOrNoneManager()

    class Meta:
        abstract = True

    def dict(self):
        model_dict = self.__dict__
        model_dict.pop("_state")
        return model_dict


class File(BaseModel):
    resource_type = models.CharField(max_length=200)

    def __str__(self):
        return str(self.id)


class GuestUser(BaseModel):
    def __str__(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True
