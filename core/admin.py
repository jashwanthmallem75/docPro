from django.contrib import admin
from .models import Patient, Doctor, Specialization, Slot, Appointment, UserProfile

admin.site.register(Patient)
admin.site.register(Specialization)
admin.site.register(Doctor)
admin.site.register(Slot)
admin.site.register(Appointment)
admin.site.register(UserProfile)