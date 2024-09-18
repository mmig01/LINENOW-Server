from django.contrib import admin
from .models import *

class BoothMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'formatted_price')

    def formatted_price(self, obj):
        return f'{int(obj.price):,}원'
    formatted_price.short_description = '가격'
    
admin.site.register(BoothMenu, BoothMenuAdmin)

admin.site.register(Event)
admin.site.register(Booth)
admin.site.register(BoothImage)