from django.core.mail import EmailMessage
from django.conf import settings
from .models import Duel, FriendRequest, Profile
from django.db.models import F, Window, Count, Sum, Case, When, Q, ExpressionWrapper, FloatField, Max, Value
from django.db.models.functions import DenseRank, Round
from django.core.paginator import Paginator
from django.template.loader import render_to_string


def send_mail(subject, body, email):
    email = EmailMessage(subject, body, to = [email])
    email.send()

def send_mail_with_template(subject, template_name, context, email):
    body = render_to_string(template_name, context)
    email = EmailMessage(subject, body, to = [email])
    email.content_subtype = "html"
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
                Q(user__slips__settled = True) & Q(user__slips__slip_won = True), then = 1
            ))
        ),
        total_slips = Count('user__slips'),
        pure_percentage_temp = Case(
            When(total_slips = 0, then = Value(0.0)),
            default = ExpressionWrapper(
                ( F('winning_slips_temp') / F('total_slips') ) * 100,
                output_field = FloatField()
            ),
            output_field = FloatField(),
        )
    )

    ranked_qs = annotated_qs.annotate(
        rank = Window(
            expression = DenseRank(), 
            order_by = [F('pure_odds_temp').desc(), F('pure_percentage_temp').desc()],
        )
    )
    return ranked_qs


def rank_users_leaderboards(wkly_qs = None, wkly = True):
    if wkly:
        wkly_qs = wkly_qs.exclude(user__user_profile__private_acct = True)

        annotated_qs = wkly_qs.annotate(
            total_events = Count('slip__slip_events'),
            events_won = Count(
                Case(When(
                    Q(slip__slip_events__event_won = True), then = F('slip__slip_events')
                ))
            ),
            accuracy = ExpressionWrapper(
                ( F('events_won') * 100.0 ) / F('total_events'), output_field = FloatField()
            ),
            highest_selection = Max('slip__slip_events__event_odd'),
            games_won = Count(
                Case(When(
                    Q(slip__slip_events__event_won = True) & Q(slip__slip_events__event_settled = True), then = 1
                ))
            ),
            games_lost = Count(
                Case(When(
                    Q(slip__slip_events__event_won = False) & Q(slip__slip_events__event_settled = True), then = 1
                ))
            )
        )
        ranked_qs = annotated_qs.annotate(rank = Window(
            expression = DenseRank(),
            order_by = [ F('accuracy').desc(), F('slip__total_odds').desc(), F('highest_selection').desc() ]
        ))
    else:
        all_profiles = Profile.objects.exclude(private_acct = True)
        ranked_qs = rank_group_members(all_profiles)

    return ranked_qs