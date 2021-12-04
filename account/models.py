from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from field_history.tracker import FieldHistoryTracker
from twilio.rest import Client


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ngo_name = models.CharField(max_length=200, blank=False)
    location = models.CharField(max_length=300, blank=False)
    pan = models.CharField(max_length=20, blank=False, unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,12}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 12 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=15, blank=False,
                             unique=True)  # validators should be a list
    document = models.FileField(upload_to='documents/', blank=False)

    def __str__(self):
        return str(self.user)

    field_history = FieldHistoryTracker(['user'])

    @property
    def _field_history_user(self):
        return self.user

    # for twilio SMS notification
    def save(self, *args, **kwargs):
        if self.user.is_active:
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID')
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN')
            client = Client(account_sid, auth_token)
            message = client.messages \
            .create(
            body=f"{self.user.first_name}"
                 f"{self.user.last_name} Your account is verified and you can login now.. ",
            from_=getattr(settings, 'TWILIO_NUMBER'),
            to=f'+977{self.phone}'
        )
        print(message.sid)


# #using signals
@receiver(post_save, sender=UserProfile.user)
def create_ngo_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# for donor registration
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthdate = models.DateField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,12}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 12 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=15, blank=False,
                             unique=True)  # validators should be a list
    profile = models.ImageField(upload_to='donor/profile', blank=True)

    def __str__(self):
        return str(self.user)

    field_history = FieldHistoryTracker(['user'])

    @property
    def _field_history_user(self):
        return self.user


# using signals
@receiver(post_save, sender=CustomerProfile.user)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.create(user=instance)


class Causes(models.Model):
    PRIORITY = (
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Low', 'Low'),
    )
    STATUS = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
    )

    ngo = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date_requested = models.DateTimeField(auto_now_add=True)
    title = models.TextField(blank=False)
    description = models.TextField(blank=False)
    amount_required = models.PositiveBigIntegerField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY, default=PRIORITY)
    status = models.CharField(max_length=20, choices=STATUS, default=STATUS)
    cause_image = models.ImageField(upload_to='causes', blank=False)

    # for the django filed history

    def __str__(self):
        return str(self.title)

    field_history = FieldHistoryTracker(['status'])

    @property
    def _field_history_user(self):
        return self.ngo.userprofile.user


class Donation(models.Model):
    donor = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    cause = models.ForeignKey(Causes, on_delete=models.SET_NULL, null=True)
    amount = models.PositiveBigIntegerField(blank=True)
    date_donated = models.DateTimeField(auto_now_add=True)
    payment_completed = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return str(self.donor)

    field_history = FieldHistoryTracker(['donor'])

    @property
    def _field_history_user(self):
        return self.donor.user
