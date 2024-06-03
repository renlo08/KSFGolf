from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from phonenumber_field import formfields

from accounts.models import UserProfile


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    family_name = forms.CharField(max_length=100)
    phone_number = formfields.PhoneNumberField(widget=forms.TextInput(attrs={'placeholder': _('Phone')}))
    hcp = forms.DecimalField(decimal_places=1, max_digits=3)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=True)
        UserProfile.objects.create(
            user=user,
            first_name=self.cleaned_data['first_name'],
            family_name=self.cleaned_data['family_name'],
            phone_number=self.cleaned_data['phone_number'],
            hcp=self.cleaned_data['hcp'],
        )
        return user


