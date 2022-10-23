from django.db import models

class Stock(models.Model):
    name = models.CharField(max_length=100)
    ## code = models.IntegerField()

# Create your models here.
