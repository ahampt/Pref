from django.conf import settings

def exposed_settings(request):
	context_settings = dict()
	for x in settings.TEMPLATE_CONTEXT_SETTINGS:
		context_settings[x] = getattr(settings, x)
	return context_settings
