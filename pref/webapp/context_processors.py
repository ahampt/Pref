from django.conf import settings

def environment(context):
	return {'ENVIRONMENT' : settings.ENVIRONMENT}
