import json, urllib, urllib2, zlib
from django.conf import settings
from id_tools import netflix_id_from_input
from webapp.models import Movies
from oauth import OAuthRequest
from oauth.signature_method.hmac_sha1 import OAuthSignatureMethod_HMAC_SHA1
from xml.dom.minidom import parseString

# Return movies from wikipedia given title and year (only sets id currently)
def wikipedia_movies_from_term(search_term, how_many):
	movies = []
	if search_term:
		try:
			# Query wikipedia search API
			req = urllib2.Request('http://en.wikipedia.org/w/api.php?format=xml&action=query&list=search&srlimit=' + str(how_many) + '&srsearch='+urllib.quote(search_term.encode('ascii', 'ignore'))+'%20film')
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				# Parse xml response
				dom = parseString(res.read())
				# If elements returned
				if dom.getElementsByTagName('p'):
					for elem in dom.getElementsByTagName('p'):
						movie = Movies( WikipediaId = elem.getAttribute('title'))
						movies.append(movie)
					if movies:
						return {'movies' : movies}
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

# Return list of movies from imdb given search term
def imdb_movies_from_term(search_term, page_limit):
	movies = []
	if search_term and len(search_term) > 0:
		#try:
			# Query omdbapi (not affiliated with imdb)
			search_term = urllib.quote(search_term.encode('ascii', 'ignore'))
			req = urllib2.Request('http://www.omdbapi.com/?s='+search_term+'&r=JSON')
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				# Parse json response
				res_dict = json.loads(res.read())
				if res_dict.get('Search'):
					min_length = page_limit if page_limit < len(res_dict.get('Search')) else len(res_dict.get('Search'))
					for i in range(min_length):
						movie = Movies()
						imdb_dict = res_dict.get('Search')[i]
						if imdb_dict.get('Type'):
							if imdb_dict.get('Type') == 'episode' or imdb_dict.get('Type') == 'series' or imdb_dict.get('Type') == 'game':
								continue
						if imdb_dict.get('imdbID'):
							movie.ImdbId = imdb_dict.get('imdbID')
						if imdb_dict.get('Title'):
							movie.Title = imdb_dict.get('Title')
						if imdb_dict.get('Year'):
							movie.Year = int(imdb_dict.get('Year'))
						if imdb_dict.get('Runtime'):
							runtime_str = imdb_dict.get('Runtime')
							# Convert [/d+] min to minutes
							try:
								runtime = int(runtime_str[:runtime_str.find(" ")])
							except Exception:
								pass
							movie.Runtime = str(runtime)
						if movie.ImdbId != '' and movie.Title != '' and movie.Year != 0 and movie.Runtime != '':
							movies.append(movie)
				else:
					return {'error' : 'No IMDb results found, please try again.'}
			else:
				return {'error_msg' : 'IMDb API failed, please try again.'}
		#except Exception:
		#	return {'error_msg' : 'IMDb API failed, please try again.'}
	else:
		return {'error_msg' : 'No term to search from.'}
	if len(movies) > 0:
		return {'movies' : movies}
	else:
		return {'error_msg' : 'No results found.'}

# Return list of movies from netflix given search term
def netflix_movies_from_term(search_term, page_limit):
	movies = []
	if search_term and len(search_term) > 0:
		try:
			# Query netflix search API with OAuth
			consumer = {'oauth_token': settings.API_KEYS['NETFLIX'], 'oauth_token_secret': settings.API_KEYS['NETFLIX_SECRET']}
			params = {'term' : search_term, 'start_index' : 0, 'max_results' : page_limit}
			request = OAuthRequest('http://api-public.netflix.com/catalog/titles', 'GET', params)
			request.sign_request(OAuthSignatureMethod_HMAC_SHA1, consumer)
			url = request.to_url(include_oauth=True)
			req = urllib2.Request(url)
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				dom = parseString(res.read())
				for node in dom.getElementsByTagName('catalog_title'):
					id, title, year = '', '', 0
					if node.getElementsByTagName('id') and node.getElementsByTagName('id')[0]:
						id = netflix_id_from_input(node.getElementsByTagName('id')[0].childNodes[0].data)
					if node.getElementsByTagName('title') and node.getElementsByTagName('title')[0]:
						title = node.getElementsByTagName('title')[0].getAttribute('regular')
						if title == '':
							title = node.getElementsByTagName('title')[0].getAttribute('short')
					if node.getElementsByTagName('release_year') and node.getElementsByTagName('release_year')[0]:
						year = int(node.getElementsByTagName('release_year')[0].childNodes[0].data)
					if id != '' and title != '' and year != 0:
						movie = Movies(Title = title, Year = year, NetflixId = id)
						movies.append(movie)
					else:
						return {'error_msg' : 'Invalid Netflix Search'}
			else:
				return {'error_msg' : 'Invalid Netflix Search'}
		except Exception:
			return {'error_msg' : 'Netflix API failed, please try again'}
	else:
		return {'error_msg' : 'No term to search from.'}
	if len(movies) > 0:
		return {'movies' : movies}
	else:
		return {'error_msg' : 'No results found.'}

