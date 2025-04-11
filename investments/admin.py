from django.contrib import admin

# Register your models here.
from .models import Investment, Transaction

admin.site.register(Investment)
admin.site.register(Transaction)
