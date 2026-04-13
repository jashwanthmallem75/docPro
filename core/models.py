from django.db import models
from django.contrib.auth.models import User

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10)
    age = models.IntegerField(default=0)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ])
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
class Specialization(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='🏥')
    
    def __str__(self):
        return self.name

class Doctor(models.Model):
    name = models.CharField(max_length=100)  # ✅ ADD THIS

    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    experience = models.IntegerField(default=0)
    fee = models.IntegerField(default=500)
    qualification = models.CharField(max_length=200)
    about = models.TextField(default='')
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Slot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.doctor} | {self.date} {self.time}"

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ], default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')
    
    # ✅ ADD THESE TWO
    payment_id = models.CharField(max_length=100, blank=True, default='')
    payment_status = models.CharField(max_length=20, default='Pending')
    
    def __str__(self):
        return f"{self.patient} → {self.slot}"
    
# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = [('patient', 'Patient'), ('doctor', 'Doctor')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10)
    age = models.IntegerField(default=0)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')
    ])
    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Specialization(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='🏥')
    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    experience = models.IntegerField(default=0)
    fee = models.IntegerField(default=500)
    qualification = models.CharField(max_length=200)
    about = models.TextField(default='')
    available = models.BooleanField(default=True)
    def __str__(self):
        return self.name

class Slot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    # 🔒 Slot locking fields
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='locked_slots')
    locked_until = models.DateTimeField(null=True, blank=True)

    def is_locked(self):
        if self.locked_by and self.locked_until:
            return timezone.now() < self.locked_until
        return False

    def __str__(self):
        return f"{self.doctor} | {self.date} {self.time}"

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ], default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')
    payment_id = models.CharField(max_length=100, blank=True, default='')
    payment_status = models.CharField(max_length=20, default='Pending')
    reminder_sent = models.BooleanField(default=False)  # for email reminders

    def __str__(self):
        return f"{self.patient} → {self.slot}"
    
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)