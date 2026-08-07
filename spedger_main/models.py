import uuid
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.utils import timezone
from .model_helpers import *


DEFAULT_PROFILE_IMG = 'https://media.istockphoto.com/id/1495088043/vector/user-profile-icon-avatar-or-person-icon-profile-picture-portrait-symbol-default-portrait.jpg?s=612x612&w=0&k=20&c=dhV2p1JwmloBTOaGAtaA3AW1KSnjsdMt7-U_3EZElZ0='
DEFAULT_BACKGROUND_IMG = '/img/others/default_background.jpg'


# Create your models here.
class GroupChat(models.Model):
    group_name = models.CharField(max_length = 100)
    group_id = models.UUIDField(default = uuid.uuid4, unique = True, editable = False)
    group_leader = models.ForeignKey(User, null = True, blank = True, on_delete = models.SET_NULL)
    private_group = models.BooleanField(default = False)
    leader_talk_only = models.BooleanField(default = False)
    banned_users = models.ManyToManyField(User, related_name = "groups_banned_from", blank = True)
    created_on = models.DateTimeField(auto_now_add = True)

    @property
    def group_url(self):
        return f'group-{self.group_id}'


class FriendRequest(models.Model):
    sender = models.ForeignKey(User, related_name = "sent_friend_requests", on_delete = models.CASCADE)
    recipient = models.ForeignKey(User, related_name = "received_friend_requests", on_delete = models.CASCADE)
    status = models.CharField(max_length = 10, choices = [('open', 'Open'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default = 'open')
    time_sent = models.DateTimeField(auto_now_add = True)


class Slip(models.Model):
    user = models.ForeignKey(User, related_name = 'slips', on_delete = models.CASCADE)
    slip_code = models.CharField(max_length = 30)
    settled = models.BooleanField(default = False)
    slip_won = models.BooleanField(default = False)
    total_odds = models.DecimalField(max_digits = 30, null = True, blank = True, decimal_places = 2)
    weekly = models.BooleanField(default = False)
    entry_date = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.user.username} - {self.slip_code}'

    @property
    def total_events(self):   
        return self.slip_events.count()
    
    @property
    def games_left(self):
        settled_events_no = self.slip_events.filter( event_settled = True ).count()
        return self.total_events - settled_events_no

    @property
    def win_percentage(self):
        total_events = self.total_events
        if total_events == 0:
            return 0
        
        events_won = self.slip_events.filter( event_won = True ).count()
        return (events_won / total_events ) * 100


class SlipEvent(models.Model):
    slip = models.ForeignKey(Slip, related_name = 'slip_events', on_delete = models.CASCADE)
    event_id = models.CharField(max_length = 40, null = True, blank = True)
    participants = models.JSONField(default = list, blank = True)
    pick = models.CharField(max_length = 200)
    market = models.CharField(max_length = 200)
    sport = models.CharField(max_length = 50)
    competition = models.CharField(max_length = 200, null = True, blank = True)
    event_odd = models.DecimalField(max_digits = 30, null = True, blank = True, decimal_places = 2)
    event_won = models.BooleanField(default = False)
    event_settled = models.BooleanField(default = False)
    event_date = models.DateTimeField()
    event_cancelled = models.BooleanField(default = False)
    event_postponed = models.BooleanField(default = False)

    def __str__(self):
        return f'{self.slip.slip_code.upper()} - {self.participants}'
    
    @property
    def home_team(self):
        return self.participants[0] if self.participants else None
    
    @property
    def away_team(self):
        return self.participants[1] if len(self.participants) > 1 else None
    
    @property
    def sport_icon(self):
        return f'img/sports_icons/{self.sport.lower()}.svg'


class DiaryEntry(models.Model):
    user = models.ForeignKey(User, related_name = 'diary_entries', on_delete = models.CASCADE, null = True, blank = True)
    slip = models.ForeignKey(Slip, related_name = 'slip', on_delete = models.CASCADE)
    created_at = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return f'{self.slip.slip_code}'
    
    class Meta:
        verbose_name_plural = 'DiaryEntries'


class Duel(models.Model):
    class StatusChoices(models.TextChoices):
        OPEN = 'open',
        ACCEPTED = 'accepted',
        REJECTED = 'rejected'

    duel_status = models.CharField(max_length = 15, null = True, blank = True, choices = StatusChoices, default = 'open')
    settled = models.BooleanField(default = False)
    settled_date = models.DateTimeField(null = True, blank = True)
    minimum_odds = models.DecimalField(max_digits = 30, decimal_places = 2, null = True, blank = True)
    created_at = models.DateTimeField(default = timezone.now)
    winning_user = models.ForeignKey(User, related_name = "winning_duels", null = True, blank = True, on_delete = models.SET_NULL)

    @property
    def winner(self):
        winning_duellist = duel_winner(self.duellists.all())
        return winning_duellist
    
    @property
    def challenger(self):
        return self.duellists.filter(recipient = False).first()
    
    @property
    def recipient(self):
        return self.duellists.filter(recipient = True).first()
    
    @property
    def active(self):
        return self.duel_status == 'open' and self.settled == False

class DuellistInfo(models.Model):
    user = models.ForeignKey(User, related_name = 'user_duels', null = True, blank = True, on_delete = models.SET_NULL)
    slip = models.ForeignKey(Slip, related_name = 'duel', on_delete = models.CASCADE, null = True, blank = True)
    duel_obj = models.ForeignKey(Duel, related_name = 'duellists', on_delete = models.CASCADE)
    recipient = models.BooleanField(default = False)

    class Meta:
        verbose_name_plural = 'DuellistInfo'


class GroupChatMsgs(models.Model):
    user = models.ForeignKey(User, related_name = 'group_chats', on_delete = models.CASCADE)
    slip = models.ForeignKey(Slip, related_name = 'group_slip', on_delete = models.CASCADE)
    group_chat = models.ForeignKey(GroupChat, related_name = 'group_chat_msgs', null = True, blank = True, on_delete = models.CASCADE)
    additional_text = models.TextField(null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add = True)


class WeeklyGame(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    current_game = models.BooleanField(default = True)

class WeeklyGameParticipant(models.Model):
    user = models.ForeignKey(User, related_name = 'wkly_game_performances', on_delete = models.CASCADE)
    wkly_game = models.ForeignKey(WeeklyGame, related_name = 'game_participants', on_delete = models.CASCADE)
    slip = models.ForeignKey(Slip, related_name = 'wkly_game_slip', on_delete = models.CASCADE)
    ranking = models.PositiveIntegerField(null = True, blank = True)


class DeleteReason(models.Model):
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.reason
    

class Feedback(models.Model):
    user = models.ForeignKey(User, null = True, blank = True, on_delete = models.SET_NULL)
    message = models.TextField()
    status = models.CharField(max_length = 20, choices = [('unattended', 'Unattended'), ('replied', 'Replied')], default = 'unattended')
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.user.username} - {self.message}'


class Profile(models.Model):
    class ReasonChoices(models.TextChoices):
        FUN = 'fun',
        ADDICTION = 'addiction',
        RECORD = 'record'

    public_id = models.UUIDField(default = uuid.uuid4, unique = True, editable = False)
    full_name = models.CharField(max_length = 200)
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'user_profile')
    profile_img = models.CharField(max_length = 50, null = True, blank = True)
    background_img = models.CharField(max_length = 50, null = True, blank = True)
    fav_team = models.CharField(max_length = 200, null = True, blank=True)
    nationality = models.CharField(max_length = 200)
    reason = models.CharField(max_length = 20, choices = ReasonChoices)
    private_acct = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    friends = models.ManyToManyField(User, blank = True, related_name = "user_friends")
    reveal_slips = models.BooleanField(default = True)
    log_all_slips = models.BooleanField(default = False)
    groups = models.ManyToManyField(GroupChat, blank = True, related_name = "group_members")
    viewers = models.ManyToManyField(User, blank = True, related_name = "users_viewed")
    muted_users = models.ManyToManyField(User, blank = True, related_name = 'users_muted_by')

    def __str__(self):
        return self.user.username
    
    @property
    def avatar(self):
        avatar_src = f'img/avatars/{self.profile_img}.jpg'
        return avatar_src or DEFAULT_PROFILE_IMG
    
    @property
    def background(self):
        background_src = f'img/backgrounds/{self.background_img}.jpg'
        return background_src or DEFAULT_BACKGROUND_IMG
    
    @property
    def winning_slips(self):
        return self.user.slips.filter(settled = True, slip_won = True)
    
    @property
    def winning_slips_count(self):
        return self.winning_slips.count()
    
    @property
    def pure_percentage(self):
        if self.user.slips.count() < 1:
            return 'None'
        return round(self.winning_slips_count / self.user.slips.count(), 2)
    
    @property
    def highest_winning_odds(self):
        result = self.winning_slips.aggregate(result = models.Max('total_odds'))['result']
        if result == None:
            return 'None'
        return round(result, 1)

    @property
    def avg_odds(self):
        result = self.user.slips.aggregate(result = models.Avg('total_odds'))['result']
        if result == None:
            return 0
        return round(result, 1)

    @property
    def avg_winning_odds(self):
        result = self.winning_slips.aggregate(result = models.Avg('total_odds'))['result']
        if result == None:
            return 0
        return round(result, 1)
    
    @property
    def accuracy(self):
        user_slips = self.user.slips.all()
        total_events, events_won = return_slips_events(user_slips, accurate = True)
        if len(total_events) < 1:
            return 0
        result = (len(events_won) / len(total_events)) * 100 
        return round(len(events_won) / len(total_events), 1)
    
    @property
    def pure_odds(self):
        slips_won = Slip.objects.prefetch_related('slip').filter(settled = True, user = self.user, slip_won = True)
        result_obj = slips_won.aggregate(result = models.Sum('total_odds'))
        result = result_obj['result'] or 0
        return round(result, 1)
    
    @property
    def pure_odds_write_up(self):
        if self.user.slips.count() < 1:
            print(self.user.slips.count())
            return 'None'
        string = f'{self.winning_slips_count}/{self.user.slips.count()} ({self.pure_percentage}%)'
        return string

    @property
    def get_wkly_score(self):
        user_wkly_obj = WeeklyGameParticipant.objects.filter(user = self.user, wkly_game__current_game = True).first()
        return user_wkly_obj.slip.win_percentage or '-'


class CustomError(models.Model):
    error_class = models.CharField(max_length = 100)
    error_txt = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)