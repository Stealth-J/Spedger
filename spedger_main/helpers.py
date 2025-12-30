from django.core.mail import EmailMessage
from django.conf import settings


def send_mail(subject, body, email):
    email = EmailMessage(subject, body, to = [email])
    email.send()