import cgi, logging, urllib
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q
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
	except Exception:
		pass

# Send email to admin that person may be incorrect (to varying degree)
def person_notification(concern_level, person):
	email_from = settings.DEFAULT_FROM_EMAIL
	email_subject = 'Priority ' + str(concern_level) + ' Person Notification for ' + person.Name + ' [' + str(person.id) + ']'
	email_message = ''
	if concern_level == 3:
		email_message = 'This person was probably added incorrectly. Please check if this person is already in the database.'
	elif concern_level == 2:
		email_message = 'This person was probably updated correctly but use caution because a new rotten tomatoes id was added to this record. Please verify this action.'
	else:
		email_message = 'This person was probably matched correctly. Please verify this action.'
	# send email
	send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)

# Create or find the correct existing person handling duplicates carefully
def create_or_find_person(person_dict, logged_in_profile_username):
	people_with_same_name = People.objects.filter(Name=person_dict.get('name'))
	# First, try to match RT id
	if person_dict.get('id'):
		try:
			person = People.objects.get(RottenTomatoesId=person_dict.get('id'))
			return person
		except People.DoesNotExist:
			pass
	# or try to match name with or without an RT id
	elif people_with_same_name.count() == 1:
		person = people_with_same_name[0]
		if person.RottenTomatoesId:
			person_notification(1, person)
		return person
	people_with_same_name_null = people_with_same_name.filter(Q(RottenTomatoesId=None) | Q(RottenTomatoesId=''))
	# Next, try to find one entry with null RT id
	if people_with_same_name_null.count() == 1:
		person = people_with_same_name_null[0]
		if person_dict.get('id'):
			person.RottenTomatoesId = person_dict.get('id')
			person.save()
			person_notification(2, person)
		else:
			person_notification(1, person)
		return person
	# Lastly, add new person
	try:
		person = People(Name=person_dict.get('name'),RottenTomatoesId=person_dict.get('id'))
		if people_with_same_name.count() > 1:
			person_notification(3, person)
		person.full_clean()
		person.save()
		property_logger.info(person_dict.get('name').encode('ascii', 'replace') + ' Create Success by ' + logged_in_profile_username)
		return person
	except ValidationError:
		property_logger.info(person_dict.get('name').encode('ascii', 'replace') + ' Create Failure by ' + logged_in_profile_username)
		return None

# Create and save properties given movie and properties
def create_properties(movie, directors, writers, actors, genres, logged_in_profile_username):
	for director in directors:
		person = create_or_find_person(director, logged_in_profile_username)
		if person:
			create_movie_property(movie, person.id, person.UrlName, 'DIRECTOR', logged_in_profile_username)
	for writer in writers:
		person = create_or_find_person(writer, logged_in_profile_username)
		if person:
			create_movie_property(movie, person.id, person.UrlName, 'WRITER', logged_in_profile_username)
	for actor in actors:
		person = create_or_find_person(actor, logged_in_profile_username)
		if person:
			create_movie_property(movie, person.id, person.UrlName, 'ACTOR', logged_in_profile_username)
	for genre in genres:
		# Associate old property
		try:
			g = Genres.objects.get(Description=genre)
			create_movie_property(movie, g.id, g.Description, 'GENRE', logged_in_profile_username)
		# Create and associate new property
		except Exception:
			try:
				g = Genres(Description=genre)
				g.save()
				property_logger.info(g.Description + ' Create Success by ' + logged_in_profile_username)
				create_movie_property(movie, g.id, g.Description, 'GENRE', logged_in_profile_username)
			except ValidationError:
				property_logger.info(genre + ' Create Failure by ' + logged_in_profile_username)

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
	# Form list of strings for all movies [title (year),] for typeahead search
	movies_titles_years = Movies.objects.values_list('Title', 'Year').order_by('Title')
	search_list = []
	try:
		for title, year in movies_titles_years:
			search_list.append(title + ' (' + str(year) + ')')
	except Exception:
		pass
	search_list.extend([cgi.escape(name, True) for name in People.objects.values_list('Name', flat=True).order_by('Name').distinct()])
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
def login_command(request, profile, remember_me = False):
	# Logout others first
	logout_command(request)
	request.session['auth_profile_id'] = profile.id
	request.session['auth_profile_username'] = profile.Username.encode('ascii', 'replace')
	request.session['admin'] = profile.IsAdmin
	if remember_me:
		# Remain logged in for approximately 20 years which is near infinite for a single computer
		request.session.set_expiry(timedelta(days=7300))
	else:
		# Remain logged in until the browser is closed
		request.session.set_expiry(0)
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
			response['LOCATION'] += '?redirect=' + urllib.quote(str(request.get_full_path()), '')
		return response
	else:
		if show_msg:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 'warning')
		response = redirect('webapp.views.profile.login')
		if request.GET.get('redirect'):
			response['LOCATION'] += '?redirect=' + request.GET.get('redirect')
		elif not request.GET.get('only_inherit_redirect'):
			response['LOCATION'] += '?redirect=' + urllib.quote(str(request.get_full_path()), '')
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

# Convert POST value into datetime and check bounds (inclusive)
def date_from_input(input, upper_bound = None, lower_bound = None):
	try:
		if not input or (lower_bound and upper_bound and lower_bound > upper_bound):
			return None
		month = int(input[0:input.find('/')])
		day = int(input[input.find('/')+1:input.find('/', input.find('/')+1)])
		year = int(input[input.find('/', input.find('/')+1)+1:])
		new_date = datetime(year, month, day)
		if((not upper_bound or (upper_bound and new_date <= upper_bound)) and (not lower_bound or (lower_bound and new_date >= lower_bound))):
			return new_date
		else:
			if upper_bound and new_date > upper_bound:
				return upper_bound
			elif lower_bound and new_date < lower_bound:
				return lower_bound
			else:
				return None
	except Exception:
		return None
