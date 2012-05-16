from django.contrib import admin
from models import *

class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'groups_display')
admin.site.register(Deployment, DeploymentAdmin)
