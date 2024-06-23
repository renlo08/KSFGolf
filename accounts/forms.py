from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from phonenumber_field import formfields

from accounts.models import UserProfile


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    family_name = forms.CharField(max_length=100, required=True)
    phone_number = formfields.PhoneNumberField(required=True, widget=forms.TextInput(attrs={'placeholder': _('Phone')}))
    hcp = forms.DecimalField(decimal_places=1, max_digits=3)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'email')

    def save(self, commit=True):
        user = super().save(commit=True)
        UserProfile.objects.create(
            user=user,
            first_name=self.cleaned_data['first_name'],
            family_name=self.cleaned_data['family_name'],
            phone_number=self.cleaned_data['phone_number'],
        )
        return user


