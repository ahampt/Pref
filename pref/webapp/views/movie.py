import cgi, logging, math, random, sys, urllib
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webapp.tools.id_tools import wikipedia_id_from_input, wikipedia_movie_from_title, movie_from_inputs, imdb_id_from_input, movie_from_imdb_input, netflix_id_from_input, netflix_movie_from_title, movie_from_netflix_input, rottentomatoes_id_from_input, rottentomatoes_movie_from_title, movie_from_rottentomatoes_input, get_netflix_availability_dict, get_rottentomatoes_supplemental_dict
from webapp.tools.misc_tools import create_properties, imdb_link_for_movie, netflix_link_for_movie, rottentomatoes_link_for_movie, wikipedia_link_for_movie, person_is_relevant, genre_is_relevant, source_is_relevant, generate_header_dict, generate_links_dict, set_msg, update_rankings, check_and_get_session_info, get_type_dict
from webapp.tools.search_tools import movies_from_term, movies_from_apis_term
from webapp.models import Profiles, Sources, People, Genres, Movies, Properties, Associations

site_logger = logging.getLogger('log.site')
movie_logger = logging.getLogger('log.movie')
property_logger = logging.getLogger('log.property')
associate_logger = logging.getLogger('log.associate')
source_logger = logging.getLogger('log.source')

