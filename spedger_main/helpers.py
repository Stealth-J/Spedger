from django.core.mail import EmailMessage
from django.conf import settings
from .models import Duel, FriendRequest, Profile, Slip, SlipEvent
from django.db.models import F, Window, Count, Sum, Case, When, Q, ExpressionWrapper, FloatField
from django.db.models.functions import DenseRank
from django.core.paginator import Paginator


def send_mail(subject, body, email):
    email = EmailMessage(subject, body, to = [email])
    email.send()


def total_notifications(request):
    total_duels = Duel.objects.prefetch_related('duellists').filter(duellists__user = request.user, duel_status = 'open', duellists__recipient = 'True').count()
    total_requests = FriendRequest.objects.prefetch_related('recipient').filter(recipient = request.user, status = 'open').count()

    return total_requests, total_duels


def paginate(request, qs, page_num = 1):
    paginator = Paginator(qs, settings.PAGE_SIZE)
    current_qs = paginator.get_page(page_num)
    return current_qs


def rank_group_members(qs):
    annotated_qs = qs.annotate(
        pure_odds_temp = Sum(
            Case(When(
                Q(user__slips__settled = True) & Q(user__slips__slip_won = True), then = F('user__slips__total_odds')
            ))
        ),
        winning_slips_temp = Count(
            Case(When(
                Q(user__slips__settled = True) & Q(user__slips__slip_won = True)
            ))
        ),
        total_slips = Count('user__slips'),
        pure_percentage_temp = ExpressionWrapper(
            ( F('winning_slips_temp') / F('total_slips') ) * 100,
            output_field = FloatField()
        )
    )

    ranked_qs = annotated_qs.annotate(
        rank = Window(
            expression = DenseRank(), 
            order_by = [F('pure_odds_temp').asc(), F('pure_percentage_temp').asc()],
        )
    )
    return ranked_qs

