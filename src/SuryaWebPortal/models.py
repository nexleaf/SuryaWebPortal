from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

class MyUser(User):
    class Meta:
        proxy = True

    def deployment_list(self):
        deployment_list = []
        for g in self.groups.all():
            for d in g.deployment_set.all():
                deployment_list.append(d.name)
        return deployment_list

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
