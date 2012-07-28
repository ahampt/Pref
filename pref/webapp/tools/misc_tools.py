import logging
from django.conf import settings
from webapp.models import Profiles, Movies, People, Genres, MovieProperties, ProfileMovies

profile_logger = logging.getLogger('log.profile')
movie_logger = logging.getLogger('log.movie')
property_logger = logging.getLogger('log.property')
associate_logger = logging.getLogger('log.associate')

# Create and save association given movie and property
def create_movie_property(movie, property_id, property_name, type, logged_in_profile_username):
	try:
		property = MovieProperties(MovieId = movie, PropertyId = property_id, Type = type)
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
			create_movie_property(movie, person.id, person.UrlName, 0, logged_in_profile_username)
		# Create and associate new property
		except:
			person = People(Name=director)
			person.full_clean()
			person.save()
			property_logger.info(person.UrlName + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, person.id, person.UrlName, 0, logged_in_profile_username)
	for writer in writers:
		# Associate old property
		try:
			person = People.objects.get(Name=writer)
			create_movie_property(movie, person.id, person.UrlName, 1, logged_in_profile_username)
		# Create and associate new property
		except:
			person = People(Name=writer)
			person.full_clean()
			person.save()
			property_logger.info(person.UrlName + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, person.id, person.UrlName, 1, logged_in_profile_username)
	for actor in actors:
		# Associate old property
		try:
			person = People.objects.get(Name=actor)
			create_movie_property(movie, person.id, person.UrlName, 2, logged_in_profile_username)
		# Create and associate new property
		except:
			person = People(Name=actor)
			person.full_clean()
			person.save()
			property_logger.info(person.UrlName + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, person.id, person.UrlName, 2, logged_in_profile_username)
	for genre in genres:
		# Associate old property
		try:
			g = Genres.objects.get(Description=genre)
			create_movie_property(movie, g.id, person.UrlName, 3, logged_in_profile_username)
		# Create and associate new property
		except:
			g = Genres(Description=genre)
			g.save()
			property_logger.info(g.Description + ' Create Success by ' + logged_in_profile_username)
			create_movie_property(movie, g.id, g.Description, 3, logged_in_profile_username)

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

# Return dictionary for use in the header template (called in every response)
def generate_header_dict(request, header_text):
	msg_heading, msg, color, tracking_code = None, None, None, None
	try:
		# Expand session for another hour
		request.session.set_expiry(3600)
		# Set alert data if present
		msg_heading = request.session['msg_heading']
		msg = request.session['msg']
		msg_color_enum = request.session['msg_color_enum']
		if msg_color_enum == 0:
			color = 'default'
		elif msg_color_enum == 1:
			color = 'primary'
		elif msg_color_enum == 2:
			color = 'info'
		elif msg_color_enum == 3:
			color = 'success'
		elif msg_color_enum == 4:
			color = 'warning'
		elif msg_color_enum == 5:
			color = 'danger'
		elif msg_color_enum == 6:
			color = 'inverse'
		else:
			color = 'default'
		del request.session['msg_heading']
		del request.session['msg']
		del request.session['msg_color_enum']
	# Ignore otherwise
	except KeyError:
		pass
	# Form list of strings for all movies [title (year),] for typeahead search
	movies_titles_years = Movies.objects.values_list('Title', 'Year').order_by('Title')
	search_list = []
	for title, year in movies_titles_years:
		search_list.append(str(title) + ' (' + str(year) + ')')
	return {'msg_dict' : {'msg_heading' : msg_heading, 'msg' : msg, 'color' : color}, 'header_text' : header_text, 'tracking_code' : settings.TRACKING_CODE, 'search_list' : search_list}

# Set alert message data (title, content, color)
def set_msg(request, msg_heading, msg, msg_color_enum):
	request.session['msg_heading'] = msg_heading
	request.session['msg'] = msg
	request.session['msg_color_enum'] = msg_color_enum

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

# Return logged in profile
def get_logged_in_profile(request):
	try:
		if request.session.get('auth_profile_id'):
			return Profiles.objects.get(id=request.session['auth_profile_id'])
		else:
			return None
	except:
		return None

# Return true if property is associated with any movies
def person_is_relevant(person):
	properties = MovieProperties.objects.filter(PropertyId=person.id)
	for property in properties:
		if property.Type == 0 or property.Type == 1 or property.Type == 2:
			return True
	return False

# Return true if property is associated with any movies
def genre_is_relevant(genre):
	properties = MovieProperties.objects.filter(PropertyId=genre.id)
	for property in properties:
		if property.Type == 3:
			return True
	return False

# Iterate through all ranked titles and set rank to increments of one
def update_rankings(profile):
	assoc_movies = ProfileMovies.objects.filter(ProfileId=profile,Watched=True).exclude(Rank__isnull=True).order_by('Rank')
	for i in range(len(assoc_movies)):
		assoc_movies[i].Rank = i+1
		assoc_movies[i].save()
