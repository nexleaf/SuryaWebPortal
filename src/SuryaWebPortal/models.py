from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

class Deployment(models.Model):
    groups = models.ManyToManyField(Group, blank=True, null=True)
    name = models.CharField(max_length=250, verbose_name='Name')
    
    @property
    def groups_display(self):
        display = ''
        for g in self.groups.all():
            display += g.name + ', '
        display = display.rstrip(', ')
        return display

    def __unicode__(self):
        return self.name
