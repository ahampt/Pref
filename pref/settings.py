# Django settings for pref project.
import os
relpath = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ACCESS_PASSWORD = 'movies'

MAX_LOGIN_ATTEMPTS = 25

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'pref_db',
		'USER': 'root',
		'PASSWORD': 'root',
		'HOST': '',
		'PORT': '',
	}
}

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

PREFIX_URL = ''

STATIC_ROOT = ''

STATIC_URL = '/' + PREFIX_URL + 'static/'

# Additional locations of static files
STATICFILES_DIRS = (
	relpath('static/'),
)

STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = '@=mx=zef-$c!^wy2ad7(av2m7c-^kd%ox^-stt)23-td&z6s!6'

TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
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
try:
	from local_settings import *
except ImportError:
	print 'Failed to load local settings'

