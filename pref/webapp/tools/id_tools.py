import json, urllib, urllib2, zlib
from django.conf import settings
from webapp.models import Movies, People, Genres
from oauth import OAuthRequest
from oauth.signature_method.hmac_sha1 import OAuthSignatureMethod_HMAC_SHA1
from xml.dom.minidom import parseString

# Return wikipedia identifier (text) given url or id
def wikipedia_id_from_input(wikipedia_input):
	wikipedia_id = wikipedia_input[29:] if wikipedia_input.find('http://en.wikipedia.org/wiki/') == 0 else wikipedia_input
	return wikipedia_id

# Return dictionary of wikipedia data for specified wikipedia id (just checks valid id currently)
def get_wikipedia_dict(wikipedia_id):
	try:
		# Query wikipedia
		req = urllib2.Request('http://en.wikipedia.org/w/api.php?format=xml&action=query&titles='+urllib.quote(wikipedia_id.encode('utf8')))
		res = urllib2.urlopen(req)
		if res.getcode() == 200:
			# Parse xml response
			dom = parseString(res.read())
			if dom.getElementsByTagName('page'):
				for elem in dom.getElementsByTagName('page'):
					if elem.hasAttribute('missing'):
						return {'Response' : False}
					else:
						return {'Response' : True}
			else:
				return {'Response' : False}
		else:
			return {'Response' : False}
	except Exception:
		return {'Response' : False}

