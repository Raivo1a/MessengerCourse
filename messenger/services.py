from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone

from messenger.models import Mailing, MailingAttempt


def send_mailing(pk) -> None:
    mailing = get_object_or_404(Mailing, pk=pk)
    recipients = mailing.recipients.all()
    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.theme_mail,
                message=mailing.message.text_mail,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient.email],
            )
            print("Почта отправлена")
        except Exception as e:
            MailingAttempt.objects.create(
                mailing=mailing,
                attempt_time=timezone.now(),
                recipients=recipient,
                status="failed",
                details=str(e),
                is_sending=False,
            )
        else:
            MailingAttempt.objects.create(
                mailing=mailing, attempt_time=timezone.now(), recipients=recipient, status="ok", is_sending=True
            )
