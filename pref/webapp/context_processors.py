from django.conf import settings

def environment(context):
	return {'ENVIRONMENT' : settings.ENVIRONMENT}

def version(context):
	return {'VERSION' : settings.VERSION}
