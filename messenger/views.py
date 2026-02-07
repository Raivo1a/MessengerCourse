from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from messenger.forms import MailingForm, MailingModeratorForm, MailMessagesForm, SubscriberForm
from messenger.models import Message, Mailing, MailingAttempt, Subscriber
from messenger.services import send_mailing


class SubscriberCreateView(LoginRequiredMixin, CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = "messenger/create_subscriber.html"
    success_url = reverse_lazy("messenger:list_subscriber")

    def form_valid(self, form):
        subscriber = form.save()
        owner = self.request.user
        subscriber.owner = owner
        subscriber.save()
        form.save()
        return super().form_valid(form)


class SubscriberListView(LoginRequiredMixin, ListView):
    model = Subscriber
    template_name = "messenger/list_subscriber.html"
    context_object_name = "objects_list"

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and not user.groups.filter(name="Менеджер").exists():
            return queryset.filter(owner=user)
        if user.groups.filter(name="Менеджер").exists():
            return queryset
        return self.model.objects.none()


class SubscriberDetailView(LoginRequiredMixin, DetailView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = "messenger/detail_subscriber.html"


class SubscriberDeleteView(LoginRequiredMixin, DeleteView):
    model = Subscriber
    template_name = "messenger/delete_subscriber.html"
    success_url = reverse_lazy("messenger:list_subscriber")


class SubscriberUpdateView(LoginRequiredMixin, UpdateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = "messenger/update_subscriber.html"
    success_url = reverse_lazy("messenger:list_subscriber")


class HomeView(TemplateView):
    template_name = "messenger/home.html"

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and not user.groups.filter(name="Менеджер").exists():
            return queryset.filter(owner=user)
        if user.groups.filter(name="Менеджер").exists():
            return queryset
        return self.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_authenticated:
            return context
        if user.is_authenticated and not user.groups.filter(name="Менеджер").exists():
            context = super().get_context_data(**kwargs)
            context["messages"] = MailingAttempt.objects.filter(mailing__owner=user).aggregate(
                ok_cnt=Count("id", filter=Q(status="ok")),
                failed_cnt=Count("id", filter=Q(status="failed")),
            )
            context["subscriber"] = Subscriber.objects.filter(owner=user).aggregate(
                count=Count("id"),
            )
            context["mailing_stats"] = Mailing.get_user_stats(self.request.user)
        if user.is_authenticated and user.groups.filter(name="Менеджер").exists():
            return context
        else:
            return context


class EmailMessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MailMessagesForm
    template_name = "messenger/create_email.html"
    success_url = reverse_lazy("messenger:list_email")

    def form_valid(self, form):
        mail_message = form.save()
        owner = self.request.user
        mail_message.owner = owner
        cache.delete(f"user_{self.request.user.id}_messages")
        return super().form_valid(form)


class EmailMessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    form_class = MailMessagesForm
    template_name = "messenger/detail_email.html"

    def get_object(self, queryset=None):
        cache_key = f'mail_message_{self.kwargs["pk"]}'
        obj = cache.get(cache_key)
        if obj is None:
            obj = super().get_object(queryset)
            if hasattr(obj, "update_status"):
                obj.update_status()
            cache.set(cache_key, obj)
        return obj


class EmailMessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "messenger/list_email.html"
    context_object_name = "objects_list"

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and not user.groups.filter(name="Менеджер").exists():
            return queryset.filter(owner=user)
        if user.groups.filter(name="Менеджер").exists():
            return queryset
        return self.model.objects.none()


class EmailMessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MailMessagesForm
    template_name = "messenger/update_email.html"
    success_url = reverse_lazy("messenger:list_email")

    def form_valid(self, form):
        response = super().form_valid(form)
        cache.delete(f"mail_message_{self.object.pk}")
        cache.delete(f"user_{self.request.user.id}_messages")
        return response


class EmailMessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "messenger/delete_message.html"
    success_url = reverse_lazy("messenger:list_email")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        pk = self.object.pk
        user_id = request.user.id

        response = super().delete(request, *args, **kwargs)

        cache.delete(f"mail_message_{pk}")
        cache.delete(f"user_{user_id}_messages")

        return response


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "messenger/create_mailing.html"
    success_url = reverse_lazy("messenger:list_mailing")

    def form_valid(self, form):
        mail_mailing = form.save()
        mail_mailing.owner = self.request.user
        mail_mailing.save()
        cache.delete(f"user_{self.request.user.id}_messages")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "messenger/list_mailing.html"
    context_object_name = "objects_list"

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and not user.groups.filter(name="Менеджер").exists():
            return queryset.filter(owner=user)
        if user.groups.filter(name="Менеджер").exists():
            return queryset
        return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for mailing in context["object_list"]:
            mailing.update_status()
        return context


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    form_class = MailingForm
    template_name = "messenger/detail_mailing.html"

    def get_object(self, queryset=None):
        cache_key = f'mailing_{self.kwargs["pk"]}'
        obj = cache.get(cache_key)
        if obj is None:
            obj = super().get_object(queryset)
            obj.update_status()
            cache.set(cache_key, obj)
        return obj


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "messenger/update_mailing.html"
    success_url = reverse_lazy("messenger:detail_mailing")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_form_class(self):
        user = self.request.user
        if user.groups.filter(name="Менеджер").exists():
            return MailingModeratorForm
        return MailingForm

    def form_valid(self, form):
        mail_mailing = form.save()
        mail_mailing.is_moderated = False
        mail_mailing.update_status()
        mail_mailing.save()
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user

        if user.groups.filter(name="Менеджер").exists():
            return reverse_lazy("messenger:list_mailing")

        return reverse_lazy("messenger:detail_mailing", kwargs={"pk": self.object.pk})

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="Менеджер").exists():
            return Mailing.objects.all()

        return Mailing.objects.filter(owner=user)


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "messenger/delete_mailing.html"
    success_url = reverse_lazy("messenger:list_mailing")


def post_mail_command(pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    send_mailing(pk)
    mailing.status = "completed"
    mailing.end_time = timezone.now()
    mailing.save()


def post_mail(request, pk):
    try:
        mailing = get_object_or_404(Mailing, pk=pk)
        send_mailing(pk)
        mailing.status = "completed"
        mailing.end_time = timezone.now()
        mailing.save()
        return redirect("messenger:home")
    except Exception:
        return redirect("messenger:home")


class ErrorView(TemplateView):
    template_name = "messenger/error.html"
