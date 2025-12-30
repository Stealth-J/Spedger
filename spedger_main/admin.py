from django.contrib import admin
from .models import Group, Profile, Duel, DuellistInfo, DiaryEntry, FriendRequest, Slip, SlipEvent, DeleteReason, Feedback

# Register your models here.
admin.site.register(Group)
admin.site.register(Profile)
admin.site.register(Duel)
admin.site.register(DuellistInfo)
admin.site.register(DiaryEntry)
admin.site.register(FriendRequest)
admin.site.register(Slip)
admin.site.register(SlipEvent)
admin.site.register(DeleteReason)
admin.site.register(Feedback)