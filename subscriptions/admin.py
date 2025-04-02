from django.contrib import admin

# Register your models here.
from .models import Subscription, SubscriptionMedia
admin.site.register(Subscription)
admin.site.register(SubscriptionMedia)