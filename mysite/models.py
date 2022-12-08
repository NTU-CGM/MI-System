from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=20, null=False)
    email = models.EmailField()
    password = models.CharField(max_length=20, null=False)
    enable = models.BooleanField(default=False)

    def __str__(self):
        return self.name
