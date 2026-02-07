from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from messenger.models import Mailing
from messenger.views import post_mail_command


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Email пользователя")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        user = User.objects.get(email=email)
        mailing_list = Mailing.objects.filter(owner=user, status="started")
        print(f"Получено {len(mailing_list)} рассылок")
        for mailing in mailing_list:
            try:
                print(f"Отравляю {mailing}")
                post_mail_command(mailing.pk)
            except Exception as e:
                print(f"Ошибка {e}")
