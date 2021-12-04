from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile, CustomerProfile, Causes, Donation


#for the seller registeration
class NgoCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30,)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = {'first_name', 'last_name', 'username', 'email', 'password1', 'password2'}

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.password1 = self.cleaned_data['password1']
        user.password2 = self.cleaned_data['password2']

        if user.password1 and user.password2 and user.password1 != user.password2:
            raise forms.ValidationError(
                self.error_messages['Password does not matched'],
                code='password_mismatch',
            )
            return password
        else:
            if commit:
                user.is_staff = True
                user.is_active = False
                user.save()
            return user

# for the updateing of profile this form is created
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
        ]

class BusinessForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('ngo_name', 'location', 'pan', 'phone', 'document')



# for the customer registeration
class DonorCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = {'first_name', 'last_name', 'username', 'email', 'password1', 'password2'}

    def save(self, commit=True):
        user = super().save(commit=False)

        user.password1 = self.cleaned_data['password1']
        user.password2 = self.cleaned_data['password2']

        if user.password1 and user.password2 and user.password1 != user.password2:
            raise forms.ValidationError(
                self.error_messages['Password does not matched'],
                code='password_mismatch',
            )
            return password
        else:
            if commit:
                user.save()
            return user


class DonorForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ('birthdate', 'phone', 'profile')


#for cause and donation
class CauseForm(forms.ModelForm):
    class Meta:
        model = Causes
        fields = {'ngo',
                  'title',
                  'description',
                  'amount_required',
                  'status',
                  'priority',
                  'cause_image'
                  }


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = {'donor',
                  'cause',
                  'amount'
                  }