# Return list of movies from rotten tomatoes given search term
def rottentomatoes_movies_from_term(search_term, page_limit):
	movies = []
	if search_term and len(search_term) > 0:
		try:
			# Query rotten tomatoes search API
			encoded_title = urllib.quote(search_term)
			req = urllib2.Request('http://api.rottentomatoes.com/api/public/v1.0/movies.json?q='+encoded_title+'&page_limit=' + str(page_limit) + '&page=1&apikey='+settings.API_KEYS['ROTTEN_TOMATOES'])
			res = urllib2.urlopen(req)
			if res.getcode() == 200:
				data = res.read()
				if res.info().get("Content-Encoding") == 'gzip':
					data = zlib.decompress(data, 16+zlib.MAX_WBITS)
				rottentomatoes_dict = json.loads(data)
				if rottentomatoes_dict.get('total') > 0:
					min_length = page_limit if page_limit < rottentomatoes_dict.get('total') else rottentomatoes_dict.get('total')
					for i in range(min_length):
						movie_dict = rottentomatoes_dict.get('movies')[i]
						movie = Movies(Title = movie_dict.get('title'), Year = movie_dict.get('year'), RottenTomatoesId = movie_dict.get('id'))
						movies.append(movie)
				else:
					return {'error_msg' : 'Invalid Rotten Tomatoes Search'}
			else:
				return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
		except Exception:
			return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
	else:
		return {'error_msg' : 'No term to search from.'}
	if len(movies) > 0:
		return {'movies' : movies}
	else:
		return {'error_msg' : 'No results found.'}

# Return dictionary of uncombined lists of movies from all sources given search term and length
def movies_from_apis_term(search_term, how_many):
	error_list = {}
	movies = []
	success = True
	imdb_movies, rottentomatoes_movies, netflix_movies, wikipedia_movies = [], [], [], []
	# Search imdb, rotten tomatoes and netflix
	imdb_dict = imdb_movies_from_term(search_term, how_many)
	rt_dict = rottentomatoes_movies_from_term(search_term, how_many)
	net_dict = netflix_movies_from_term(search_term, how_many)
	wiki_dict = wikipedia_movies_from_term(search_term, how_many)
	if imdb_dict.get('movies'):
		imdb_movies = imdb_dict.get('movies')
	else:
		error_list['ImdbSearch'] = imdb_dict.get('error_msg')
	if rt_dict.get('movies'):
		rottentomatoes_movies = rt_dict.get('movies')
	else:
		error_list['RottenTomatoesSearch'] = rt_dict.get('error_msg')
	if net_dict.get('movies'):
		netflix_movies = net_dict.get('movies')
	else:
		error_list['NetflixSearch'] = net_dict.get('error_msg')
	if wiki_dict.get('movies'):
		wikipedia_movies = wiki_dict.get('movies')
	else:
		error_list['WikipediaSearch'] = wiki_dict.get('error_msg')
	return {'imdb_movies' : imdb_movies, 'netflix_movies' : netflix_movies, 'rottentomatoes_movies' : rottentomatoes_movies, 'wikipedia_movies' : wikipedia_movies}

# Return list of movies given search term and length
def movies_from_term(search_term, how_many):
	error_list = {}
	movies = []
	success = True
	imdb_movies, rottentomatoes_movies, netflix_movies = [], [], []
	if search_term and len(search_term) > 0:
		# Search imdb, rotten tomatoes and netflix
		imdb_dict = imdb_movies_from_term(search_term, how_many)
		rt_dict = rottentomatoes_movies_from_term(search_term, how_many)
		net_dict = netflix_movies_from_term(search_term, how_many)
		if imdb_dict.get('movies'):
			imdb_movies = imdb_dict.get('movies')
		else:
			error_list['ImdbSearch'] = imdb_dict.get('error_msg')
		if rt_dict.get('movies'):
			rottentomatoes_movies = rt_dict.get('movies')
		else:
			error_list['RottenTomatoesSearch'] = rt_dict.get('error_msg')
		if net_dict.get('movies'):
			netflix_movies = net_dict.get('movies')
		else:
			error_list['NetflixSearch'] = net_dict.get('error_msg')
		if not imdb_dict.get('movies') and not rt_dict.get('movies') and not net_dict.get('movies'):
			success = False
		# Connect all of the results
		for movie in imdb_movies:
			if not movie.Year:
				break
			for rt_movie in rottentomatoes_movies:
				if movie.Title.lower() in rt_movie.Title.lower() and rt_movie.Year and abs(movie.Year - rt_movie.Year) < 2:
					movie.RottenTomatoesId = rt_movie.RottenTomatoesId
					rottentomatoes_movies.remove(rt_movie)
					break
			for net_movie in netflix_movies:
				if movie.Title.lower() in net_movie.Title.lower() and net_movie.Year and abs(movie.Year - net_movie.Year) < 2:
					movie.NetflixId = net_movie.NetflixId
					netflix_movies.remove(net_movie)
					break
			if movie.RottenTomatoesId == '':
				for rt_movie in rottentomatoes_movies:
					if rt_movie.Year and abs(movie.Year - rt_movie.Year) < 2:
						movie.RottenTomatoesId = rt_movie.RottenTomatoesId
						rt_movies.remove(rt_movie)
						break
			if movie.NetflixId == '':
				if net_movie.Year and abs(movie.Year - net_movie.Year) < 2:
					movie.NetflixId = net_movie.NetflixId
					netflix_movies.remove(net_movie)
					break
			if movie.RottenTomatoesId != '' and movie.NetflixId != '':
				movies.append(movie)
	else:
		success = False
	return {'success': success, 'movies' : movies, 'error_list' : error_list}
