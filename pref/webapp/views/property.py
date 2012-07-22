import logging, sys
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webapp.tools.misc_tools import create_properties, create_movie_property, person_is_relevant, genre_is_relevant, generate_header_dict, set_msg
from webapp.models import Profiles, People, Genres, Movies, MovieProperties, ProfileMovies

property_logger = logging.getLogger('log.property')
associate_logger = logging.getLogger('log.associate')

# Display people list
def people(request):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.profile.login')
		'''*****************************************************************************
		Display people list page
		PATH: webapp.views.propery.people; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		people = None
		people_list = People.objects.all().order_by('Name')
		length = int(request.GET.get('length')) if request.GET.get('length') and request.GET.get('length').isdigit() else 25
		length = length if length <= 100 else 100
		paginator = Paginator(people_list, length)
		page = request.GET.get('page')
		try:
			people = paginator.page(page)
		except PageNotAnInteger:
			people = paginator.page(1)
		except EmptyPage:
			people = paginator.page(paginator.num_pages)
		return render_to_response('property/view_people_list.html', {'header' : generate_header_dict(request, 'People List'), 'people' : people}, RequestContext(request))
	except Exception:
		property_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Person tools including view, delete, edit, suggestion, and movie association tools (add, remove)
def person(request, urlname):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.profile.login')
		# Get all movie associations with person and get all profile associations with said movies
		person = People.objects.get(UrlName=urlname)
		directed_properties = MovieProperties.objects.select_related().filter(Type=0, PropertyId=person.id).order_by('-MovieId__Year', 'MovieId__Title')
		written_properties = MovieProperties.objects.select_related().filter(Type=1, PropertyId=person.id).order_by('-MovieId__Year', 'MovieId__Title')
		acted_properties = MovieProperties.objects.select_related().filter(Type=2, PropertyId=person.id).order_by('-MovieId__Year', 'MovieId__Title')
		directed_movies, written_movies, acted_movies = [], [], []
		directed_movies_tuples, written_movies_tuples, acted_movies_tuples = [], [], []
		for prop in directed_properties:
			movie = prop.MovieId
			directed_movies.append(movie)
			try:
				association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
				directed_movies_tuples.append((movie, True))
			except Exception:
				directed_movies_tuples.append((movie, False))
		for prop in written_properties:
			movie = prop.MovieId
			written_movies.append(movie)
			try:
				association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
				written_movies_tuples.append((movie, True))
			except Exception:
				written_movies_tuples.append((movie, False))
		for prop in acted_properties:
			movie = prop.MovieId
			acted_movies.append(movie)
			try:
				association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
				acted_movies_tuples.append((movie, True))
			except Exception:
				acted_movies_tuples.append((movie, False))
		if request.GET.get('suggestion'):
			if request.method == 'POST':
				'''*****************************************************************************
				Send suggestion/comment/correction email and redirect to person page
				PATH: webapp.views.property.person urlname; METHOD: post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				profile = Profiles.objects.get(id=logged_in_profile_id)
				email_from = profile.Email if profile.Email else settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' PersonId: ' + str(person.id)
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 3)
				if email_message:
					# send email
					send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
				else:
					pass
				return redirect('webapp.views.property.person', urlname=person.UrlName)
			else:
				'''*****************************************************************************
				Display suggestion/comment/correction page
				PATH: webapp.views.property.person urlname; METHOD: not post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				return render_to_response('site/suggestion_form.html', {'header' : generate_header_dict(request, 'Suggestion/Comment/Correction'), 'person' : person}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('edit'):
			if request.method == 'POST':
				'''*****************************************************************************
				Save changes made to person and redirect to person page
				PATH: webapp.views.property.person urlname; METHOD: post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				person.Name = request.POST.get('name')
				try:
					person.full_clean()
					person.save()
					property_logger.info(person.UrlName + ' Update Success by ' + logged_in_profile_username)
					set_msg(request, 'Person Updated!', person.Name + ' has successfully been updated.', 3)
					return redirect('webapp.views.movie.person', urlname=person.UrlName)
				except ValidationError as e:
					property_logger.info(person.UrlName + ' Update Failure by ' + logged_in_profile_username)
					error_msg = e.message_dict
					for key in error_msg:
						error_msg[key] = str(error_msg[key][0])
					return render_to_response('property/edit_person.html', {'header' : generate_header_dict(request, 'Update'), 'person' : person, 'directed_movies' : directed_movies, 'written_movies' : written_movies, 'acted_movies' : acted_movies, 'error_msg' : error_msg}, RequestContext(request))
			else:
				'''*****************************************************************************
				Display edit page
				PATH: webapp.views.property.person urlname; METHOD: not post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				return render_to_response('property/edit_person.html', {'header' : generate_header_dict(request, 'Update'), 'person' : person, 'directed_movies' : directed_movies, 'written_movies' : written_movies, 'acted_movies' : acted_movies}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('delete'):
			'''*****************************************************************************
			Delete person and redirect to home
			PATH: webapp.views.property.person urlname; METHOD: none; PARAMS: get - delete; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			# Delete all movie associations with person
			for prop in directed_properties:
				prop.delete()
				associate_logger.info(prop.MovieId.UrlTitle + ' Disassociated ' + person.UrlName + ' Success by ' + logged_in_profile_username)
			for prop in written_properties:
				prop.delete()
				associate_logger.info(prop.MovieId.UrlTitle + ' Disassociated ' + person.UrlName + ' Success by ' + logged_in_profile_username)
			for prop in acted_properties:
				prop.delete()
				associate_logger.info(prop.MovieId.UrlTitle + ' Disassociated ' + person.UrlName + ' Success by ' + logged_in_profile_username)
			# Delete person
			person.delete()
			property_logger.info(person.UrlName + ' Delete Success by ' + logged_in_profile_username)
			set_msg(request, 'Person Deleted!', person.Name + ' has successfully been deleted.', 5)
			return redirect('webapp.views.site.home')
		elif logged_in_profile_admin and request.GET.get('add') and request.method == 'POST':
			'''*****************************************************************************
			Create movie association with person and redirect to edit page
			PATH: webapp.views.property.person urlname; METHOD: post; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			try:
				value = request.POST.get('add')
				title = value[:len(value) - 7] if value and len(value) > 7 else None
				year = int(value[len(value) - 5:len(value)-1]) if value and len(value) > 7 and value[len(value) - 5:len(value)-1].isdigit() else None
				type = int(request.GET.get('t')) if request.GET.get('t') and request.GET.get('t').isdigit() else -1
				movie = Movies.objects.get(Title=title, Year=year)
				create_movie_property(movie, person.id, person.UrlName, type, logged_in_profile_username)
				directed_properties = MovieProperties.objects.select_related().filter(Type=0, PropertyId=person.id)
				written_properties = MovieProperties.objects.select_related().filter(Type=1, PropertyId=person.id)
				acted_properties = MovieProperties.objects.select_related().filter(Type=2, PropertyId=person.id)
				directed_movies, written_movies, acted_movies = [], [], []
				for prop in directed_properties:
					directed_movies.append(prop.MovieId)
				for prop in written_properties:
					written_movies.append(prop.MovieId)
				for prop in acted_properties:
					acted_movies.append(prop.MovieId)
				set_msg(request, 'Movie Added!', movie.Title + ' has successfully been added to ' + person.Name + '\'s career.', 3)
				return render_to_response('property/edit_person.html', {'header' : generate_header_dict(request, 'Update'), 'person' : person, 'directed_movies' : directed_movies, 'written_movies' : written_movies, 'acted_movies' : acted_movies}, RequestContext(request))
			except ObjectDoesNotExist:
				property_logger.info(value + ' Added to ' + person.UrlName + ' Failure by ' + logged_in_profile_username)
				return render_to_response('property/edit_person.html', {'header' : generate_header_dict(request, 'Update'), 'person' : person, 'directed_movies' : directed_movies, 'written_movies' : written_movies, 'acted_movies' : acted_movies, 'error_msg' : {'MovieTitle' : 'Movie does not exist.'}}, RequestContext(request))
			except Exception:
				property_logger.info(value + ' Added to ' + person.UrlName + ' Failure by ' + logged_in_profile_username)
				return render_to_response('property/edit_person.html', {'header' : generate_header_dict(request, 'Update'), 'person' : person, 'directed_movies' : directed_movies, 'written_movies' : written_movies, 'acted_movies' : acted_movies, 'error_msg' : {'Movie' : 'Movie not found.'}}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('remove'):
			'''*****************************************************************************
			Remove property association with movie and redirect to home or edit page appropriately
			PATH: webapp.views.property.person urlname; METHOD: none; PARAMS: get - remove; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			re = True if request.GET.get('redirect') else False
			id = request.GET.get('i')
			type = int(request.GET.get('t')) if request.GET.get('t') and request.GET.get('t').isdigit() else -1
			movie = Movies.objects.get(UrlTitle=id)
			prop = MovieProperties.objects.get(MovieId=movie, PropertyId=person.id, Type=type)
			prop.delete()
			associate_logger.info(movie.UrlTitle + ' Disassociated ' + person.UrlName + ' Success by ' + logged_in_profile_username)
			if person_is_relevant(person):
				if re:
					set_msg(request, 'Person Removed!', person.Name + ' has successfully been removed from ' + movie.Title + '.', 4)
					response = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					response['Location'] += '?edit=1'
					return response
				else:
					set_msg(request, 'Movie Removed!', movie.Title + ' has successfully been removed from ' + person.Name + ' \'s career.', 4)
					response = redirect('webapp.views.property.person', urlname=person.UrlName)
					response['Location'] += '?edit=1'
					return response
			else:
				if re:
					person.delete()
					property_logger.info(person.Name + ' Delete Success by' + logged_in_profile_username)
					set_msg(request, 'Person Deleted!', person.Name + ' has successfully been deleted due to the removal of them from ' + movie.Title + '.', 5)
					response = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					response['Location'] += '?edit=1'
					return response
				else:
					person.delete()
					property_logger.info(person.Name + ' Delete Success by' + logged_in_profile_username)
					set_msg(request, 'Person Deleted!', person.Name + ' has successfully been deleted due to the removal of ' + movie.Title + ' from their career.', 5)
					return redirect('webapp.views.site.home')
		else:
			'''*****************************************************************************
			Display person page
			PATH: webapp.views.property.person urltitle; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			return render_to_response('property/view_person.html', {'header' : generate_header_dict(request, person.Name), 'person' : person, 'directed_movies' : directed_movies_tuples, 'written_movies' : written_movies_tuples, 'acted_movies' : acted_movies_tuples}, RequestContext(request))
	except ObjectDoesNotExist:
		raise Http404
	except Exception:
		property_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display genre list
def genres(request):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.pofile.login')
		'''*****************************************************************************
		Display genre list page
		PATH: webapp.views.property.genres; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		genres = None
		genre_list = Genres.objects.all().order_by('Description')
		length = int(request.GET.get('length')) if request.GET.get('length') and request.GET.get('length').isdigit() else 25
		length = length if length <= 100 else 100
		paginator = Paginator(genre_list, length)
		page = request.GET.get('page')
		try:
			genres = paginator.page(page)
		except PageNotAnInteger:
			genres = paginator.page(1)
		except EmptyPage:
			genres = paginator.page(paginator.num_pages)
		return render_to_response('property/view_genre_list.html', {'header' : generate_header_dict(request, 'Genre List'), 'genres' : genres}, RequestContext(request))
	except Exception:
		property_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Genre tools including view, delete, edit, suggestion, and movie association tools (add, remove)
