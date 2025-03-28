from django.contrib import admin
from .models import Waiting

class WaitingAdmin(admin.ModelAdmin):
    # list_display = ('id', 'user', 'booth', 'party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at')
    list_display = ('waiting_id', 'user', 'booth', 'person_num', 'waiting_status', 'created_at', 'confirmed_at', 'canceled_at')
    list_filter = ('waiting_status', 'booth', 'user')
    search_fields = ('user__username', 'booth__name')

admin.site.register(Waiting, WaitingAdmin)
