import logging, urllib
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from webapp.models import Profiles, Movies, ConsumeableTypes, People, Genres, Properties, PropertyTypes, Associations

profile_logger = logging.getLogger('log.profile')
movie_logger = logging.getLogger('log.movie')
property_logger = logging.getLogger('log.property')
associate_logger = logging.getLogger('log.associate')

# Create and save association given movie and property
def create_movie_property(movie, property_id, property_name, property_type, logged_in_profile_username):
	try:
		property = Properties(ConsumeableId = movie, ConsumeableTypeId = ConsumeableTypes.objects.get(Description='MOVIE'), PropertyId = property_id, PropertyTypeId = PropertyTypes.objects.get(Description=property_type))
		property.save()
		associate_logger.info(movie.UrlTitle + ' Associated ' + property_name + ' Success by ' + logged_in_profile_username)
	except:
		pass

# Create and save properties given movie and properties
def create_properties(movie, directors, writers, actors, genres, logged_in_profile_username):
	for director in directors:
		# Associate old property
		try:
			person = People.objects.get(Name=director)
			create_movie_property(movie, person.id, person.UrlName, 'DIRECTOR', logged_in_profile_username)
		# Create and associate new property
		except Exception:
			person = People(Name=director)
			person.full_clean()
			person.save()
			property_logger.info(person.UrlName + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, person.id, person.UrlName, 'DIRECTOR', logged_in_profile_username)
	for writer in writers:
		# Associate old property
		try:
			person = People.objects.get(Name=writer)
			create_movie_property(movie, person.id, person.UrlName, 'WRITER', logged_in_profile_username)
		# Create and associate new property
		except Exception:
			person = People(Name=writer)
			person.full_clean()
			person.save()
			property_logger.info(person.UrlName + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, person.id, person.UrlName, 'WRITER', logged_in_profile_username)
	for actor in actors:
		# Associate old property
		try:
			person = People.objects.get(Name=actor)
			create_movie_property(movie, person.id, person.UrlName, 'ACTOR', logged_in_profile_username)
		# Create and associate new property
		except Exception:
			person = People(Name=actor)
			person.full_clean()
			person.save()
			property_logger.info(person.UrlName + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, person.id, person.UrlName, 'ACTOR', logged_in_profile_username)
	for genre in genres:
		# Associate old property
		try:
			g = Genres.objects.get(Description=genre)
			create_movie_property(movie, g.id, g.Description, 'GENRE', logged_in_profile_username)
		# Create and associate new property
		except Exception:
			g = Genres(Description=genre)
			g.save()
			property_logger.info(g.Description + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, g.id, g.Description, 'GENRE', logged_in_profile_username)

# Return imdb url given movie
def imdb_link_for_movie(movie):
	if movie.ImdbId:
		return 'http://www.imdb.com/title/' + movie.ImdbId
	return None

# Return rotten tomatoes url given movie
def rottentomatoes_link_for_movie(movie):
	if movie.RottenTomatoesId:
		return 'http://www.rottentomatoes.com/m/' + movie.RottenTomatoesId
	return None

# Return netflix url given movie
def netflix_link_for_movie(movie):
	if movie.NetflixId:
		return 'http://movies.netflix.com/Movie/' + movie.NetflixId
	return None

# Return wikipedia url given movie
def wikipedia_link_for_movie(movie):
	if movie.WikipediaId:
		return 'http://en.wikipedia.org/wiki/' + movie.WikipediaId
	return None

# Return dictionary of links for movie
def generate_links_dict(movie):
	links = { }
	links['imdb'] = imdb_link_for_movie(movie)
	links['rt'] = rottentomatoes_link_for_movie(movie)
	links['netflix'] = netflix_link_for_movie(movie)
	links['wikipedia'] = wikipedia_link_for_movie(movie)
	return links

# Set alert message data (title, content, level)
def set_msg(request, msg_head, msg, msg_lvl):
	request.session['msg_head'] = msg_head
	request.session['msg'] = msg
	request.session['msg_lvl'] = msg_lvl

# Clear message data
def clear_msg(request):
	try:
		del request.session['msg_head']
	except KeyError:
		pass
	try:
		del request.session['msg']
	except KeyError:
		pass
	try:
		del request.session['msg_lvl']
	except KeyError:
		pass

# Get and clear message data
def get_msg_dict(request):
	msg_dict = {'head' : request.session.get('msg_head'), 'msg' : request.session.get('msg'), 'lvl' : request.session.get('msg_lvl')}
	clear_msg(request)
	return msg_dict