# Return movie given wikipedia url or id (only sets id currently)
def movie_from_wikipedia_input(wikipedia_input):
	movie = Movies()
	directors, writers, actors, genres = [], [], [], []
	wikipedia_id = wikipedia_id_from_input(wikipedia_input)
	if wikipedia_id:
		try:
			wikipedia_dict = get_wikipedia_dict(wikipedia_id)
			if wikipedia_dict.get('Response') == True:
				movie.WikipediaId = wikipedia_id
			else:
				return {'error_msg' : 'Invalid'}
		except Exception:
			return {'error_msg' : 'Wikipedia API failed, please try again.'}
	else:
		return {'error_msg' : 'Could not be parsed from input.'}
	return {'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres}


# Return movie from wikipedia given movie object (only sets id currently)
def wikipedia_movie_from_title(cur_movie):
	movie = Movies()
	if cur_movie and cur_movie.Title and cur_movie.Year:
		try:
			# Query wikipedia search API
			req = urllib2.Request('http://en.wikipedia.org/w/api.php?format=xml&action=query&list=search&srlimit=10&srsearch='+urllib.quote(cur_movie.Title.encode('ascii', 'ignore'))+'%20'+str(cur_movie.Year)+'%20film')
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				# Parse xml response
				dom = parseString(res.read())
				# If elements returned
				if dom.getElementsByTagName('p'):
					id = None
					for elem in dom.getElementsByTagName('p'):
						cur_id = elem.getAttribute('title')
						comp_cur_id = cur_id.lower()
						comp_id = cur_movie.Title.lower()
						# If movie title is contained in wikipedia title
						if comp_id in comp_cur_id:
							id = cur_id
							break
					if id:
						return movie_from_wikipedia_input(id)
					else:
						return {'error_msg' : 'Invalid'}
				else:
					return {'error_msg' : 'Invalid'}
			else:
				return {'error_msg' : 'Invalid'}
		except Exception:
			return {'error_msg' : 'Wikipedia API failed, please try again.'}
	else:
		return {'error_msg' : 'Could not be parsed from input.'}

# Return imdb identifier (ttxxxx) given url or id
def imdb_id_from_input(imdb_input):
	# If direct id input, check for tt followed only by digits
	if len(imdb_input) > 2 and imdb_input[0:2] == 'tt':
		for i in range(2, len(imdb_input)):
			if not imdb_input[i].isdigit():
				return None
			elif i == len(imdb_input)-1:
				return imdb_input
	# If direct id input without tt, check for all digits and return with 'tt'
	for i in range(len(imdb_input)):
		if not imdb_input[i].isdigit():
			break
		elif i == len(imdb_input)-1:
			return 'tt' + imdb_input
	imdb_str = 'http://www.imdb.com/title/tt'
	id_end = len(imdb_input)
	# If url input, extract imdb id
	if imdb_input.find(imdb_str) != 0 or len(imdb_input) < len(imdb_str)+1:
		return None
	# Start with tt
	id_start = len(imdb_str) - 2
	# Continue until no more numbers
	for i in range(id_start+2, len(imdb_input)):
		if imdb_input[i] == '/':
			id_end = i
			break
		if not imdb_input[i].isdigit():
			return None
	imdb_id = imdb_input[id_start:id_end]
	return imdb_id

# Return dictionary of imdb data for specified imdb id
def get_imdb_dict(imdb_id):
	try:
		# Query IMDb using omdbapi (not affiliated with imdb)
		req = urllib2.Request('http://www.omdbapi.com/?i='+imdb_id)
		res = urllib2.urlopen(req)
		if res.getcode() == 200:
			# Parse json response
			return json.loads(res.read())
		else:
			return {'Response' : False}
	except Exception:
		return {'Response' : False}

# Return movie given imdb url or id
def movie_from_imdb_input(imdb_input):
	directors, writers, actors, genres = [], [], [], []
	movie = Movies()
	imdb_id = imdb_id_from_input(imdb_input)
	if imdb_id:
		try:
			imdb_dict = get_imdb_dict(imdb_id)
			if imdb_dict.get('Response') == 'True':
				movie.ImdbId = imdb_id
				if imdb_dict.get('Title'):
					movie.Title = imdb_dict.get('Title')
				if imdb_dict.get('Year'):
					movie.Year = int(imdb_dict.get('Year'))
				if imdb_dict.get('Runtime') and imdb_dict.get('Runtime') != "N/A":
					runtime_str = imdb_dict.get('Runtime')
					# Convert [/d+] min to minutes
					try:
						runtime = int(runtime_str[:runtime_str.find(" ")])
					except Exception:
						pass
					movie.Runtime = str(runtime)
				if imdb_dict.get('Director'):
					cur_directors = imdb_dict.get('Director').split(', ')
					for i in range(len(cur_directors)):
						directors.append({'name' : cur_directors[i]})
				if imdb_dict.get('Writer'):
					cur_writers = imdb_dict.get('Writer').split(', ')
					for i in range(len(cur_writers)):
						cur_writer = cur_writers[i]
						cur_writer = cur_writer[:cur_writer.find("(")] if cur_writer.find("(") >= 0 else cur_writer
						writers.append({'name' : cur_writer})
				if imdb_dict.get('Actors'):
					cur_actors = imdb_dict.get('Actors').split(', ')
					for i in range(len(cur_actors)):
						actors.append({'name' : cur_actors[i]})
				if imdb_dict.get('Genre'):
					cur_genres = imdb_dict.get('Genre').split(', ')
					for i in range(len(cur_genres)):
						genres.append(cur_genres[i])
			else:
				return {'error_msg' : 'Invalid'}
		except Exception:
			return {'error_msg' : 'IMDb API failed, please try again.'}
	else:
		return {'error_msg' : 'Could not be parsed from input.'}
	return {'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres}

# Return netflix identifier (number) given url or id
def netflix_id_from_input(netflix_input):
	# If direct id input, check for digits only
	for i in range(len(netflix_input)):
		if not netflix_input[i].isdigit():
			break
		elif i == len(netflix_input)-1:
			return netflix_input
	netflix_str = 'http://'
	id_end = len(netflix_input)
	# If url input
	if netflix_input.find(netflix_str) != 0 or len(netflix_input) < len(netflix_str)+1:
		return None;
	# Start with subdomain
	id_start = len(netflix_str)
	num_hit = netflix_input[id_start].isdigit()
	# Find first string matching /[/d+]/
	for i in range(id_start, len(netflix_input)):
		if num_hit and (netflix_input[i] == '/' or netflix_input[i] == '?'):
			id_end = i
			break
		elif not num_hit and netflix_input[i] == '/':
			if i + 1 < len(netflix_input) and netflix_input[i+1].isdigit():
				num_hit = True
			id_start = i + 1
			continue
		if not netflix_input[i].isdigit() and num_hit:
			num_hit = False
		if i == len(netflix_input) - 1 and not num_hit:
			return None
	netflix_id = netflix_input[id_start:id_end]
	return netflix_id

# Return dom of netflix data for specified netflix id
def get_netflix_dom(netflix_id, href = None):
	try:
		# Query netflix API using OAuth
		consumer = {'oauth_token': settings.API_KEYS['NETFLIX'], 'oauth_token_secret': settings.API_KEYS['NETFLIX_SECRET']}
		request = None
		if href:
			request = OAuthRequest(href)
		else:
			request = OAuthRequest('http://api-public.netflix.com/catalog/titles/movies/'+netflix_id)
		request.sign_request(OAuthSignatureMethod_HMAC_SHA1, consumer)
		url = request.to_url(include_oauth=True)
		req = urllib2.Request(url)
		res = urllib2.urlopen(req)
		if res.getcode() == 200:
			# Parse xml response
			return parseString(res.read())
		else:
			return {'Response' : False}
	except Exception:
		return {'Response' : False}

# Return dictionary of netflix availability data for specified movie
def get_netflix_availability_dict(movie):
	if movie.NetflixId:
		availability_dict = {'BLU_RAY' : False, 'DVD' : False, 'INSTANT' : False}
		dom = get_netflix_dom(None, 'http://api-public.netflix.com/catalog/titles/movies/' + movie.NetflixId + '/format_availability')
		try:
			if dom.get('Response') == False:
				return {'error_msg' : 'Invalid'}
		except Exception:
			pass
		for node in dom.getElementsByTagName('availability'):
			if node.getElementsByTagName('category') and node.getElementsByTagName('category')[0] and node.getElementsByTagName('category')[0].getAttribute('label'):
				availability_label = node.getElementsByTagName('category')[0].getAttribute('label')
				if availability_label == 'Blu-ray':
					availability_dict['BLU-RAY'] = True
				elif availability_label == 'DVD':
					availability_dict['DVD'] = True
				elif availability_label == 'instant':
					availability_dict['INSTANT'] = True
		return availability_dict
	else:
		return {'error_msg' : 'Invalid'}

# Return movie given netflix url or id
def movie_from_netflix_input(netflix_input):
	movie = Movies()
	directors, writers, actors, genres = [], [], [], []
	netflix_id = netflix_id_from_input(netflix_input)
	if netflix_id:
		try:
			dom = get_netflix_dom(netflix_id)
			try:
				if dom.get('Response') == False:
					return {'error_msg' : 'Invalid'}
			except Exception:
				pass
			movie.NetflixId = netflix_id
			if dom.getElementsByTagName('title') and dom.getElementsByTagName('title')[0]:
				title = dom.getElementsByTagName('title')[0].getAttribute('regular')
				if title == '':
					title = dom.getElementsByTagName('title')[0].getAttribute('short')
			if dom.getElementsByTagName('release_year') and dom.getElementsByTagName('release_year')[0]:
				movie.Year = int(dom.getElementsByTagName('release_year')[0].childNodes[0].data)
			if dom.getElementsByTagName('runtime') and dom.getElementsByTagName('runtime')[0]:
				runtime = int(dom.getElementsByTagName('runtime')[0].childNodes[0].data)
				movie.Runtime = int(runtime / 60)
			for node in dom.getElementsByTagName('link'):
				if node.getAttribute('title') == 'directors' or node.getAttribute('title') == 'cast':
					# Retrive directors and actors by following cast links in dom
					is_cast = node.getAttribute('title') == 'cast'
					href = node.getAttribute('href')
					person_dom = get_netflix_dom(None, href)
					for person in person_dom.getElementsByTagName('person'):
						if not is_cast:
							directors.append({'name' : person.getElementsByTagName('name')[0].childNodes[0].data})
						else:
							actors.append({'name' : person.getElementsByTagName('name')[0].childNodes[0].data})
			for node in dom.getElementsByTagName('category'):
				if node.getAttribute('scheme') == 'http://api.netflix.com/categories/genres':
					genre = node.getAttribute('label')
					# Only add single word genres
					if len(genre.split(' ')) == 1:
						genres.append(genre)
		except Exception:
			return {'error_msg' : 'Netflix API failed, please try again.'}
	else:
		return {'error_msg' : 'Could not be parsed from input.'}
	return {'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres}

# Return movie from netflix given movie object
def netflix_movie_from_title(cur_movie, only_id = False):
	movie = Movies()
	if cur_movie and cur_movie.Title and cur_movie.Year:
		try:
			# Query netflix search API with OAuth
			consumer = {'oauth_token': settings.API_KEYS['NETFLIX'], 'oauth_token_secret': settings.API_KEYS['NETFLIX_SECRET']}
			params = {'term' : cur_movie.Title, 'start_index' : 0, 'max_results' : 5}
			request = OAuthRequest('http://api-public.netflix.com/catalog/titles', 'GET', params)
			request.sign_request(OAuthSignatureMethod_HMAC_SHA1, consumer)
			url = request.to_url(include_oauth=True)
			req = urllib2.Request(url)
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				# Parse xml response
				dom = parseString(res.read())
				for node in dom.getElementsByTagName('catalog_title'):
					# If year is the same
					if node.getElementsByTagName('release_year') and node.getElementsByTagName('release_year')[0] and abs(cur_movie.Year - int(node.getElementsByTagName('release_year')[0].childNodes[0].data)) < 1:
						if node.getElementsByTagName('id') and node.getElementsByTagName('id')[0]:
							if only_id:
								return {'id' : netflix_id_from_input(str(node.getElementsByTagName('id')[0].childNodes[0].data))}
							else:
								return movie_from_netflix_input(node.getElementsByTagName('id')[0].childNodes[0].data)
				return {'error_msg' : 'Invalid'}
			else:
				return {'error_msg' : 'Invalid'}
		except Exception:
			return {'error_msg' : 'Netflix API failed, please try again'}
	else:
		return {'error_msg' : 'No title to search from.'}

# Return rotten tomatoes identifier given id only
def rottentomatoes_id_from_input(rottentomatoes_input):
	# If all digits
	for i in range(len(rottentomatoes_input)):
		if not rottentomatoes_input[i].isdigit():
			return None
	return rottentomatoes_input

# Return dictionary of rotten tomatoes data for specified rotten tomatoes id
def get_rottentomatoes_dict(rottentomatoes_id):
	try:	
		# Query rotten tomatoes API
		req = urllib2.Request('http://api.rottentomatoes.com/api/public/v1.0/movies/'+rottentomatoes_id+'.json?apikey='+settings.API_KEYS['ROTTEN_TOMATOES'])
		res = urllib2.urlopen(req)
		if res.getcode() == 200:
			data = res.read()
			if res.info().get("Content-Encoding") == 'gzip':
				data = zlib.decompress(data, 16+zlib.MAX_WBITS)
			# Parse json response
			return json.loads(data)
		else:
			return {'Response' : False}
	except Exception:
		return {'Response' : False}

# Return dictionary of supplemental rotten tomatoes data for specified movie
def get_rottentomatoes_supplemental_dict(movie):
	if movie.RottenTomatoesId:
		supplemental_dict = {'POSTER_HREF' : False, 'CONSENSUS' : False, 'CRITICS_RATING' : False, 'CRITICS_SCORE' : False, 'AUDIENCE_RATING' : False, 'AUDIENCE_SCORE' : False}
		rt_dict = get_rottentomatoes_dict(movie.RottenTomatoesId)
		try:
			if rt_dict.get('Response') == False:
				return {'error_msg' : 'Invalid'}
		except Exception:
			pass
		if rt_dict.get('posters'):
			if rt_dict.get('posters').get('detailed'):
				supplemental_dict['POSTER_HREF'] = rt_dict.get('posters').get('detailed')
			elif rt_dict.get('posters').get('profile'):
				supplemental_dict['POSTER_HREF'] = rt_dict.get('posters').get('profile')
		if rt_dict.get('critics_consensus'):
			supplemental_dict['CONSENSUS'] = rt_dict.get('critics_consensus')
		if rt_dict.get('ratings'):
			if rt_dict.get('ratings').get('critics_rating'):
				if rt_dict.get('ratings').get('critics_rating') == 'Certified Fresh':
					supplemental_dict['CRITICS_RATING'] = 'certified_fresh.png'
				elif rt_dict.get('ratings').get('critics_rating') == 'Fresh':
					supplemental_dict['CRITICS_RATING'] = 'fresh.png'
				elif rt_dict.get('ratings').get('critics_rating') == 'Rotten':
					supplemental_dict['CRITICS_RATING'] = 'rotten.png'
			if rt_dict.get('ratings').get('audience_rating'):
				if rt_dict.get('ratings').get('audience_rating') == 'Upright':
					supplemental_dict['AUDIENCE_RATING'] = 'upright.png'
				elif rt_dict.get('ratings').get('audience_rating') == 'Spilled':
					supplemental_dict['AUDIENCE_RATING'] = 'spilled.png'
			if rt_dict.get('ratings').get('critics_score'):
				supplemental_dict['CRITICS_SCORE'] = rt_dict.get('ratings').get('critics_score')
			if rt_dict.get('ratings').get('audience_score'):
				supplemental_dict['AUDIENCE_SCORE'] = rt_dict.get('ratings').get('audience_score')
		return supplemental_dict
	else:
		return {'error_msg' : 'Invalid'}

# Return movie given rotten tomatoes id
def movie_from_rottentomatoes_input(rottentomatoes_input):
	movie = Movies()
	directors, writers, actors, genres = [], [], [], []
	rottentomatoes_id = rottentomatoes_id_from_input(rottentomatoes_input)
	if rottentomatoes_id:
		try:
			movie_dict = get_rottentomatoes_dict(rottentomatoes_id)
			try:
				if movie_dict.get('Response') == False:
					return {'error_msg' : 'Invalid'}
			except Exception:
				pass
			movie.RottenTomatoesId = str(movie_dict.get('id'))
			movie.Title = movie_dict.get('title')
			movie.Year = movie_dict.get('year')
			if movie_dict.get('runtime'):
				runtime_str = str(movie_dict.get('runtime'))
			if movie_dict.get('abridged_directors'):
				for j in range(len(movie_dict.get('abridged_directors'))):
					directors.append({'name' : movie_dict.get('abridged_directors')[j].get('name')})
			if movie_dict.get('abridged_cast'):
				for j in range(len(movie_dict.get('abridged_cast'))):
					actors.append({'name' : movie_dict.get('abridged_cast')[j].get('name'), 'id' : movie_dict.get('abridged_cast')[j].get('id')})
			if movie_dict.get('genres'):
				for j in range(len(movie_dict.get('genres'))):
					genres.append(movie_dict.get('genres')[j])
		except Exception:
			return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
	else:
		return {'error_msg' : 'Could not be parsed from input.'}
	return {'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres}

# Return movie from rotten tomatoes given movie object (optioanally return only id)
def rottentomatoes_movie_from_title(cur_movie, only_id = False):
	movie = Movies()
	page_limit = 5
	if cur_movie and cur_movie.Title and cur_movie.Year:
		try:
			# Query rotten tomatoes search API
			encoded_title = urllib.quote(cur_movie.Title)
			req = urllib2.Request('http://api.rottentomatoes.com/api/public/v1.0/movies.json?q='+encoded_title+'&page_limit=' + str(page_limit) + '&page=1&apikey='+settings.API_KEYS['ROTTEN_TOMATOES'])
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				# Parse json response
				rottentomatoes_dict = json.loads(res.read())
				if rottentomatoes_dict.get('total') > 0:
					min_length = page_limit if page_limit < rottentomatoes_dict.get('total') else rottentomatoes_dict.get('total')
					for i in range(min_length):
						movie_dict = rottentomatoes_dict.get('movies')[i]
						# If year is the same
						if movie_dict.get('year') and abs(cur_movie.Year - movie_dict.get('year')) < 1:
							if only_id:
								return {'id' : str(movie_dict.get('id'))}
							else:
								return movie_from_rottentomatoes_input(movie_dict.get('id'))
					return {'error_msg' : 'Invalid'}
				else:
					return {'error_msg' : 'Invalid'}
			else:
				return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
		except Exception:
			return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
	else:
		return {'error_msg' : 'No title to search from.'}

# Return movie given user inputs (imdb, netflix, rotten tomatoes) (url, id)
def movie_from_inputs(imdb_input, netflix_input, rottentomatoes_input, wikipedia_input):
	imdb_movie, rottentomatoes_movie, netflix_movie, wikipedia_movie = None, None, None, None
	directors, writers, actors, genres = [], [], [], []
	movie = Movies()
	error_list = {}
	success = True
	if imdb_input and len(imdb_input) > 0:
		imdb_res = movie_from_imdb_input(imdb_input)
		if imdb_res.get('movie'):
			imdb_movie = imdb_res.get('movie')
			movie.ImdbId = imdb_res.get('movie').ImdbId
			movie.Title = imdb_res.get('movie').Title
			movie.Year = imdb_res.get('movie').Year
			movie.Runtime = imdb_res.get('movie').Runtime
			directors = imdb_res.get('directors')
			writers = imdb_res.get('writers')
			actors = imdb_res.get('actors')
			genres = imdb_res.get('genres')
		else:
			error_list['ImdbId'] = imdb_res.get('error_msg')
			success = False
	# Imdb success required for now
	else:
		error_list['ImdbId'] = 'This field cannot be blank.'
		success = False
	if netflix_input and len(netflix_input) > 0:
		netflix_res = movie_from_netflix_input(netflix_input)
		if netflix_res.get('movie'):
			netflix_movie = netflix_res.get('movie')
			movie.NetflixId = netflix_movie.NetflixId
		else:
			error_list['NetflixId'] = netflix_res.get('error_msg')
			success = False
	# If no netflix input, get netflix movie given imdb movie
	elif movie.Title and movie.Year:
		netflix_res = netflix_movie_from_title(movie)
		if netflix_res.get('movie'):
			netflix_movie = netflix_res.get('movie')
			movie.NetflixId = netflix_movie.NetflixId
	if rottentomatoes_input and len(rottentomatoes_input) > 0:
		rottentomatoes_res = movie_from_rottentomatoes_input(rottentomatoes_input)
		if rottentomatoes_res.get('movie'):
			rottentomatoes_movie = rottentomatoes_res.get('movie')
			movie.RottenTomatoesId = rottentomatoes_movie.RottenTomatoesId
			# Use better cast list from rotten tomatoes
			actors = rottentomatoes_res.get('actors')
		else:
			error_list['RottenTomatoesId'] = rottentomatoes_res.get('error_msg')
			success = False
	# If no rotten tomatoes input, get rotten tomatoes movie given imdb movie
	elif movie.Title and movie.Year:
		rottentomatoes_res = rottentomatoes_movie_from_title(movie)
		if rottentomatoes_res.get('movie'):
			rottentomatoes_movie = rottentomatoes_res.get('movie')
			movie.RottenTomatoesId = rottentomatoes_movie.RottenTomatoesId
			# Use better cast list from rotten tomatoes
			actors = rottentomatoes_res.get('actors')
	# Rotten Tomatoes success required for now
	else:
		error_list['RottenTomatoesId'] = 'This field cannot be blank.'
		success = False
	# Use given wikipedia input with no validation, maybe include in future
	if wikipedia_input and len(wikipedia_input) > 0:
		wikipedia_res = movie_from_wikipedia_input(wikipedia_input)
		if wikipedia_res.get('movie'):
			wikipedia_movie = wikipedia_res.get('movie')
			movie.WikipediaId = wikipedia_movie.WikipediaId
		else:
			error_list['WikipediaId'] = wikipedia_res.get('error_msg')
			success = False
	elif movie.Title and movie.Year:
		wikipedia_res = wikipedia_movie_from_title(movie)
		if wikipedia_res.get('movie'):
			wikipedia_movie = wikipedia_res.get('movie')
			movie.WikipediaId = wikipedia_movie.WikipediaId
	return {'success': success, 'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'error_list' : error_list}