# Display movie list and tools for admin add movie, and add movie with ids
def view_list(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		if not logged_in_profile_info['id']:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 'warning')
			return redirect('webapp.views.profile.login')
		type_dict = get_type_dict()
		if request.GET.get('add') and request.GET.get('i') and request.GET.get('r') and request.GET.get('n'):
			'''*****************************************************************************
			Add movie given imdb identifier (rotten tomatoes and netflix ids required as well) and redirect to movie page by way of association functions if success otherwise back to search with errors
			PATH: webapp.views.movie.view_list; METHOD: none; PARAMS: get - add,i,r,n; MISC: none;
			*****************************************************************************'''
			try:
				has_error = False
				error_text = None
				# Start movie from imdb id
				res_dict = movie_from_imdb_input(request.GET.get('i'))
				if res_dict.get('movie'):
					movie = res_dict.get('movie')
				else:
					has_error = True
					error_text = 'IMDb ID Validation: ' + res_dict.get('error_msg')
					raise ValidationError('')
				# Get wikipedia id if resolved
				res = wikipedia_movie_from_title(movie)
				if res.get('movie'):
					movie.WikipediaId = res.get('movie').WikipediaId
				# Set rotten tomatoes, netflix, and wikipedia id
				movie.RottenTomatoesId = request.GET.get('r')
				test = movie_from_rottentomatoes_input(movie.RottenTomatoesId)
				if test.get('movie'):
					# Use better cast list from rotten tomatoes
					res_dict['actors'] = test.get('actors')
				else:
					has_error = True
					error_text = 'Rotten Tomatoes ID Validation: ' + test.get('error_msg')
					raise ValidationError('')
				movie.NetflixId = request.GET.get('n')
				test = movie_from_netflix_input(movie.NetflixId)
				if not test.get('movie'):
					has_error = True
					error_text = 'Netflix ID Validation: ' + test.get('error_msg')
					raise ValidationError('')
				movie.full_clean()
				movie.save()
				create_properties(movie, res_dict.get('directors'), res_dict.get('writers'), res_dict.get('actors'), res_dict.get('genres'), logged_in_profile_info['username'])
				movie_logger.info(movie.UrlTitle + ' Create Success by '  + logged_in_profile_info['username'])
				# Redirect to 'add association' function and add option 'seen' if already present
				res = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
				res['Location'] += '?assoc=1&add=1'
				if request.GET.get('seen'):
					res['Location'] += '&seen=1'
				return res
			except ValidationError as e:
				urltitle = movie.UrlTitle if movie.UrlTitle else 'Unknown'
				movie_logger.info(urltitle + ' Create Failure by ' + logged_in_profile_info['username'])
				error_msg = None
				if has_error:
					error_msg = {'Error' : error_text}
				else:
					error_msg = e.message_dict
					for key in error_msg:
						error_msg[key] = str(error_msg[key][0])
				return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search'), 'success' : False, 'results' : error_msg}, RequestContext(request))
		elif logged_in_profile_info['admin'] and request.GET.get('add'):
			if request.method == 'POST':
				if request.POST.get('api_search_term'):
					'''*****************************************************************************
					Return results from imdb, netflix, rottentomatoes, and wikipedia searches as options to add movie
					PATH: webapp.views.movie.view_list; METHOD: post; PARAMS: get - add, post - api_search_term; MISC: logged_in_profile.IsAdmin;
					*****************************************************************************'''
					api_search_term = request.POST.get('api_search_term')
					res_dict = movies_from_apis_term(api_search_term, 5)
					imdb_possibilities = res_dict.get('imdb_movies')
					for movie in imdb_possibilities:
						movie.UrlTitle = imdb_link_for_movie(movie)
					netflix_possibilities = res_dict.get('netflix_movies')
					for movie in netflix_possibilities:
						movie.UrlTitle = netflix_link_for_movie(movie)
					rottentomatoes_possibilities = res_dict.get('rottentomatoes_movies')
					for movie in rottentomatoes_possibilities:
						movie.UrlTitle = rottentomatoes_link_for_movie(movie)
					wikipedia_possibilities = res_dict.get('wikipedia_movies')
					for movie in wikipedia_possibilities:
						movie.UrlTitle = wikipedia_link_for_movie(movie)
					return render_to_response('movie/add.html', {'header' : generate_header_dict(request, 'Add Movie'), 'api_search_term' : api_search_term, 'imdb_possibilities' : imdb_possibilities, 'netflix_possibilities' : netflix_possibilities, 'rottentomatoes_possibilities' : rottentomatoes_possibilities, 'wikipedia_possibilities' : wikipedia_possibilities}, RequestContext(request))
				else:
					'''*****************************************************************************
					Add movie given user input of imdb, netflix, rottentomatoes, and wikipedia urls or ids and redirect to movie page
					PATH: webapp.views.movie.view_list; METHOD: post; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
					*****************************************************************************'''
					res_dict = movie_from_inputs(request.POST.get('imdb_url'), request.POST.get('netflix_url'), request.POST.get('rottentomatoes_id'), request.POST.get('wikipedia_id'))
					if res_dict.get('success'):
						try:
							movie = res_dict.get('movie')
							movie.full_clean()
							movie.save()
							create_properties(movie, res_dict.get('directors'), res_dict.get('writers'), res_dict.get('actors'), res_dict.get('genres'), logged_in_profile_info['username'])
							movie_logger.info(movie.UrlTitle + ' Create Success by ' + logged_in_profile_info['username'])
							return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
						except ValidationError as e:
							urltitle = movie.UrlTitle if movie.UrlTitle else 'Unknown'
							movie_logger.info(urltitle + ' Create Failure by ' + logged_in_profile_info['username'])
							error_msg = e.message_dict
							for key in error_msg:
								error_msg[key] = str(error_msg[key][0])
							return render_to_response('movie/add.html', {'header' : generate_header_dict(request, 'Add Movie'), 'error_msg' : error_msg, 'movie' : movie, 'links' : generate_links_dict(movie)}, RequestContext(request))
					else:
						movie_logger.info('Movie Create Failure by ' + logged_in_profile_info['username'])
						return render_to_response('movie/add.html', {'header' : generate_header_dict(request, 'Add Movie'), 'movie' : res_dict.get('movie'), 'error_msg' : res_dict.get('error_list'), 'links' : generate_links_dict(res_dict.get('movie'))}, RequestContext(request))
			else:
				'''*****************************************************************************
				Display admin add movie page
				PATH: webapp.views.movie.view_list; METHOD: none; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				return render_to_response('movie/add.html', {'header' : generate_header_dict(request, 'Add Movie')}, RequestContext(request))
		else:
			'''*****************************************************************************
			Display movie list page
			PATH: webapp.views.movie.view_list; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			movies, paginated_movies = [], None
			movie_list = Movies.objects.all().order_by('-Year', 'Title')
			length = int(request.GET.get('length')) if request.GET.get('length') and request.GET.get('length').isdigit() else 25
			length = length if length <= 100 else 100
			paginator = Paginator(movie_list, length)
			page = request.GET.get('page')
			try:
				paginated_movies = paginator.page(page)
			except PageNotAnInteger:
				paginated_movies = paginator.page(1)
			except EmptyPage:
				paginated_movies = paginator.page(paginator.num_pages)
			# Get all associations with logged in profile to correctly display links (seen later as well)
			for movie in paginated_movies:
				try:
					association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = movie,  ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
					movies.append((movie, True))
				except Exception:
					movies.append((movie, False))
			return render_to_response('movie/view_list.html', {'header' : generate_header_dict(request, 'Movie List'), 'movies' : movies, 'page' : paginated_movies}, RequestContext(request))
	except Exception:
		movie_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Movie tools including view, rank, delete, edit, suggestion, add property, and association tools (add, remove, edit)
