# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def filter_status(queryset, status):
    """Filter a queryset by status"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(status=status)
    return []

@register.filter
def get_item(dictionary, key):
    """Get a value from a dictionary by key"""
    return dictionary.get(key, '')