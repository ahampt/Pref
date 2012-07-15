import json, urllib, urllib2
from django.conf import settings
from id_tools import netflix_id_from_input
from webapp.models import Movies
from oauth import OAuthRequest
from oauth.signature_method.hmac_sha1 import OAuthSignatureMethod_HMAC_SHA1
from xml.dom.minidom import parseString

# Return movie from imdb given title and year
def imdb_movie_from_data(search_term, year):
	try:
		movie = Movies()
		# Query imdbapi (not affiliated with imdb)
		search_term = urllib.quote(search_term.encode('ascii', 'ignore'))
		req = urllib2.Request('http://www.imdbapi.com/?t='+search_term+'&y='+str(year))
		res = urllib2.urlopen(req)
		if res.getcode() == 200:
			# Parse json response
			imdb_dict = json.loads(res.read())
			if imdb_dict.get('Response') == 'True':
				if imdb_dict.get('imdbID'):
					movie.ImdbId = imdb_dict.get('imdbID')
				if imdb_dict.get('Title'):
					movie.Title = imdb_dict.get('Title')
				if imdb_dict.get('Year'):
					movie.Year = int(imdb_dict.get('Year'))
				if imdb_dict.get('Runtime'):
					runtime_str = imdb_dict.get('Runtime')
					runtime = 0
					num_hit, first = False, True
					str_to_convert = ''
					# Convert [/d+] h [/d+] m to minutes
					for char in runtime_str:
						# Add digits to temp string
						if char.isdigit():
							num_hit = True
							str_to_convert += char
							continue
						# Convert temp string from hours to minutes and add to runtime
						if char.isspace() and num_hit and first:
							runtime += int(str_to_convert) * 60
							first = False
							num_hit = False
							str_to_convert = ''
							continue
						# Add minutes from temp string to runtime
						if char.isspace() and num_hit and not first:
							runtime += int(str_to_convert)
					movie.Runtime = str(runtime)
			else:
				return {'error' : 'Invalid IMDb Search'}
		else:
			return {'error_msg' : 'IMDb API failed, please try again.'}
		return {'movie' : movie}
	except:
		return {'error_msg' : 'IMDb API failed, please try again.'}

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
						# Get movie from imdb to return
						res_dict = imdb_movie_from_data(title, year)
						if res_dict.get('movie'):
							movie = res_dict.get('movie')
							duplicate = False
							for j in range(len(movies)):
								if movies[j].ImdbId == movie.ImdbId:
									duplicate = True
									break
							if not duplicate:
								movie.NetflixId = id
								movies.append(movie)
						elif res_dict.get('error'):
							continue
						else:
							return {'error_msg' : res_dict.get('error_msg')}
					else:
						return {'error_msg' : 'Invalid Netflix Search'}
			else:
				return {'error_msg' : 'Invalid Netflix Search'}
		except:
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
				rottentomatoes_dict = json.loads(res.read())
				if rottentomatoes_dict.get('total') > 0:
					min_length = page_limit if page_limit < rottentomatoes_dict.get('total') else rottentomatoes_dict.get('total')
					for i in range(min_length):
						movie_dict = rottentomatoes_dict.get('movies')[i]
						# Get movie from imdb to return
						res_dict = imdb_movie_from_data(movie_dict.get('title'), movie_dict.get('year'))
						if res_dict.get('movie'):
							movie = res_dict.get('movie')
							duplicate = False
							for j in range(len(movies)):
								if movies[j].ImdbId == movie.ImdbId:
									duplicate = True
									break
							if not duplicate:
								movie.RottenTomatoesId = movie_dict.get('id')
								movies.append(movie)
						elif res_dict.get('error'):
							continue
						else:
							return {'error_msg' : res_dict.get('error_msg')}
				else:
					return {'error_msg' : 'Invalid Rotten Tomatoes Search'}
			else:
				return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
		except:
			return {'error_msg' : 'Rotten Tomatoes API failed, please try again.'}
	else:
		return {'error_msg' : 'No term to search from.'}
	if len(movies) > 0:
		return {'movies' : movies}
	else:
		return {'error_msg' : 'No results found.'}

# Return list of movies given search term and length
def movies_from_term(search_term, how_many):
	error_list = {}
	movies = []
	success = True
	rottentomatoes_movies, netflix_movies = [], []
	if search_term and len(search_term) > 0:
		# Search rotten tomatoes and netflix (IMDb data returned)
		rt_dict = rottentomatoes_movies_from_term(search_term, how_many)
		net_dict = netflix_movies_from_term(search_term, how_many)
		if rt_dict.get('movies'):
			rottentomatoes_movies = rt_dict.get('movies')
			movies = rottentomatoes_movies
		else:
			error_list['RottenTomatoesSearch'] = rt_dict.get('error_msg')
		if net_dict.get('movies'):
			netflix_movies = net_dict.get('movies')
		else:
			error_list['NetflixSearch'] = net_dict.get('error_msg')
		if not rt_dict.get('movies') and not net_dict.get('movies'):
			success = False
		# If duplicate imdb id, delete the netflix value
		for movie in movies:
			i = 0
			while i < len(netflix_movies):
				net_movie = netflix_movies[i]
				if movie.ImdbId == net_movie.ImdbId:
					movie.NetflixId = net_movie.NetflixId
					del netflix_movies[i]
					break
				else:
					i += 1
		for movie in netflix_movies:
			movies.append(movie)
	else:
		success = False
	return {'success': success, 'movies' : movies, 'error_list' : error_list}