def view(request, urltitle):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		if not logged_in_profile_info['id']:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 'danger')
			return redirect('webapp.views.profile.login')
		movie = Movies.objects.get(UrlTitle=urltitle)
		type_dict = get_type_dict()
		# Get all properties associated with movie (actors, directors, writers, genres)
		properties = Properties.objects.filter(ConsumeableId=movie, ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE'])
		directors, writers, actors, genres = [], [], [], []
		for property in properties:
			if property.PropertyTypeId.Description == 'DIRECTOR':
				directors.append(People.objects.get(id=property.PropertyId))
			elif property.PropertyTypeId.Description == 'WRITER':
				writers.append(People.objects.get(id=property.PropertyId))
			elif property.PropertyTypeId.Description == 'ACTOR':
				actors.append(People.objects.get(id=property.PropertyId))
			elif property.PropertyTypeId.Description == 'GENRE':
				genres.append(Genres.objects.get(id=property.PropertyId))
		if request.GET.get('assoc'):
			try:
				if request.GET.get('add'):
					'''*****************************************************************************
					Create association and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - assoc,add; MISC: none;
					*****************************************************************************'''
					watched = True if request.GET.get('seen') else False
					profile = Profiles.objects.get(id=logged_in_profile_info['id'])
					association = Associations(ProfileId = profile, ConsumeableId = movie,  ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'], Consumed = watched, Accessible = False, CreatedAt = datetime.now(), UpdatedAt = datetime.now())
					association.save()
					associate_logger.info(profile.Username + ' Associated ' + movie.UrlTitle + ' Success')
					set_msg(request, 'Movie Associated!', movie.Title + ' has been added to your list of movies. Please check that the information on this page is accurate as Pref relies on user feedback to correct errors. If you notice an error, such as an actor with a similar (same) name to a different actor being shown here, click on the offending piece of information and click on the correction link to let Pref know about it. Thanks.', 'success')
				elif request.GET.get('recent'):
					'''*****************************************************************************
					Update association based on a user recently watching a movie and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - assoc,recent; MISC: none;
					*****************************************************************************'''
					association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = movie,  ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
					# First time watching the specified movie
					if not association.Consumed:
						association.Consumed = True
						association.CreatedAt = datetime.now()
					association.UpdatedAt = datetime.now()
					association.save()
					associate_logger.info(logged_in_profile_info['username'] + ' Association with ' + movie.UrlTitle + ' Update Success')
					set_msg(request, 'Association Updated!', 'Your association with ' + movie.Title + ' has successfully been updated.', 'success')
				elif request.method == 'POST' and request.GET.get('update'):
					'''*****************************************************************************
					Update association from input on movie page and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - assoc,update; MISC: none;
					*****************************************************************************'''
					rankings_changed = False
					profile = Profiles.objects.get(id=logged_in_profile_info['id'])
					association = Associations.objects.get(ProfileId = profile, ConsumeableId = movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
					# If first time user watched the movie, update both times
					if not association.Consumed and request.POST.get('watched') == 'Watched':
						association.CreatedAt = datetime.now()
						association.UpdatedAt = datetime.now()
					# Else if user is unwatching movie (should not be allowed but mistakes happen), delete saved data
					elif association.Consumed and not request.POST.get('watched') == 'Watched':
						association.CreatedAt = None
						association.UpdatedAt = None
						association.Rank = None
						association.Rating = None
						association.Review = None
						rankings_changed = True
					# Update the rest
					else:
						if request.POST.get('first_viewed') and request.POST.get('first_viewed') != (str(association.CreatedAt.month) + '/' + str(association.CreatedAt.day) + '/' + str(association.CreatedAt.year)):
							try:
								new_date_text = request.POST.get('first_viewed')
								month = int(new_date_text[0:new_date_text.find('/')])
								day = int(new_date_text[new_date_text.find('/')+1:new_date_text.find('/', new_date_text.find('/')+1)])
								year = int(new_date_text[new_date_text.find('/', new_date_text.find('/')+1)+1:])
								new_date = datetime(year, month, day)
								if(new_date < datetime.now()):
									association.CreatedAt = new_date
								else:
									association.CreatedAt = datetime.now()
							except Exception:
								pass
						if request.POST.get('last_viewed') and request.POST.get('last_viewed') != (str(association.UpdatedAt.month) + '/' + str(association.UpdatedAt.day) + '/' + str(association.UpdatedAt.year)):
							try:
								new_date_text = request.POST.get('last_viewed')
								month = int(new_date_text[0:new_date_text.find('/')])
								day = int(new_date_text[new_date_text.find('/')+1:new_date_text.find('/', new_date_text.find('/')+1)])
								year = int(new_date_text[new_date_text.find('/', new_date_text.find('/')+1)+1:])
								new_date = datetime(year, month, day)
								if(new_date < datetime.now()):
									association.UpdatedAt = new_date
								else:
									association.UpdatedAt = datetime.now()
							except Exception:
								pass
						if request.POST.get('rating_rated') and request.POST.get('rating_rated') != 'false':
							# Handle bad float coercion by ignoring the rating
							try:
								association.Rating = int(math.ceil(float(request.POST.get('rating_rated')) * int(math.ceil(100 / profile.NumberOfStars))))
							except Exception:
								pass
						association.Review = request.POST.get('review')
					# Clear source information if no longer accessible or update it with new source object
					old_source = None
					if association.SourceId:
						old_source = association.SourceId
					if association.Accessible and not request.POST.get('accessible') == 'Accessible':
						association.SourceId = None
					elif association.Accessible:
						source_text = request.POST.get('source')
						if source_text:
							try:
								existing_source = Sources.objects.get(ProfileId = profile, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'], Description = source_text)
								association.SourceId = existing_source
							except ObjectDoesNotExist:
								if request.POST.get('update_all_sources') == 'Update_All' and old_source:
									old_source.Description = source_text
									old_source.save()
									source_logger.info(old_source.Description + ' Update Success by ' + profile.Username)
								else:
									new_source = Sources(ProfileId=profile, ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE'], Description=source_text)
									new_source.save()
									source_logger.info(new_source.Description + ' Create Success by ' + profile.Username)
									association.SourceId = new_source
						elif old_source:
							association.SourceId = None
					association.Consumed = request.POST.get('watched') == 'Watched'
					association.Accessible = request.POST.get('accessible') == 'Accessible'
					try:
						association.full_clean()
						association.save()
					except ValidationError:
						pass
					# Delete old source if no longer relevant
					if old_source and ((old_source != association.SourceId and not source_is_relevant(old_source)) or (request.POST.get('update_all_sources') == 'Update_All' and association.SourceId == None)):
						if source_is_relevant(old_source):
							for source_association in Associations.objects.filter(ProfileId = profile, ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE'], SourceId = old_source):
								source_association.SourceId = None
								source_association.save()
								associate_logger.info(logged_in_profile_info['username'] + ' Association with ' + source_association.movieId.UrlTitle + ' Update Success')
						old_source.delete()
						source_logger.info(old_source.Description + ' Delete Success by ' + profile.Username)
					associate_logger.info(logged_in_profile_info['username'] + ' Association with ' + movie.UrlTitle + ' Update Success')
					# Update rankings if ranking of movie was altered in some way
					if rankings_changed:
						update_rankings(logged_in_profile_info['id'])
					set_msg(request, 'Association Updated!', 'Your association with ' + movie.Title + ' has successfully been updated.', 'success')
				elif request.GET.get('remove'):
					'''*****************************************************************************
					Delete association and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - assoc,remove; MISC: none;
					*****************************************************************************'''
					source = None
					association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
					if association.SourceId:
						source = association.SourceId
						association.SourceId = None
					association.delete()
					if source and not source_is_relevant(source):
						source.delete()
						source_logger.info(source.Description + ' Delete Success by ' + logged_in_profile_info['username'])
					associate_logger.info(logged_in_profile_info['username'] + ' Disassociated ' + movie.UrlTitle + ' Success')
					# Fill in the gap in rankings
					update_rankings(logged_in_profile_info['id'])
					set_msg(request, 'Movie Disassociated!', movie.Title + ' has been removed from your list of movies.', 'danger')
			except ObjectDoesNotExist:
				set_msg(request, 'Association Not Found!', 'You have no association with ' + movie.Title + '.', 'danger')
			except Exception:
				associate_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
				return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))
			return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
		elif request.GET.get('rank'):
			try:
				profile = Profiles.objects.get(id=logged_in_profile_info['id'])
				association = Associations.objects.get(ProfileId = profile, ConsumeableId = movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'], Consumed=True, Rank__isnull=True)
				associations = Associations.objects.filter(ProfileId=profile, ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE'], Consumed=True).exclude(Rank__isnull=True).order_by('Rank')
				if request.method == 'POST':
					'''*****************************************************************************
					Tree ranker substep consisting of providing new comparison if not done ranking or redirecting to movie page if done ranking
					PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - rank; MISC: none;
					*****************************************************************************'''
					# Check if currently ranking movie before proceeding
					if not request.session.get('currently_ranking') and not request.session.get('currently_ranking') == movie.Id:
						raise Exception('Not currently ranking movie.')
					# Min and max limits (done when max < min)
					min = int(request.POST.get('hiddenMin')) if request.POST.get('hiddenMin') and request.POST.get('hiddenMin').isdigit() else 0
					max = int(request.POST.get('hiddenMax')) if request.POST.get('hiddenMax') and request.POST.get('hiddenMax').isdigit() else -1
					mid = (min + max) / 2
					# If done
					if max < min:
						old_rank = int(request.POST.get('hiddenPickOld')) if request.POST.get('hiddenPickOld') and request.POST.get('hiddenPickOld').isdigit() else 0
						new_rank = int(request.POST.get('hiddenPickNew')) if request.POST.get('hiddenPickNew') and request.POST.get('hiddenPickNew').isdigit() else 0
						start = None
						# If picked old movie, start reranking (including new rank) at one above old movie
						if old_rank:
							start = old_rank + 1
						# If picked new movie, start reranking at new_rank (usually one less than old_rank)
						elif new_rank:
							start = new_rank
						association.Rank = start
						# Increment all ranks above new one (can't use update_rankings because of single duplicate rank)
						for assoc in associations:
							if assoc.Rank >= start:
								assoc.Rank += 1
								assoc.save()
						association.save()
						# Delete currently_ranking variable
						del request.session['currently_ranking']
						associate_logger.info(logged_in_profile_info['username'] + ' Association with ' + movie.UrlTitle + ' Rank: ' + str(association.Rank) + ' Success')
						set_msg(request, 'Movie Ranked!', movie.Title + ' is ranked number ' + str(association.Rank) + ' out of ' + str(associations.count() + 1) + '.', 'success')
						return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					# Else continue ranking by finding new comparison movie
					else:
						association.Rating = association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if association.Rating else None
						compare_movie = Movies.objects.get(id=associations[mid].ConsumeableId.id)
						compare_association = Associations.objects.get(ProfileId = profile, ConsumeableId = compare_movie,  ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
						compare_association.Rating = compare_association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if compare_association.Rating else None
						# Use in deciding to pick which movie on left or right
						rand = random.randint(0,1)

						movie1 = movie if rand == 0 else compare_movie
						movie2 = compare_movie if rand == 0 else movie
						association1 = association if rand == 0 else compare_association
						association2 = compare_association if rand == 0 else association
						min1 = min if rand == 0 else mid + 1
						max1 = mid - 1 if rand == 0 else max
						min2 = mid + 1 if rand == 0 else min
						max2 = max if rand == 0 else mid - 1

						current_progress = int(request.POST.get('hiddenCurrentProgress')) + 1 if request.POST.get('hiddenCurrentProgress') and request.POST.get('hiddenCurrentProgress').isdigit() else 1
						max_progress = int(request.POST.get('hiddenMaxProgress')) if request.POST.get('hiddenMaxProgress') and request.POST.get('hiddenMaxProgress').isdigit() else 1
						progress = int(round((float(current_progress) / float(max_progress)) * 100))
						print str(current_progress) + ' - ' + str(max_progress) + ' - ' + str(progress)

						return render_to_response('movie/t_rank.html', {'header' : generate_header_dict(request, 'Movie Ranker'), 'movie' : movie, 'movie1' : movie1, 'movie2' : movie2, 'association1' : association1, 'association2' : association2, 'min1' : min1, 'max1' : max1, 'min2' : min2, 'max2' : max2, 'current_progress' : current_progress, 'max_progress' : max_progress, 'progress' : progress}, RequestContext(request))
				else:
					'''*****************************************************************************
					Tree ranker start displaying first comparison or redirecting to movie page if first ranking
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - rank; MISC: none;
					*****************************************************************************'''
					# Set currently ranking variable
					request.session['currently_ranking'] = movie.id
					if associations.count() == 0:
						association.Rank = 1
						association.save()
						associate_logger.info(logged_in_profile_info['username'] + ' Association with ' + movie.UrlTitle + ' Rank: ' + str(association.Rank) + ' Success')
						set_msg(request, 'Movie Ranked!', movie.Title + ' is ranked number 1 out of 1.', 'success')
						return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					min = 0
					max = associations.count()-1
					mid = (min + max) / 2
					association.Rating = association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if association.Rating else None
					compare_movie = Movies.objects.get(id=associations[mid].ConsumeableId.id)
					compare_association = Associations.objects.get(ProfileId = profile, ConsumeableId = compare_movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
					compare_association.Rating = compare_association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if compare_association.Rating else None
					rand = random.randint(0,1)

					movie1 = movie if rand == 0 else compare_movie
					movie2 = compare_movie if rand == 0 else movie
					association1 = association if rand == 0 else compare_association
					association2 = compare_association if rand == 0 else association
					min1 = min if rand == 0 else mid + 1
					max1 = mid - 1 if rand == 0 else max
					min2 = mid + 1 if rand == 0 else min
					max2 = max if rand == 0 else mid - 1

					current_progress = 0
					max_progress = int(math.ceil(math.log(associations.count(), 2))) + 1
					progress = 0

					return render_to_response('movie/t_rank.html', {'header' : generate_header_dict(request, 'Movie Ranker'), 'movie' : movie, 'movie1' : movie1, 'movie2' : movie2, 'association1' : association1, 'association2' : association2, 'min1' : min1, 'max1' : max1, 'min2' : min2, 'max2' : max2, 'current_progress' : current_progress, 'max_progress' : max_progress, 'progress' : progress}, RequestContext(request))
			except Exception:
				return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
		elif request.GET.get('rerank'):
			'''*****************************************************************************
			Remove current rank if present and redirect to tree ranker regardless
			PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - rank; MISC: none;
			*****************************************************************************'''
			try:
				association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
				association.Rank = None
				association.save()
				associate_logger.info(logged_in_profile_info['username'] + ' Association with ' + movie.UrlTitle + ' Reset Rank Success')
				update_rankings(logged_in_profile_info['id'])
			except Exception:
				pass
			res = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
			res['Location'] += '?rank=1'
			return res
		elif request.GET.get('suggestion'):
			if request.method == 'POST':
				'''*****************************************************************************
				Send suggestion/comment/correction email and redirect to movie page
				PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				profile = Profiles.objects.get(id=logged_in_profile_info['id'])
				email_from = settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' MovieId: ' + str(movie.id)
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 'success')
				if email_message:
					# send email
					send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
				else:
					pass
				return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
			else:
				'''*****************************************************************************
				Display suggestion/comment/correction page
				PATH: webapp.views.movie.view urltitle; METHOD: not post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				return render_to_response('site/suggestion_form.html', {'header' : generate_header_dict(request, 'Suggestion/Comment/Correction'), 'movie' : movie}, RequestContext(request))
		elif logged_in_profile_info['admin'] and request.GET.get('edit'):
			if request.method == 'POST':
				'''*****************************************************************************
				Save changes made to movie and redirect to movie page
				PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				has_error = False
				old_urltitle = None
				validation_dict = None
				try:
					movie.Title = request.POST.get('title')
					movie.Year = request.POST.get('year')
					movie.Runtime = request.POST.get('runtime')
					movie.ImdbId = imdb_id_from_input(request.POST.get('imdb'))
					movie.RottenTomatoesId = rottentomatoes_id_from_input(request.POST.get('rottentomatoes'))
					movie.NetflixId = netflix_id_from_input(request.POST.get('netflix'))
					movie.WikipediaId = wikipedia_id_from_input(request.POST.get('wikipedia'))
					old_urltitle = movie.UrlTitle
					validation_dict = movie_from_inputs(movie.ImdbId, movie.NetflixId, movie.RottenTomatoesId, movie.WikipediaId)
					if validation_dict.get('success'):
						movie.full_clean()
						movie.save()
						movie_logger.info(movie.UrlTitle + ' Update Success by ' + logged_in_profile_info['username'])
						set_msg(request, 'Movie Updated!', movie.Title + ' has successfully been updated.', 'success')
						return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					else:
						has_error = True
						raise ValidationError('')
				except ValidationError as e:
					movie_logger.info(movie.UrlTitle + ' Update Failure by ' + logged_in_profile_info['username'])
					error_msg = {}
					if has_error:
						if validation_dict and not validation_dict.get('success'):
							for key, value in validation_dict.get('error_list').items():
								error_msg[key] = value
					else:
						error_msg = e.message_dict
						for key in error_msg:
							error_msg[key] = str(error_msg[key][0])
					return render_to_response('movie/edit.html', {'header' : generate_header_dict(request, 'Update'), 'movie' : movie, 'old_urltitle' : old_urltitle, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'links' : generate_links_dict(movie), 'error_msg' : error_msg, 'people_list' : [cgi.escape(name, True) for name in People.objects.values_list('Name', flat=True).order_by('Name')], 'genres_list' : [cgi.escape(description, True) for description in Genres.objects.values_list('Description', flat=True).order_by('Description')]}, RequestContext(request))
			else:
				'''*****************************************************************************
				Display edit page
				PATH: webapp.views.movie.view urltitle; METHOD: not post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				return render_to_response('movie/edit.html', {'header' : generate_header_dict(request, 'Update'), 'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'links' : generate_links_dict(movie), 'people_list' : [cgi.escape(name, True) for name in People.objects.values_list('Name', flat=True).order_by('Name')], 'genres_list' : [cgi.escape(description, True) for description in Genres.objects.values_list('Description', flat=True).order_by('Description')]}, RequestContext(request))
		elif logged_in_profile_info['admin'] and request.GET.get('delete'):
			'''*****************************************************************************
			Delete movie and redirect to home
			PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - delete; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			for property in properties:
				person, genre = None, None
				# Delete all property associations
				property.delete()
				# Delete actual property if no longer relevant (i.e. has another movie associated with it)
				if property.PropertyTypeId.TableName == 'PEOPLE':
					person = People.objects.get(id=property.PropertyId)
					if person_is_relevant(person):
						continue
					else:
						person.delete()
						property_logger.info(person.UrlName + ' Delete Success by ' + logged_in_profile_info['username'])
				elif property.PropertyTypeId.TableName == 'GENRES':
					genre = Genres.objects.get(id=property.PropertyId)
					if genre_is_relevant(genre):
						continue
					else:
						genre.delete()
						property_logger.info(genre.Description + ' Delete Success by ' + logged_in_profile_info['username'])
			# Delete all profile associations (Update rankings afterwards)
			for association in Associations.objects.select_related().filter(ConsumeableId=movie,ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE']):
				source = None
				if association.SourceId:
					source = association.SourceId
					association.SourceId = None
				association.delete()
				if source and not source_is_relevant(source):
					source.delete()
					source_logger.info(source.Description + ' Delete Success by ' + logged_in_profile_info['username'])
				associate_logger.info(logged_in_profile_info['username'] + ' Disassociated ' + movie.UrlTitle + ' Success')
				update_rankings(association.ProfileId)
			# Delete movie
			movie.delete()
			movie_logger.info(movie.UrlTitle + ' Delete Success by ' + logged_in_profile_info['username'])
			set_msg(request, 'Movie Deleted!', movie.Title + ' has successfully been deleted.', 'danger')
			return redirect('webapp.views.site.home')
		elif logged_in_profile_info['admin'] and request.GET.get('add') and request.method == 'POST':
			'''*****************************************************************************
			Create property association with movie and redirect to edit page
			PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			dirs, writs, acts, gens = [], [], [], []
			type = str(request.GET.get('t')) if request.GET.get('t') else None
			value = request.POST.get('add')
			if type and type ==  'DIRECTOR':
				dirs.append(value)
			elif type and type ==  'WRITER':
				writs.append(value)
			elif type and type ==  'ACTOR':
				acts.append(value)
			elif type and type ==  'GENRE':
				gens.append(value)
			create_properties(movie, dirs, writs, acts, gens, logged_in_profile_info['username'])
			set_msg(request, 'Property Added!', movie.Title + ' has successfully been updated with the new property specified.', 'success')
			properties = Properties.objects.filter(ConsumeableId=movie, ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE'])
			directors, writers, actors, genres = [], [], [], []
			for property in properties:
				if property.PropertyTypeId.Description == 'DIRECTOR':
					directors.append(People.objects.get(id=property.PropertyId))
				elif property.PropertyTypeId.Description == 'WRITER':
					writers.append(People.objects.get(id=property.PropertyId))
				elif property.PropertyTypeId.Description == 'ACTOR':
					actors.append(People.objects.get(id=property.PropertyId))
				elif property.PropertyTypeId.Description == 'GENRE':
					genres.append(Genres.objects.get(id=property.PropertyId))
			return render_to_response('movie/edit.html', {'header' : generate_header_dict(request, 'Update'), 'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'links' : generate_links_dict(movie), 'people_list' : [cgi.escape(name, True) for name in People.objects.values_list('Name', flat=True).order_by('Name')], 'genres_list' : [cgi.escape(description, True) for description in Genres.objects.values_list('Description', flat=True).order_by('Description')]}, RequestContext(request))
		else:
			'''*****************************************************************************
			Display movie page
			PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			association = None
			profile = None
			indicators = []
			sources = []
			try:
				profile = Profiles.objects.get(id=logged_in_profile_info['id'])
				association = Associations.objects.get(ProfileId = profile, ConsumeableId = movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
				# Scale rating to profile preference (i.e. from percentage rating to n stars)
				association.Rating = association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if association.Rating else None
				indicators = profile.StarIndicators.split(',')
			except Exception:
				pass
			try:
				sources = Sources.objects.filter(ProfileId = profile, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE']).values_list('Description', flat=True).order_by('Description')
			except Exception:
				pass
			return render_to_response('movie/view.html', {'header' : generate_header_dict(request, movie.Title + ' (' + str(movie.Year) + ')'), 'movie' : movie, 'profile' : profile, 'sources' : sources, 'indicators' : indicators, 'association' : association, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'links' : generate_links_dict(movie), 'availability' : get_netflix_availability_dict(movie), 'supplements' : get_rottentomatoes_supplemental_dict(movie)}, RequestContext(request))
	except ObjectDoesNotExist:
		raise Http404
	except Exception:
		movie_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display search results
def search(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		type_dict = get_type_dict()
		if request.GET.get('t'):
			'''*****************************************************************************
			Search for movie and display movie page or search results page appropriately
			PATH: webapp.views.movie.search; METHOD: none; PARAMS: get - t; MISC: none;
			*****************************************************************************'''
			term = request.GET.get('t')
			try:
				year = int(term[len(term) - 5:len(term)-1])
				title = term[:len(term) - 7]
				movie = None
				movie = Movies.objects.get(Title=title, Year=year)
				return redirect('webapp.views.movie.view', urltitle = movie.UrlTitle)
			except Exception:
				pass
			length = int(request.GET.get('length')) if request.GET.get('length') and request.GET.get('length').isdigit() else 2
			length = length if length <= 20 else 20
			res_dict = movies_from_term(term, length)
			if res_dict.get('error_list'):
				site_logger.debug('Search Failed - Text: '+term+' Errors: ' + str(res_dict.get('error_list')))
			if res_dict.get('success'):
				result_movies = res_dict.get('movies')
				movies = []
				i = 0
				while i < len(result_movies):
					movie = result_movies[i]
					found = False
					try:
						if movie.ImdbId:
							imdb_movie = Movies.objects.get(ImdbId=movie.ImdbId)
							found = True
							if (imdb_movie, False, False) not in movies and (imdb_movie, True, False) not in movies:
								try:
									association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = imdb_movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
									movies.append((imdb_movie, True, False))
								except Exception:
									movies.append((imdb_movie, False, False))
					except ObjectDoesNotExist:
						pass
					try:
						if movie.NetflixId:
							netflix_movie = Movies.objects.get(NetflixId=movie.NetflixId)
							found = True
							if (netflix_movie, False, False) not in movies and (netflix_movie, True, False) not in movies:
								try:
									association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = netflix_movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
									movies.append((netflix_movie, True, False))
								except Exception:
									movies.append((netflix_movie, False, False))
					except ObjectDoesNotExist:
						pass
					try:
						if movie.RottenTomatoesId:
							rt_movie = Movies.objects.get(RottenTomatoesId=movie.RottenTomatoesId)
							found = True
							if (rt_movie, False, False) not in movies and (rt_movie, True, False) not in movies:
								try:
									association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = rt_movie, ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
									movies.append((rt_movie, True, False))
								except Exception:
									movies.append((rt_movie, False, False))
					except ObjectDoesNotExist:
						pass
					if not found:
						if result_movies[i].ImdbId and result_movies[i].RottenTomatoesId and not result_movies[i].NetflixId:
							res = netflix_movie_from_title(result_movies[i], True)
							if res.get('id'):
								result_movies[i].NetflixId = res.get('id')
						elif result_movies[i].ImdbId and result_movies[i].NetflixId and not result_movies[i].RottenTomatoesId:
							res = rottentomatoes_movie_from_title(result_movies[i], True)
							if res.get('id'):
								result_movies[i].RottenTomatoesId = res.get('id')
						if result_movies[i].ImdbId and result_movies[i].RottenTomatoesId and result_movies[i].NetflixId:
							result_movies[i].UrlTitle = imdb_link_for_movie(result_movies[i])
							movies.append((result_movies[i], False, True))
					del result_movies[i]
				return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search Results'), 'success' : True, 'quoted_term' : term, 'term' : urllib.unquote(term), 'length' : length, 'movies' : movies}, RequestContext(request))
			else:
				return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search Results'), 'success' : False, 'term' : urllib.unquote(term), 'results' : {'Error' : 'No results found.'} }, RequestContext(request))
		else:
			'''*****************************************************************************
			Empty search page
			PATH: webapp.views.movie.search; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search Results'), 'success' : False, 'results' : {'Error' : 'No results, did not search for anything.'}}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

