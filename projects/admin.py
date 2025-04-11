from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Project)
admin.site.register(ProjectMedia)
admin.site.register(Sector)
admin.site.register(TeamMember)
admin.site.register(ProjectUpdate)