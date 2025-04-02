from django.contrib import admin

# Register your models here.
from .models import Investment, InvestmentMedia

admin.site.register(Investment)
admin.site.register(InvestmentMedia)
