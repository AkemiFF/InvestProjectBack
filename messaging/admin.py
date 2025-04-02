from django.contrib import admin

# Register your models here.

from .models import Message, MessageMedia

admin.site.register(Message)
admin
