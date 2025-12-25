import uuid
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User

# Create your models here.
class Group(models.Model):
    group_name = models.CharField(max_length = 100)
    group_id = models.UUIDField(default = uuid.uuid4, unique = True, editable = False)
    group_leader = models.ForeignKey(User, null = True, blank = True, on_delete = models.SET_NULL)
    private_group = models.BooleanField(default = False)


class Profile(models.Model):
    class ReasonChoices(models.TextChoices):
        FUN = 'fun',
        ADDICTION = 'addiction',
        RECORD = 'record'

    public_id = models.UUIDField(default = uuid.uuid4, unique = True, editable = False)
    full_name = models.CharField(max_length = 200)
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'user_profile')
    profile_src = models.URLField(null = True, blank = True)
    fav_team = models.CharField(max_length = 200, null = True, blank=True)
    nationality = models.CharField(max_length = 200)
    reason = models.CharField(max_length = 20, choices = ReasonChoices)
    private_acct = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    friends = models.ManyToManyField(User, blank = True, related_name = "user_friends")
    reveal_slips = models.BooleanField(default = True)
    log_all_slips = models.BooleanField(default = False)
    groups = models.ManyToManyField(Group, blank = True, related_name = "group_members")

    def __str__(self):
        return self.user.username
    

class FriendRequest(models.Model):
    sender = models.ForeignKey(User, related_name = "sent_friend_requests", on_delete = models.CASCADE)
    recipient = models.ForeignKey(User, related_name = "received_friend_requests", on_delete = models.CASCADE)
    accepted = models.BooleanField(default = False)
    time_sent = models.DateTimeField(auto_now_add = True)


class Slip(models.Model):
    user = models.ForeignKey(User, related_name = 'slips', on_delete = models.CASCADE)
    slip_code = models.CharField(max_length = 30)
    total_odds = models.DecimalField(max_digits = 30, null = True, blank = True)
    settled = models.BooleanField(default = False)
    slip_won = models.BooleanField(default = False)
    total_odds = models.DecimalField(max_digits = 30, null = True, blank = True, decimal_places = 2)
    weekly = models.BooleanField(default = False)
    entry_date = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.user.username} - {self.slip_code}. {self.entry_date}'

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
    participants = models.JSONField()
    pick = models.CharField(max_length = 200)
    market = models.CharField(max_length = 200)
    sport = models.CharField(max_length = 50)
    competition = models.CharField(max_length = 200, null = True, blank = True)
    event_odd = models.DecimalField(max_digits = 30, null = True, blank = True, decimal_places = 2)
    event_won = models.BooleanField(default = False)
    event_settled = models.BooleanField(default = False)
    event_date = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.slip.slip_code.upper()} - {self.participants}'


class DiaryEntry(models.Model):
    slip = models.ForeignKey(Slip, related_name = 'slip', on_delete = models.CASCADE)

    def __str__(self):
        return f'{self.slip.slip_code} - {self.slip.entry_date}'
    
    class Meta:
        verbose_name_plural = 'DiaryEntries'


class Duel(models.Model):
    accepted = models.BooleanField(default = False)
    settled = models.BooleanField(default = False)
    settled_date = models.DateTimeField(null = True, blank = True)

    def winner(self):
        return

class DuellistInfo(models.Model):
    slip = models.ForeignKey(Slip, related_name = 'duel', on_delete = models.CASCADE)
    duel_obj = models.ForeignKey(Duel, related_name = 'duellists', on_delete = models.CASCADE)
    recipient = models.BooleanField(default = False)

    class Meta:
        verbose_name_plural = 'DuellistInfo'





# work weekly logic later on