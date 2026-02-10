from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone

from messenger.models import Mailing, MailingAttempt, Message
from django.core.cache import cache
from messenger.models import Subscriber


def send_mailing(pk) -> str:
    mailing = get_object_or_404(Mailing, pk=pk)
    recipients = mailing.recipients.all()

    overall_response = "Рассылка завершена."

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.theme_mail,
                message=mailing.message.text_mail,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient.email],
            )
            server_response_text = "Письмо успешно отправлено."
            status = "Успешно"
        except Exception as e:
            server_response_text = str(e)
            status = "Не успешно"

        if server_response_text is None:
            server_response_text = "Успешно отправлено"

        m = MailingAttempt.objects.create(
            mailing=mailing,
            attempt_time=timezone.now(),
            status=status,
            server_response=server_response_text,
        )
        m.save()
    return overall_response


CACHE_TIMEOUT = 60 * 15

def get_subscribers_from_cache(user):
    '''Получает список подписчиков из кеша или из базы данных'''
    key = f'subscribers_user_{user.id}'
    subscribers = cache.get(key)
    if subscribers is not None:
        return subscribers
    if not user.groups.filter(name="Менеджер").exists():
        subscribers = Subscriber.objects.filter(owner=user)
    else:
        subscribers = Subscriber.objects.all()
    cache.set(key, subscribers, CACHE_TIMEOUT)
    return subscribers


def get_message_from_cache(message_id):
    '''Получает сообщение из кеша или из базы данных'''
    key = f'mail_message_{message_id}'
    message = cache.get(key)
    if message is not None:
        return message
    try:
        message = Message.objects.get(pk=message_id)
        if hasattr(message, "update_status"):
            message.update_status()
        cache.set(key, message, CACHE_TIMEOUT)
        return message
    except Message.DoesNotExist:
        return None
