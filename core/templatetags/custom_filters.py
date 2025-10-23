from django import template

register = template.Library()

@register.filter
def abs(value):
    """Return the absolute value of the number."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value
    
@register.filter
def absolute(value):
    """Alternative name for abs filter"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    

@register.filter
def map_attribute(value, attr_name):
    """Get attribute from each object in a list."""
    try:
        return [getattr(item, attr_name) for item in value]
    except (AttributeError, TypeError):
        return []

@register.filter
def sum_values(value):
    """Sum all values in a list."""
    try:
        return sum(value)
    except (TypeError):
        return 0
    
@register.filter
def total_quantity(items):
    """Calculate total quantity from purchase order items"""
    return sum(item.quantity for item in items)

@register.filter
def max_quantity(items):
    """Get the maximum quantity from purchase order items"""
    if items:
        return max(item.quantity for item in items)
    return 0

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key, '')