# Return dictionary for use in the header template (called in every response)
def generate_header_dict(request, header_text):
	tracking_code = None
	try:
		# Expand session for another hour
		request.session.set_expiry(3600)
	# Ignore otherwise
	except Exception:
		pass
	# Form list of strings for all movies [title (year),] for typeahead search
	movies_titles_years = Movies.objects.values_list('Title', 'Year').order_by('Title')
	search_list = []
	for title, year in movies_titles_years:
		search_list.append(unicode(title) + unicode(' (') + unicode(year) + unicode(')'))
	return {'msg_dict' : get_msg_dict(request), 'header_text' : header_text, 'tracking_code' : settings.TRACKING_CODE, 'search_list' : search_list}

# Logout and return profile of user
def logout_command(request):
	try:
		logged_in_id = request.session['auth_profile_id']
		del request.session['auth_profile_id']
		del request.session['auth_profile_username']
		del request.session['admin']
		# Give 5 minutes of unlogged in access (to create profile or login)
		request.session['auth_access'] = True
		request.session.set_expiry(300)
		profile = Profiles.objects.get(id=logged_in_id)
		return profile
	# Ignore if none logged in
	except KeyError:
		profile = Profiles()
		return profile

# Login and return profile of user
def login_command(request, profile):
	# Logout others first
	logout_command(request)
	request.session['auth_profile_id'] = profile.id
	request.session['auth_profile_username'] = profile.Username.encode('ascii', 'replace')
	request.session['admin'] = profile.IsAdmin
	# Give hour of logged in access
	request.session.set_expiry(3600)
	# No longer need access key
	try:
		del request.session['auth_access']
	except KeyError:
		pass
	return profile

# Return logged in profile information in a dictionary otherwise redirect
def check_and_get_session_info(request, logged_in_profile_info, check_access = False, show_msg = True):
	if request.session.get('auth_profile_id'):
		logged_in_profile_info['id'] = request.session.get('auth_profile_id')
		logged_in_profile_info['username'] = request.session.get('auth_profile_username')
		logged_in_profile_info['admin'] = request.session.get('admin')
		return True
	elif check_access and request.session.get('auth_access'):
		return True
	elif check_access:
		if show_msg:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 'warning')
		response = redirect('webapp.views.site.access')
		if request.GET.get('redirect'):
			response['LOCATION'] += '?redirect=' + request.GET.get('redirect')
		elif not request.GET.get('only_inherit_redirect'):
			response['LOCATION'] += '?redirect=' + urllib.quote(request.path, '')
		return response
	else:
		if show_msg:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 'warning')
		response = redirect('webapp.views.profile.login')
		if request.GET.get('redirect'):
			response['LOCATION'] += '?redirect=' + request.GET.get('redirect')
		elif not request.GET.get('only_inherit_redirect'):
			response['LOCATION'] += '?redirect=' + urllib.quote(request.path, '')
		return response

# Return true if property is associated with any movies
def person_is_relevant(person):
	properties = Properties.objects.filter(ConsumeableTypeId=ConsumeableTypes.objects.get(Description='MOVIE'), PropertyId=person.id)
	for property in properties:
		if property.PropertyTypeId.TableName == 'PEOPLE':
			return True
	return False

# Return true if property is associated with any movies
def genre_is_relevant(genre):
	properties = Properties.objects.filter(ConsumeableTypeId=ConsumeableTypes.objects.get(Description='MOVIE'), PropertyId=genre.id)
	for property in properties:
		if property.PropertyTypeId.TableName == 'GENRES':
			return True
	return False

def source_is_relevant(source):
	return Associations.objects.filter(SourceId=source).count() > 0

# Iterate through all ranked titles and set rank to increments of one
def update_rankings(profile):
	associations = Associations.objects.filter(ProfileId=profile,Consumed=True).exclude(Rank__isnull=True).order_by('Rank')
	for i in range(len(associations)):
		associations[i].Rank = i+1
		associations[i].save()

# Return dictionary of all consumeable and property types
def get_type_dict():
	type_dict = {}
	for consumeable_type in ConsumeableTypes.objects.all():
		type_dict['CONSUMEABLE_' + consumeable_type.Description] = consumeable_type
	for property_type in PropertyTypes.objects.all():
		type_dict['PROPERTY_' + property_type.Description] = property_type
	return type_dict
