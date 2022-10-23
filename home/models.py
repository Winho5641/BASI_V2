from django.db import models

class Stock(models.Model):
    name = models.CharField(max_length=100)
    ## code = models.IntegerField()

    def to_json(self):
        return {
            "name" : self.name
        }
# Create your models here.
