import logging, math, random, sys, urllib
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webapp.tools.id_tools import wikipedia_id_from_movie, movie_from_inputs, movie_from_imdb_input, netflix_movie_from_title, movie_from_netflix_input, rottentomatoes_movie_from_title, movie_from_rottentomatoes_input
from webapp.tools.misc_tools import create_properties, imdb_link_for_movie, rottentomatoes_link_for_movie, netflix_link_for_movie, wikipedia_link_for_movie, person_is_relevant, genre_is_relevant, generate_header_dict, set_msg, update_rankings
from webapp.tools.search_tools import movies_from_term
from webapp.models import Profiles, People, Genres, Movies, MovieProperties, ProfileMovies

site_logger = logging.getLogger('log.site')
movie_logger = logging.getLogger('log.movie')
property_logger = logging.getLogger('log.property')
associate_logger = logging.getLogger('log.associate')

# Display movie list and tools for admin add movie, and add movie with ids
def view_list(request):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.site.login')
		if request.GET.get('add') and request.GET.get('i') and request.GET.get('r') and request.GET.get('n'):
			'''*****************************************************************************
			Add movie given imdb identifier (rotten tomatoes and netflix ids required as well) and redirect to movie page by way of association functions if success otherwise back to search with errors
			PATH: webapp.views.movie.view_list; METHOD: none; PARAMS: get - add,i,r,n; MISC: none;
			*****************************************************************************'''
			res_dict = movie_from_imdb_input(request.GET.get('i'))
			if res_dict.get('movie'):
				try:
					has_error = False
					error_text = None
					movie = res_dict.get('movie')
					# Get wikipedia id if resolved
					res = wikipedia_id_from_movie(movie)
					if res.get('id'):
						movie.WikipediaId = res.get('id')
					# Set rotten tomatoes and netflix id
					movie.RottenTomatoesId = request.GET.get('r')
					test = movie_from_rottentomatoes_input(movie.RottenTomatoesId)
					if not test.get('movie'):
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
					create_properties(movie, res_dict.get('directors'), res_dict.get('writers'), res_dict.get('actors'), res_dict.get('genres'), logged_in_profile_username)
					movie_logger.info(movie.UrlTitle + ' Create Success by '  + logged_in_profile_username)
					# Redirect to 'add association' function and add option 'seen' if already present
					res = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					res['Location'] += '?assoc=1&add=1'
					if request.GET.get('seen'):
						res['Location'] += '&seen=1'
					return res
				except ValidationError as e:
					urltitle = movie.UrlTitle if movie.UrlTitle else 'Unknown'
					movie_logger.info(urltitle + ' Create Failure by ' + logged_in_profile_username)
					error_msg = None
					if has_error:
						error_msg = {'Error' : error_text}
					else:
						error_msg = e.message_dict
						for key in error_msg:
							error_msg[key] = str(error_msg[key][0])
					return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search'), 'success' : False, 'results' : error_msg}, RequestContext(request))
			else:
				movie_logger.info('Movie Create Failure by ' + logged_in_profile_username)
				res_dict['error_list'] = {'ImdbId' : res_dict['error_msg']}
				return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search'), 'success' : False, 'results' : res_dict.get('error_list')}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('add'):
			if request.method == 'POST':
				'''*****************************************************************************
				Add movie given user input of imdb, netflix, and rottentomatoes urls or ids and redirect to movie page
				PATH: webapp.views.movie.view_list; METHOD: post; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				res_dict = movie_from_inputs(request.POST.get('imdb_url'), request.POST.get('netflix_url'), request.POST.get('rottentomatoes_id'))
				if res_dict.get('success'):
					try:
						movie = res_dict.get('movie')
						movie.full_clean()
						movie.save()
						create_properties(movie, res_dict.get('directors'), res_dict.get('writers'), res_dict.get('actors'), res_dict.get('genres'), logged_in_profile_username)
						movie_logger.info(movie.UrlTitle + ' Create Success by ' + logged_in_profile_username)
						return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					except ValidationError as e:
						urltitle = movie.UrlTitle if movie.UrlTitle else 'Unknown'
						movie_logger.info(urltitle + ' Create Failure by ' + logged_in_profile_username)
						error_msg = e.message_dict
						for key in error_msg:
							error_msg[key] = str(error_msg[key][0])
						return render_to_response('movie/add.html', {'header' : generate_header_dict(request, 'Add Movie'), 'error_msg' : error_msg, 'movie' : movie, 'imdb_link' : imdb_link_for_movie(movie), 'rt_link' : rottentomatoes_link_for_movie(movie), 'netflix_link' : netflix_link_for_movie(movie), 'wikipedia_link' : wikipedia_link_for_movie(movie)}, RequestContext(request))
				else:
					movie_logger.info('Movie Create Failure by ' + logged_in_profile_username)
					return render_to_response('movie/add.html', {'header' : generate_header_dict(request, 'Add Movie'), 'movie' : res_dict.get('movie'), 'error_msg' : res_dict.get('error_list'), 'imdb_link' : imdb_link_for_movie(res_dict.get('movie')), 'rt_link' : rottentomatoes_link_for_movie(res_dict.get('movie')), 'netflix_link' : netflix_link_for_movie(res_dict.get('movie')), 'wikipedia_link' : wikipedia_link_for_movie(res_dict.get('movie'))}, RequestContext(request))
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
					association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
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
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.profile.login')
		movie = Movies.objects.get(UrlTitle=urltitle)
		# Get all properties associated with movie (actors, directors, writers, genres)
		properties = MovieProperties.objects.filter(MovieId=movie)
		directors, writers, actors, genres = [], [], [], []
		for property in properties:
			if property.Type == 0:
				directors.append(People.objects.get(id=property.PropertyId))
			elif property.Type == 1:
				writers.append(People.objects.get(id=property.PropertyId))
			elif property.Type == 2:
				actors.append(People.objects.get(id=property.PropertyId))
			elif property.Type == 3:
				genres.append(Genres.objects.get(id=property.PropertyId))
		if request.GET.get('assoc'):
			try:
				if request.GET.get('add'):
					'''*****************************************************************************
					Create association and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - assoc,add; MISC: none;
					*****************************************************************************'''
					watched = True if request.GET.get('seen') else False
					profile = Profiles.objects.get(id=logged_in_profile_id)
					profile_movie = ProfileMovies(ProfileId = profile, MovieId = movie, Watched = watched, Accessible = False, CreatedAt = datetime.now(), UpdatedAt = datetime.now())
					profile_movie.save()
					associate_logger.info(profile.Username + ' Associated ' + movie.UrlTitle + ' Success')
					set_msg(request, 'Movie Associated!', movie.Title + ' has been added to your list of movies.', 3)
				elif request.GET.get('recent'):
					'''*****************************************************************************
					Update association based on a user recently watching a movie and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - assoc,recent; MISC: none;
					*****************************************************************************'''
					association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
					# First time watching the specified movie
					if not association.Watched:
						association.Watched = True
						association.CreatedAt = datetime.now()
					association.UpdatedAt = datetime.now()
					association.save()
					associate_logger.info(logged_in_profile_username + ' Association with ' + movie.UrlTitle + ' Update Success')
					set_msg(request, 'Association Updated!', 'Your association with ' + movie.Title + ' has successfully been updated.', 3)
				elif request.method == 'POST' and request.GET.get('update'):
					'''*****************************************************************************
					Update association from input on movie page and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - assoc,update; MISC: none;
					*****************************************************************************'''
					rankings_changed = False
					association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
					# If first time user watched the movie, update both times
					if not association.Watched and request.POST.get('watched') == 'Watched':
						association.CreatedAt = datetime.now()
						association.UpdatedAt = datetime.now()
					# Else if user is unwatching movie (should not be allowed but mistakes happen), delete saved data
					elif association.Watched and not request.POST.get('watched') == 'Watched':
						association.CreatedAt = None
						association.UpdatedAt = None
						association.Rank = None
						association.Rating = None
						association.Review = None
						rankings_changed = True
					# Update the rest
					else:
						if request.POST.get('rating_rated') and request.POST.get('rating_rated') != 'false':
							# Handle bad float coercion by ignoring the rating
							try:
								profile = Profiles.objects.get(id=logged_in_profile_id)
								association.Rating = int(math.ceil(float(request.POST.get('rating_rated')) * int(math.ceil(100 / profile.NumberOfStars))))
							except Exception:
								pass
						association.Review = request.POST.get('review')
					association.Watched = request.POST.get('watched') == 'Watched'
					# Clear source information if no longer accessiblt
					if association.Accessible and not request.POST.get('accessible') == 'Accessible':
						association.Source = None
					else:
						association.Source = request.POST.get('source')
					association.Accessible = request.POST.get('accessible') == 'Accessible'
					association.save()
					associate_logger.info(logged_in_profile_username + ' Association with ' + movie.UrlTitle + ' Update Success')
					# Update rankings if ranking of movie was altered in some way
					if rankings_changed:
						update_rankings(logged_in_profile_id)
					set_msg(request, 'Association Updated!', 'Your association with ' + movie.Title + ' has successfully been updated.', 3)
				elif request.GET.get('remove'):
					'''*****************************************************************************
					Delete association and redirect to movie page
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - assoc,remove; MISC: none;
					*****************************************************************************'''
					association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
					association.delete()
					associate_logger.info(logged_in_profile_username + ' Disassociated ' + movie.UrlTitle + ' Success')
					# Fill in the gap in rankings
					update_rankings(logged_in_profile_id)
					set_msg(request, 'Movie Disassociated!', movie.Title + ' has been removed from your list of movies.', 5)
			except ObjectDoesNotExist:
				set_msg(request, 'Association Not Found!', 'You have no association with ' + movie.Title + '.', 5)
			except Exception:
				associate_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
				return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))
			return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
		elif request.GET.get('rank'):
			try:
				profile = Profiles.objects.get(id=logged_in_profile_id)
				association = ProfileMovies.objects.get(ProfileId = profile, MovieId = movie, Watched=True)
				association.Rating = association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if association.Rating else None
				associations = ProfileMovies.objects.filter(ProfileId=profile,Watched=True).exclude(Rank__isnull=True).order_by('Rank')
				if request.method == 'POST':
					'''*****************************************************************************
					Tree ranker substep consisting of providing new comparison if not done ranking or redirecting to movie page if done ranking
					PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - rank; MISC: none;
					*****************************************************************************'''
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
						associate_logger.info(logged_in_profile_username + ' Association with ' + movie.UrlTitle + ' Rank: ' + str(association.Rank) + ' Success')
						set_msg(request, 'Movie Ranked!', movie.Title + ' is ranked number ' + str(association.Rank) + ' out of ' + str(associations.count() + 1) + '.', 3)
						return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					# Else continue ranking by finding new comparison movie
					else:
						compare_movie = Movies.objects.get(id=associations[mid].MovieId.id)
						compare_association = ProfileMovies.objects.get(ProfileId = profile, MovieId = compare_movie)
						compare_association.Rating = compare_association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if compare_association.Rating else None
						# Use in deciding to pick which movie on left or right
						rand = random.randint(0,1)
						return render_to_response('movie/t_rank.html', {'header' : generate_header_dict(request, 'Movie Ranker'), 'movie' : movie, 'movie1' : movie if rand == 0 else compare_movie, 'movie2' : compare_movie if rand == 0 else movie, 'association1' : association if rand == 0 else compare_association, 'association2' : compare_association if rand == 0 else association, 'min1' : min if rand == 0 else mid + 1, 'max1' : mid - 1 if rand == 0 else max, 'min2' : mid + 1 if rand == 0 else min, 'max2' : max if rand == 0 else mid - 1}, RequestContext(request))
				else:
					'''*****************************************************************************
					Tree ranker start displaying first comparison or redirecting to movie page if first ranking
					PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - rank; MISC: none;
					*****************************************************************************'''
					if associations.count() == 0:
						association.Rank = 1
						association.save()
						associate_logger.info(logged_in_profile_username + ' Association with ' + movie.UrlTitle + ' Rank: ' + str(association.Rank) + ' Success')
						set_msg(request, 'Movie Ranked!', movie.Title + ' is ranked number 1 out of 1.', 3)
						return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					min = 0
					max = associations.count()-1
					mid = (min + max) / 2
					compare_movie = Movies.objects.get(id=associations[mid].MovieId.id)
					compare_association = ProfileMovies.objects.get(ProfileId = profile, MovieId = compare_movie)
					compare_association.Rating = compare_association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if compare_association.Rating else None
					rand = random.randint(0,1)
					return render_to_response('movie/t_rank.html', {'header' : generate_header_dict(request, 'Movie Ranker'), 'movie' : movie, 'movie1' : movie if rand == 0 else compare_movie, 'movie2' : compare_movie if rand == 0 else movie, 'association1' : association if rand == 0 else compare_association, 'association2' : compare_association if rand == 0 else association, 'min1' : min if rand == 0 else mid + 1, 'max1' : mid - 1 if rand == 0 else max, 'min2' : mid + 1 if rand == 0 else min, 'max2' : max if rand == 0 else mid - 1}, RequestContext(request))
			except Exception:
				return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
		elif request.GET.get('rerank'):
			'''*****************************************************************************
			Remove current rank if present and redirect to tree ranker regardless
			PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - rank; MISC: none;
			*****************************************************************************'''
			try:
				association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
				association.Rank = None
				association.save()
				associate_logger.info(logged_in_profile_username + ' Association with ' + movie.UrlTitle + ' Reset Rank Success')
				update_rankings(logged_in_profile_id)
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
				profile = Profiles.objects.get(id=logged_in_profile_id)
				email_from = settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' MovieId: ' + str(movie.id)
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 3)
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
		elif logged_in_profile_admin and request.GET.get('edit'):
			if request.method == 'POST':
				'''*****************************************************************************
				Save changes made to movie and redirect to movie page
				PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				try:
					movie.Title = request.POST.get('title')
					movie.Year = request.POST.get('year')
					movie.Runtime = request.POST.get('runtime')
					movie.ImdbId = request.POST.get('imdb')
					movie.RottenTomatoesId = request.POST.get('rottentomatoes')
					movie.NetflixId = request.POST.get('netflix')
					movie.full_clean()
					movie.save()
					movie_logger.info(movie.UrlTitle + ' Update Success by ' + logged_in_profile_username)
					set_msg(request, 'Movie Updated!', movie.Title + ' has successfully been updated.', 3)
					return redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
				except ValidationError as e:
					movie_logger.info(movie.UrlTitle + ' Update Failure by ' + logged_in_profile_username)
					error_msg = e.message_dict
					for key in error_msg:
						error_msg[key] = str(error_msg[key][0])
					return render_to_response('movie/edit.html', {'header' : generate_header_dict(request, 'Update'), 'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'imdb_link' : imdb_link_for_movie(movie), 'rt_link' : rottentomatoes_link_for_movie(movie), 'netflix_link' : netflix_link_for_movie(movie), 'wikipedia_link' : wikipedia_link_for_movie(movie), 'error_msg' : error_msg, 'people_list' : map(str, People.objects.values_list('Name', flat=True).order_by('Name')), 'genres_list' : map(str, Genres.objects.values_list('Description', flat=True).order_by('Description'))}, RequestContext(request))
			elif logged_in_profile_admin and request.GET.get('delete'):
				'''*****************************************************************************
				Delete movie and redirect to home
				PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: get - delete; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				for property in properties:
					person, genre = None, None
					# Delete all property associations
					property.delete()
					# Delete actual property if no longer relevant (i.e. has another movie associated with it)
					if property.Type == 0 or property.Type == 1 or property.Type == 2:
						person = People.objects.get(id=property.PropertyId)
						if person_is_relevant(person):
							continue
						else:
							person.delete()
							property_logger.info(person.UrlName + ' Delete Success by ' + logged_in_profile_username)
					elif property.Type == 3:
						genre = Genres.objects.get(id=property.PropertyId)
						if genre_is_relevant(genre):
							continue
						else:
							genre.delete()
							property_logger.info(genre.Description + ' Delete Success by ' + logged_in_profile_username)
				# Delete all profile associations (Update rankings afterwards)
				for association in ProfileMovies.objects.select_related().filter(MovieId=movie):
					association.delete()
					associate_logger.info(logged_in_profile_username + ' Disassociated ' + movie.UrlTitle + ' Success')
					update_rankings(association.ProfileId)
				# Delete movie
				movie.delete()
				movie_logger.info(movie.UrlTitle + ' Delete Success by ' + logged_in_profile_username)
				set_msg(request, 'Movie Deleted!', movie.Title + ' has successfully been deleted.', 5)
				return redirect('webapp.views.site.home')
			else:
				'''*****************************************************************************
				Display edit page
				PATH: webapp.views.movie.view urltitle; METHOD: not post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				return render_to_response('movie/edit.html', {'header' : generate_header_dict(request, 'Update'), 'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'imdb_link' : imdb_link_for_movie(movie), 'rt_link' : rottentomatoes_link_for_movie(movie), 'netflix_link' : netflix_link_for_movie(movie), 'wikipedia_link' : wikipedia_link_for_movie(movie), 'people_list' : map(str, People.objects.values_list('Name', flat=True).order_by('Name')), 'genres_list' : map(str, Genres.objects.values_list('Description', flat=True).order_by('Description'))}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('add') and request.method == 'POST':
			'''*****************************************************************************
			Create property association with movie and redirect to edit page
			PATH: webapp.views.movie.view urltitle; METHOD: post; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			dirs, writs, acts, gens = [], [], [], []
			type = int(request.GET.get('t')) if request.GET.get('t') and request.GET.get('t').isdigit() else -1
			value = request.POST.get('add')
			if type ==  0:
				dirs.append(value)
			elif type == 1:
				writs.append(value)
			elif type == 2:
				acts.append(value)
			elif type == 3:
				gens.append(value)
			create_properties(movie, dirs, writs, acts, gens, logged_in_profile_username)
			set_msg(request, 'Property Added!', movie.Title + ' has successfully been updated with the new property specified.', 3)
			properties = MovieProperties.objects.filter(MovieId=movie)
			directors, writers, actors, genres = [], [], [], []
			for property in properties:
				if property.Type == 0:
					directors.append(People.objects.get(id=property.PropertyId))
				elif property.Type == 1:
					writers.append(People.objects.get(id=property.PropertyId))
				elif property.Type == 2:
					actors.append(People.objects.get(id=property.PropertyId))
				elif property.Type == 3:
					genres.append(Genres.objects.get(id=property.PropertyId))
			return render_to_response('movie/edit.html', {'header' : generate_header_dict(request, 'Update'), 'movie' : movie, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'imdb_link' : imdb_link_for_movie(movie), 'rt_link' : rottentomatoes_link_for_movie(movie), 'netflix_link' : netflix_link_for_movie(movie), 'wikipedia_link' : wikipedia_link_for_movie(movie), 'people_list' : map(str, People.objects.values_list('Name', flat=True).order_by('Name')), 'genres_list' : map(str, Genres.objects.values_list('Description', flat=True).order_by('Description'))}, RequestContext(request))
		else:
			'''*****************************************************************************
			Display movie page
			PATH: webapp.views.movie.view urltitle; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			association = None
			profile = None
			indicators = []
			try:
				profile = Profiles.objects.get(id=logged_in_profile_id)
				association = ProfileMovies.objects.get(ProfileId = profile, MovieId = movie)
				# Scale rating to profile preference (i.e. from percentage rating to n stars)
				association.Rating = association.Rating / float(math.ceil(100 / profile.NumberOfStars)) if association.Rating else None
				indicators = profile.StarIndicators.split(',')
			except Exception:
				pass
			return render_to_response('movie/view.html', {'header' : generate_header_dict(request, movie.Title + ' (' + str(movie.Year) + ')'), 'movie' : movie, 'profile' : profile, 'indicators' : indicators, 'association' : association, 'directors' : directors, 'writers' : writers, 'actors' : actors, 'genres' : genres, 'imdb_link' : imdb_link_for_movie(movie), 'rt_link' : rottentomatoes_link_for_movie(movie), 'netflix_link' : netflix_link_for_movie(movie), 'wikipedia_link' : wikipedia_link_for_movie(movie)}, RequestContext(request))
	except ObjectDoesNotExist:
		raise Http404
	except Exception:
		movie_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display search results
def search(request):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.movie.login')
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
			if res_dict.get('success'):
				new_movies = res_dict.get('movies')
				old_movies = []
				links = []
				i = 0
				while i < len(new_movies):
					movie = new_movies[i]
					found = False
					try:
						if movie.ImdbId:
							imdb_movie = Movies.objects.get(ImdbId=movie.ImdbId)
							found = True
							if (imdb_movie, False) not in old_movies and (imdb_movie, True) not in old_movies:
								try:
									association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = imdb_movie)
									old_movies.append((imdb_movie, True))
								except Exception:
									old_movies.append((imdb_movie, False))
					except ObjectDoesNotExist:
						pass
					try:
						if movie.NetflixId:
							netflix_movie = Movies.objects.get(NetflixId=movie.NetflixId)
							found = True
							if (netflix_movie, False) not in old_movies and (netflix_movie, True) not in old_movies:
								try:
									association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = netflix_movie)
									old_movies.append((netflix_movie, True))
								except Exception:
									old_movies.append((netflix_movie, False))
					except ObjectDoesNotExist:
						pass
					try:
						if movie.RottenTomatoesId:
							rt_movie = Movies.objects.get(RottenTomatoesId=movie.RottenTomatoesId)
							found = True
							if (rt_movie, False) not in old_movies and (rt_movie, True) not in old_movies:
								try:
									association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = rt_movie)
									old_movies.append((rt_movie, True))
								except Exception:
									old_movies.append((rt_movie, False))
					except ObjectDoesNotExist:
						pass
					if found:
						del new_movies[i]
					else:
						i += 1
				i = 0
				while i < len(new_movies):
					if new_movies[i].ImdbId and new_movies[i].RottenTomatoesId and not new_movies[i].NetflixId:
						res = netflix_movie_from_title(new_movies[i], True)
						if res.get('id'):
							new_movies[i].NetflixId = res.get('id')
					elif new_movies[i].ImdbId and new_movies[i].NetflixId and not new_movies[i].RottenTomatoesId:
						res = rottentomatoes_movie_from_title(new_movies[i], True)
						if res.get('id'):
							new_movies[i].RottenTomatoesId = res.get('id')
					if new_movies[i].ImdbId and new_movies[i].RottenTomatoesId and new_movies[i].NetflixId:
						new_movies[i].UrlTitle = imdb_link_for_movie(new_movies[i])
						i += 1
					else:
						del new_movies[i]
				return render_to_response('movie/search.html', {'header' : generate_header_dict(request, 'Search Results'), 'success' : True, 'term' : urllib.unquote(term), 'length' : length, 'new_movies' : new_movies, 'old_movies' : old_movies}, RequestContext(request))
			else:
				site_logger.debug('Search Errors: ' + str(res_dict.get('error_list')))
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

