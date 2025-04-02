from django.contrib import admin

# Register your models here.
from .models import Payment, PaymentMedia

admin.site.register(Payment)
admin.site.register(PaymentMedia)