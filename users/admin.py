from django.contrib import admin

from .models import *

admin.site.register(User)
admin.site.register(InvestorProfile)
admin.site.register(ProjectOwnerProfile)
admin.site.register(Favorite)
admin.site.register(RegistrationRequest)


