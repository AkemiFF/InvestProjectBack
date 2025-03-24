# projects/filters.py
import django_filters
from .models import Project

class ProjectFilter(django_filters.FilterSet):
    sector = django_filters.NumberFilter(field_name='sector__id')
    min_amount = django_filters.NumberFilter(field_name='amount_needed', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount_needed', lookup_expr='lte')
    funding_type = django_filters.CharFilter(field_name='funding_type')
    status = django_filters.CharFilter(field_name='status')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Project
        fields = ['sector', 'funding_type', 'status', 'min_amount', 'max_amount']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value) | queryset.filter(description__icontains=value)