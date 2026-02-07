from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from messenger.apps import MessengerConfig
from messenger.views import (
    SubscriberCreateView,
    SubscriberListView,
    SubscriberDetailView,
    SubscriberDeleteView,
    SubscriberUpdateView,
    HomeView,
    EmailMessageCreateView,
    EmailMessageListView,
    EmailMessageUpdateView,
    EmailMessageDetailView,
    EmailMessageDeleteView,
    MailingCreateView,
    MailingListView,
    MailingDetailView,
    MailingUpdateView,
    MailingDeleteView,
    post_mail,
    ErrorView,
)

app_name = MessengerConfig.name

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("create_email/", EmailMessageCreateView.as_view(), name="create_email"),
    path("list_email/", EmailMessageListView.as_view(), name="list_email"),
    path("update_email/<int:pk>/", EmailMessageUpdateView.as_view(), name="update_email"),
    path("detail_email/<int:pk>/", EmailMessageDetailView.as_view(), name="detail_email"),
    path("delete_message/<int:pk>/", EmailMessageDeleteView.as_view(), name="delete_message"),
    path("create_mailing/", MailingCreateView.as_view(), name="create_mailing"),
    path("list_mailing/", MailingListView.as_view(), name="list_mailing"),
    path("detail_mailing/<int:pk>/", MailingDetailView.as_view(), name="detail_mailing"),
    path("update_mailing/<int:pk>/", MailingUpdateView.as_view(), name="update_mailing"),
    path("delete_mailing/<int:pk>/", MailingDeleteView.as_view(), name="delete_mailing"),
    path("mail_messages/<int:pk>/send", post_mail, name="send_mailing"),
    path("create_subscriber/", SubscriberCreateView.as_view(), name="create_subscriber"),
    path("list_subscriber/", SubscriberListView.as_view(), name="list_subscriber"),
    path("detail_subscriber/<int:pk>/", SubscriberDetailView.as_view(), name="detail_subscriber"),
    path("delete_subscriber/<int:pk>/", SubscriberDeleteView.as_view(), name="delete_subscriber"),
    path("update_subscriber/<int:pk>/", SubscriberUpdateView.as_view(), name="update_subscriber"),
    path("error/", ErrorView.as_view(), name="error"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
