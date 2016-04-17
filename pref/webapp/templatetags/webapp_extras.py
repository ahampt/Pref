from django import template
import math
import urllib

register = template.Library()

@register.filter
def multiply(value, arg):
	return int(value) * int(arg)
	
@register.filter
def divide_rounding_up(value, arg):
	return int(math.ceil(float(value) / float(arg)))
	
@register.filter
def get_range(value):
	return range(value)
	
@register.filter
def get_item(i, arr):
	try:
		return arr[i]
	except:
		return ''

@register.filter
def urlencode(value):
	return value[:5] + urllib.quote(value[5:])