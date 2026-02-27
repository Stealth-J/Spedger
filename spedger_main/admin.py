from django.contrib import admin
from .models import GroupChatMsgs, Profile, Duel, DuellistInfo, DiaryEntry, FriendRequest, Slip, SlipEvent, DeleteReason, Feedback, GroupChat, WeeklyGame, WeeklyGameParticipant

# Register your models here.
admin.site.register(Profile)
admin.site.register(Duel)
admin.site.register(DuellistInfo)
admin.site.register(DiaryEntry)
admin.site.register(FriendRequest)
admin.site.register(Slip)
admin.site.register(SlipEvent)
admin.site.register(DeleteReason)
admin.site.register(Feedback)
admin.site.register(GroupChat)
admin.site.register(GroupChatMsgs)
admin.site.register(WeeklyGame)
admin.site.register(WeeklyGameParticipant)