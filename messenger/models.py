from django.db.models import Count, Q
from django.utils import timezone
from django.db import models

from users.models import User


class Subscriber(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=50, blank=False, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=50, blank=False, null=True, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=50, blank=False, null=True, verbose_name="Отчество")
    comment = models.CharField(
        max_length=200, verbose_name="Комментарий", blank=True, null=True, help_text="Введите комментарий"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Отправитель",
        help_text="Введите отправителя рассылки",
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        permissions = [
            ("can_view_recipient", "Can view recipient"),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"


class Message(models.Model):
    theme_mail = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тема письма")
    text_mail = models.TextField(blank=False, null=False, verbose_name="Текст письма")
    owner = models.ForeignKey(
        User,
        verbose_name="Создатель сообщения",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="custom_messages",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        unique_together = [
            ("theme_mail", "owner"),
        ]
        permissions = [
            ("can_view_message", "Can view message"),
        ]

    def __str__(self):
        return f"Сообщение. Тема: {self.theme_mail}"


class Mailing(models.Model):
    STATUS_CHOICES = [
        ("on_moderation", "На модерации"),
        ("created", "Создана"),
        ("started", "Готова к отправке"),
        ("completed", "Завершена"),
        ("failed", "Ошибка"),
    ]
    start_time = models.DateTimeField(blank=False, null=False, verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(blank=False, null=False, verbose_name="Дата и время окончания отправки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="on_moderation", verbose_name="Статус")
    recipients = models.ManyToManyField(Subscriber, verbose_name="Получатели", related_name="mailing")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="Сообщение", related_name="mailing")
    is_moderated = models.BooleanField(default=False)
    owner = models.ForeignKey(
        User,
        verbose_name="Менеджер клиента рассылки",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mailing",
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        unique_together = [
            ("message", "owner"),
        ]
        permissions = [
            ("can_view_mailing", "Can view mailing"),
            ("can_moderated_mailing", "Can moderated mailing"),
        ]

    def update_status(self):
        from messenger.views import post_mail_command

        now = timezone.now()
        for mailing in Mailing.objects.all():
            old_status = mailing.status
            if not mailing.is_moderated:
                if mailing.start_time and mailing.end_time:
                    if now < mailing.start_time:
                        mailing.status = "created"
                    elif mailing.start_time <= now <= mailing.end_time:
                        mailing.status = "started"
                    elif now > mailing.end_time:
                        mailing.status = "completed"
                    else:
                        mailing.status = "failed"
                else:
                    mailing.status = "failed"
                mailing.save()
                if old_status != "started" and mailing.status == "started":
                    try:
                        post_mail_command(mailing.pk)
                    except Exception:
                        pass

    @classmethod
    def get_user_stats(cls, user):
        return cls.objects.filter(owner=user).aggregate(
            count_on_moderation=Count("id", filter=Q(status="on_moderation")),
            count_created=Count("id", filter=Q(status="created")),
            count_completed=Count("id", filter=Q(status="completed")),
            count_started=Count("id", filter=Q(status="started")),
            count_failed=Count("id", filter=Q(status="failed")),
            total=Count("id"),
        )


class MailingAttempt(models.Model):
    recipients = models.ForeignKey(
        Subscriber,
        on_delete=models.CASCADE,
        related_name="mailing_recipients",
    )
    mailing = models.ForeignKey(
        Mailing,
        verbose_name="Рассылка",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="mailing",
    )
    STATUS_CHOICES = [("ok", "Успешно"), ("failed", "Ошибка")]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус отправки")
    is_sending = models.BooleanField(null=True, blank=True)
    details = models.TextField(verbose_name="Детали отправки", blank=True, null=True)
    attempt_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    server_response = models.TextField(verbose_name="Ответ сервера", blank=True, null=True)

    class Meta:
        verbose_name = "Попытка отправки рассылки"
        verbose_name_plural = "Попытки отправки рассылок"
        ordering = ["-attempt_time"]