def genre(request, description):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.profile.login')
		genre = Genres.objects.get(Description=description)
		properties = MovieProperties.objects.select_related().filter(Type=3, PropertyId=genre.id).order_by('-MovieId__Year', 'MovieId__Title')
		length = int(request.GET.get('length')) if request.GET.get('length') and request.GET.get('length').isdigit() else 25
		length = length if length <= 100 else 100
		paginator = Paginator(properties, length)
		page = request.GET.get('page')
		try:
			genre_movies = paginator.page(page)
		except PageNotAnInteger:
			genre_movies = paginator.page(1)
		except EmptyPage:
			genre_movies = paginator.page(paginator.num_pages)
		movies, movies_tuples = [], []
		for prop in genre_movies:
			movie = prop.MovieId
			movies.append(movie)
			try:
				association = ProfileMovies.objects.get(ProfileId = logged_in_profile_id, MovieId = movie)
				movies_tuples.append((movie, True))
			except Exception:
				movies_tuples.append((movie, False))
		if request.GET.get('suggestion'):
			if request.method == 'POST':
				'''*****************************************************************************
				Send suggestion/comment/correction email and redirect to genre page
				PATH: webapp.views.property.genre description; METHOD: post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				profile = Profiles.objects.get(id=logged_in_profile_id)
				email_from = profile.Email if profile.Email else settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' GenreId: ' + str(genre.id)
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 3)
				if email_message:
					# send email
					send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
				else:
					pass
				return redirect('webapp.views.property.genre', description=genre.Description)
			else:
				'''*****************************************************************************
				Display suggestion/comment/correction page
				PATH: webapp.views.property.genre description; METHOD: not post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				return render_to_response('site/suggestion_form.html', {'header' : generate_header_dict(request, 'Suggestion/Comment/Correction'), 'genre' : genre}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('edit'):
			if request.method == 'POST':
				'''*****************************************************************************
				Save changes made to genre and redirect to genre page
				PATH: webapp.views.property.genre description; METHOD: post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				genre.Description = request.POST.get('description')
				try:
					genre.full_clean()
					genre.save()
					property_logger.info(genre.Description + ' Update Success by ' + logged_in_profile_username)
					set_msg(request, 'Genre Updated!', genre.Description + ' has successfully been updated.', 3)
					return redirect('webapp.views.property.genre', description=genre.Description)
				except ValidationError as e:
					property_logger.info(genre.Description + ' Update Failure by ' + logged_in_profile_username)
					error_msg = e.message_dict
					for key in error_msg:
						error_msg[key] = str(error_msg[key][0])
					return render_to_response('property/edit_genre.html', {'header' : generate_header_dict(request, 'Update'), 'genre' : genre, 'movies' : movies, 'error_msg' : error_msg}, RequestContext(request))
			else:
				'''*****************************************************************************
				Display edit page
				PATH: webapp.views.property.genre description; METHOD: not post; PARAMS: get - edit; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				return render_to_response('property/edit_genre.html', {'header' : generate_header_dict(request, 'Update'), 'genre' : genre, 'movies' : movies}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('delete'):
			'''*****************************************************************************
			Delete genre and redirect to home
			PATH: webapp.views.property.genre description; METHOD: none; PARAMS: get - delete; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			for prop in properties:
				prop.delete()
				associate_logger.info(prop.MovieId.UrlTitle + ' Disassociated ' + genre.Description + ' Success by ' + logged_in_profile_username)
			genre.delete()
			property_logger.info(genre.Description + ' Delete Success by' + logged_in_profile_username)
			set_msg(request, 'Genre Deleted!', genre.Description + ' has successfully been deleted.', 5)
			return redirect('webapp.views.site.home')
		elif logged_in_profile_admin and request.GET.get('add') and request.method == 'POST':
			try:
				'''*****************************************************************************
				Create movie association with genre and redirect to edit page
				PATH: webapp.views.property.genre description; METHOD: post; PARAMS: get - add; MISC: logged_in_profile.IsAdmin;
				*****************************************************************************'''
				value = request.POST.get('add')
				title = value[:len(value) - 7] if value and len(value) > 7 else None
				year = int(value[len(value) - 5:len(value)-1]) if value and len(value) > 7 and value[len(value) - 5:len(value)-1].isdigit() else None
				movie = Movies.objects.get(Title=title, Year=year)
				create_movie_property(movie, genre.id, genre.Description, 3, logged_in_profile_username)
				properties = MovieProperties.objects.select_related().filter(Type=3, PropertyId=genre.id)
				movies = []
				for prop in properties:
					movies.append(prop.MovieId)
				set_msg(request, 'Movie Added!', movie.Title + ' has successfully been added to' + genre.Description + ' movies.', 4)
				return render_to_response('property/edit_genre.html', {'header' : generate_header_dict(request, 'Update'), 'genre' : genre, 'movies' : movies}, RequestContext(request))
			except ObjectDoesNotExist:
				property_logger.info(value + ' Added to ' + genre.Description + ' Failure by ' + logged_in_profile_username)
				return render_to_response('property/edit_genre.html', {'header' : generate_header_dict(request, 'Update'), 'genre' : genre, 'movies' : movies, 'error_msg' : {'MovieTitle' : 'Movie does not exist.'}}, RequestContext(request))
			except Exception:
				property_logger.info(value + ' Added to ' + genre.Description + ' Failure by ' + logged_in_profile_username)
				return render_to_response('property/edit_genre.html', {'header' : generate_header_dict(request, 'Update'), 'genre' : genre, 'movies' : movies, 'error_msg' : {'MovieTitle' : 'Year must be between 1901 and 2155 (inclusive).'}}, RequestContext(request))
		elif logged_in_profile_admin and request.GET.get('remove'):
			'''*****************************************************************************
			Remove property association with movie and redirect to home or edit page appropriately
			PATH: webapp.views.property.genre descsription; METHOD: none; PARAMS: get - remove; MISC: logged_in_profile.IsAdmin;
			*****************************************************************************'''
			re = True if request.GET.get('redirect') else False
			id = request.GET.get('i')
			movie = Movies.objects.get(UrlTitle=id)
			prop = MovieProperties.objects.get(MovieId=movie, PropertyId=genre.id, Type=3)
			prop.delete()
			associate_logger.info(movie.UrlTitle + ' Disassociated ' + genre.Description + ' Success by ' + logged_in_profile_username)
			if genre_is_relevant(genre):
				if re:
					set_msg(request, 'Genre Removed!', genre.Description + ' has successfully been removed from ' + movie.Title + '.', 4)
					response = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					response['Location'] += '?edit=1'
					return response
				else:
					set_msg(request, 'Movie Removed!', movie.Title + ' has successfully been removed from' + genre.Description + 'movies.', 4)
					response = redirect('webapp.views.property.genre', description=genre.Description)
					response['Location'] += '?edit=1'
					return resposne
			else:
				if re:
					genre.delete()
					property_logger.info(genre.Description + ' Delete Success by' + logged_in_profile_username)
					set_msg(request, 'Genre Deleted!', genre.Description + ' has successfully been deleted due to the removal of it from ' + movie.Title + '.', 5)
					response = redirect('webapp.views.movie.view', urltitle=movie.UrlTitle)
					response['Location'] += '?edit=1'
					return response
				else:
					genre.delete()
					property_logger.info(genre.Description + ' Delete Success by' + logged_in_profile_username)
					set_msg(request, 'Genre Deleted!', genre.Description + ' has successfully been deleted due to the removal of ' + movie.Title + ' from this genre.', 5)
					return redirect('webapp.views.site.home')
		else:
			return render_to_response('property/view_genre.html', {'header' : generate_header_dict(request, genre.Description), 'genre' : genre, 'movies' : movies_tuples, 'page' : genre_movies}, RequestContext(request))
	except ObjectDoesNotExist:
		raise Http404
	except Exception:
		property_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

