from django.contrib import admin
from .models import UserProfile, Causes, Donation
from .models import CustomerProfile
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(CustomerProfile)
admin.site.register(Donation)
admin.site.register(Causes)