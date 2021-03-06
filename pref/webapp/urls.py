from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	('^' + settings.PREFIX_URL + r'$', 'webapp.views.site.access'),
	('^' + settings.PREFIX_URL + r'home/$', 'webapp.views.site.home'),
	('^' + settings.PREFIX_URL + r'register/$', 'webapp.views.profile.register'),
	('^' + settings.PREFIX_URL + r'profiles/$', 'webapp.views.profile.view_list'),
	('^' + settings.PREFIX_URL + r'profiles/(?P<username>\w{0,30})/$', 'webapp.views.profile.view'),
	('^' + settings.PREFIX_URL + r'login/$', 'webapp.views.profile.login'),
	('^' + settings.PREFIX_URL + r'logout/$', 'webapp.views.profile.logout'),
	('^' + settings.PREFIX_URL + r'movies/$', 'webapp.views.movie.view_list'),
	('^' + settings.PREFIX_URL + r'movies/(?P<urltitle>[a-zA-Z0-9_~]{0,100})/$', 'webapp.views.movie.view'),
	('^' + settings.PREFIX_URL + r'people/$', 'webapp.views.property.people'),
	('^' + settings.PREFIX_URL + r'people/(?P<urlname>[a-zA-Z0-9_~]{0,100})/$', 'webapp.views.property.person'),
	('^' + settings.PREFIX_URL + r'genres/$', 'webapp.views.property.genres'),
	('^' + settings.PREFIX_URL + r'genres/(?P<description>[a-zA-Z0-9_~-]{0,50})/$', 'webapp.views.property.genre'),
	('^' + settings.PREFIX_URL + r'search/$', 'webapp.views.movie.search'),
	('^' + settings.PREFIX_URL + r'random/$', 'webapp.views.movie.random'),
	('^' + settings.PREFIX_URL + r'discovery/$', 'webapp.views.site.discovery'),
	('^' + settings.PREFIX_URL + r'about/$', 'webapp.views.site.about'),
	('^' + settings.PREFIX_URL + r'disclaimers/$', 'webapp.views.site.disclaimers'),
	('^' + settings.PREFIX_URL + r'privacy_policy/$', 'webapp.views.site.privacy'),
	('^' + settings.PREFIX_URL + r'channel/$', 'webapp.views.site.channel'),
)
