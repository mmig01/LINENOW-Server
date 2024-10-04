import django_filters
from waiting.models import Waiting

class WaitingFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(method='filter_by_status_group')

    class Meta:
        model = Waiting
        fields = ['waiting_status', 'created_at']

    def filter_by_status_group(self, queryset, name, value):
        """
        status 값에 따라 필터링
        """
        if value == 'waiting':
            return queryset.filter(waiting_status='waiting')
        elif value == 'calling':
            return queryset.filter(waiting_status__in=['ready_to_confirm', 'confirmed'])
        elif value == 'arrived':
            return queryset.filter(waiting_status='arrived')
        elif value == 'canceled':
            return queryset.filter(waiting_status__in=['canceled', 'time_over_canceled'])
        else:
            return queryset  # status_group이 없거나 잘못된 값이면 전체 반환