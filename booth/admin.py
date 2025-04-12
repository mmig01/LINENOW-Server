from django.contrib import admin
from .models import *

class MenuAdmin(admin.ModelAdmin):
    list_display = ('menu_name', 'formatted_price')

    def formatted_price(self, obj):
        return f'{int(obj.menu_price):,}원'
    formatted_price.short_description = '가격'
    
admin.site.register(BoothMenu, MenuAdmin)
admin.site.register(Booth)
admin.site.register(BoothImage)