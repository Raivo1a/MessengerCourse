from django import forms
from django.core.validators import EmailValidator
from django.utils import timezone

from messenger.models import Message, Mailing
from messenger.models import Subscriber


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email", "first_name", "last_name", "middle_name", "comment"]
        email = forms.EmailField(validators=[EmailValidator()])

    def __init__(self, *args, **kwargs):
        super(SubscriberForm, self).__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "E-mail получателя"})
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "Имя"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Фамилия"})
        self.fields["middle_name"].widget.attrs.update({"class": "form-control", "placeholder": "Отчество"})
        self.fields["comment"].widget.attrs.update({"class": "form-control", "placeholder": "Комментарий"})


class MailMessagesForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = ["theme_mail", "text_mail"]

    def __init__(self, *args, **kwargs):
        super(MailMessagesForm, self).__init__(*args, **kwargs)

        self.fields["theme_mail"].widget.attrs.update(
            {"class": "form-control"},
        )
        self.fields["text_mail"].widget.attrs.update(
            {"class": "form-control"},
        )

    def clean_theme_mail(self):
        cleaned_data = super().clean()
        theme_mail = cleaned_data.get("theme_mail")
        theme_mail_error = [
            "спам",
        ]
        if theme_mail in theme_mail_error:
            self.add_error("theme_mail", f"Тема не может содержать слово {theme_mail}")
        if len(theme_mail) > 50:
            self.add_error("theme_mail", "Количество символов в теме не должно превышать 50")
        return theme_mail


class MailingModeratorForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = [
            "is_moderated",
        ]
        widgets = {"is_moderated": forms.CheckboxInput(attrs={"class": "form-check-input"})}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["is_moderated"].label = "Проверено модератором"
            self.fields["is_moderated"].help_text = "Отметьте, если рассылка прошла модерацию"


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "recipients", "message"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "recipients": forms.CheckboxSelectMultiple(),
            "message": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["start_time"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_time"].input_formats = ["%Y-%m-%dT%H:%M"]

        if self.user and self.user.is_authenticated:
            is_moderator = self.user.groups.filter(name="Менеджер").exists()

            if is_moderator:
                self.fields["recipients"].queryset = Subscriber.objects.all()
                self.fields["message"].queryset = Message.objects.all()
            else:
                self.fields["recipients"].queryset = Subscriber.objects.filter(owner=self.user)
                self.fields["message"].queryset = Message.objects.filter(owner=self.user)
        else:
            self.fields["recipients"].queryset = Subscriber.objects.none()
            self.fields["message"].queryset = Message.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time < timezone.now():
            self.add_error("start_time", "Дата начала не может быть в прошлом")

        if start_time > end_time:
            self.add_error("start_time", "Дата начала не может быть позже даты окончания")
