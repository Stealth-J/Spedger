from django.core.mail import EmailMessage
from django.conf import settings


def send_mail(email, body, subject):
    email = EmailMessage(subject, body, to = [email])