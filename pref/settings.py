# Django settings for pref project.
import os
relpath = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ACCESS_PASSWORD = 'movies'

API_KEYS = {
	'ROTTEN_TOMATOES': '7vsq9s5wkrqe6kmy9bce4m42',
	'NETFLIX': 'fr9pc2q6ypjb2969vjrfprc5',
	'NETFLIX_SECRET': 'bJdEVY2AqD'
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'pref_db',                      # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': 'root',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

PREFIX_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
# Development
STATIC_URL = '/' + PREFIX_URL + 'static/'
# Production
#STATIC_URL = 'http://doqh27zvd7u5w.cloudfront.net/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
	relpath('static/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@=mx=zef-$c!^wy2ad7(av2m7c-^kd%ox^-stt)23-td&z6s!6'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.request',
	'django.contrib.auth.context_processors.auth',
	'django.core.context_processors.debug',
	'django.core.context_processors.i18n',
	'django.core.context_processors.media',
	'django.core.context_processors.static',
	"django.core.context_processors.tz",
	'django.contrib.messages.context_processors.messages'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'pref.webapp.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
	relpath('webapp/templates/'),
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
	'pref.webapp',
)

LOGGING_DIR = '/var/log/pref/'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
	'formatters': {
		'verbose': {
			'format': '%(levelname)s %(asctime)s: %(message)s'
		}
	},
    'handlers': {
		'site': {
			'level': 'DEBUG',
			'class': 'logging.FileHandler',
			'formatter': 'verbose',
			'filename': LOGGING_DIR + 'site.log',
		},
        'profile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
			'formatter': 'verbose',
			'filename': LOGGING_DIR + 'profile.log'
        },
		'movie': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
			'formatter': 'verbose',
			'filename': LOGGING_DIR + 'movie.log'
        },
		'property': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
			'formatter': 'verbose',
			'filename': LOGGING_DIR + 'property.log'
        },
		'associate': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
			'formatter': 'verbose',
			'filename': LOGGING_DIR + 'associate.log'
        }
    },
    'loggers': {
		'log.site': {
			'handlers': ['site'],
			'level': 'DEBUG',
			'propagate': False,
		},
        'log.profile': {
            'handlers': ['profile'],
            'level': 'DEBUG',
            'propagate': False,
        },
		'log.movie': {
            'handlers': ['movie'],
            'level': 'DEBUG',
            'propagate': False,
        },
		'log.property': {
            'handlers': ['property'],
            'level': 'DEBUG',
            'propagate': False,
        },
		'log.associate': {
			'handlers': ['associate'],
			'level': 'DEBUG',
			'propogate': False,
		}
    }
}

