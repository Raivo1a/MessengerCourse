from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import User


class UserModeratorForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "is_active",
        ]


class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["avatar", "email", "phone", "country", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Ivaniv@example.com"})
        self.fields["phone"].widget.attrs.update({"class": "form-control", "placeholder": "222-22-22"})
        self.fields["country"].widget.attrs.update({"class": "form-control", "placeholder": "Россия"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Пароль"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Подтверждение пароля"})


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar", "phone", "country"]

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)

        self.fields["avatar"].widget.attrs.update(
            {"class": "form-control"},
        )
        self.fields["phone"].widget.attrs.update(
            {"class": "form-control"},
        )
        self.fields["country"].widget.attrs.update(
            {"class": "form-control"},
        )
