from django.contrib import admin
from .models import SearchHistory

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('city', 'period', 'user', 'timestamp')
    list_filter = ('city', 'user')
    search_fields = ('city',)