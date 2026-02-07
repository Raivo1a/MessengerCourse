import secrets

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from config.settings import EMAIL_HOST_USER
from users.forms import UserCreationForm, UserModeratorForm, UserUpdateForm
from users.models import User


class UserCreateView(CreateView):
    model = User
    form_class = UserCreationForm
    success_url = reverse_lazy("users:login")
    template_name = "users/new_user_create.html"

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email_confirm/{token}/"
        send_mail(
            subject="Подтверждение почты",
            message=f"Перейдите по ссылке для завершения регистрации {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.token = None
    user.save()
    return redirect(reverse("users:login"))


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserCreationForm
    template_name = "users/user_update.html"
    success_url = reverse_lazy("users:user_list")

    def get_form_class(self):
        user = self.request.user
        target_user = self.object
        if user == target_user:
            return UserUpdateForm
        if user.groups.filter(name="Менеджер").exists():
            return UserModeratorForm
        raise PermissionDenied("У вас недостаточно прав")


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "objects_list"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.groups.filter(name="Менеджер").exists():
            return queryset.exclude(pk=user.pk)
        raise PermissionDenied("У вас недостаточно прав")
        return queryset.none()


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
