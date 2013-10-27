import logging, sys, time, urllib2, json
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webapp.tools.id_tools import get_rottentomatoes_dict
from webapp.tools.misc_tools import generate_header_dict, set_msg, check_and_get_session_info, create_movie_property, get_type_dict
from webapp.models import Profiles, People, Properties

site_logger = logging.getLogger('log.site')

# Landing page for everyone that requires a group password or profile
def access(request):
	try:
		if request.method == 'POST':
			'''*****************************************************************************
			Create profile and redirect to home on success or back to register on failure
			PATH: webapp.views.site.access - *See urls.py
			METHOD: post - *Required to get to function
			PARAMS: none - *Required to get to function
			MISC: none - *Required to get to function
			*****************************************************************************'''
			if request.POST.get('access_password') == settings.ACCESS_PASSWORD:
				site_logger.info('Access Success')
				request.session['auth_access'] = True
				# Five minutes to create a profile or login
				request.session.set_expiry(300)
				# Message to display to user (levels: default, primary, info, success, warning, danger, inverse
				set_msg(request, 'Access Granted!', 'Welcome, you have successfully accessed the site.', 'success')
				return redirect('webapp.views.site.home')
			else:
				set_msg(request, 'Access Denied!', 'Password not correct', 'danger')
				return redirect('webapp.views.site.access')
		else:
			'''*****************************************************************************
			Display access page
			PATH: webapp.views.site.access; METHOD: not post; PARAMS: none; MISC: none;
			*****************************************************************************'''
			# Mandatory check in every function (in development/limited access mode) that checks if user is logged in (or has access for a few pages like this one)
			if settings.ENVIRONMENT == 'DEVELOPMENT':
				
				logged_in_profile_info = { }
				permission_response = check_and_get_session_info(request, logged_in_profile_info, True, False)
				if permission_response != True:
					return render_to_response('site/access.html', {'header' : generate_header_dict(request, 'Access')}, RequestContext(request))
			return redirect('webapp.views.site.home')

	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Landing page after login or profile creation
def home(request):
	try:
		if settings.ENVIRONMENT == 'DEVELOPMENT':
			logged_in_profile_info = { }
			permission_response = check_and_get_session_info(request, logged_in_profile_info, True)
			if permission_response != True:
				return permission_response
		if request.GET.get('error') and request.method == 'POST':
			'''*****************************************************************************
			Error page will submit user email here (could be delegated to an error function)
			PATH: webapp.views.site.home; METHOD: post; PARAMS: get - error; MISC: none;
			*****************************************************************************'''
			profile, email_from, email_subject = None, settings.DEFAULT_FROM_EMAIL, 'Error'
			try:
				profile = Profiles.objects.get(id=logged_in_profile_info['id'])
			except Exception:
				pass
			if profile:
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' Error'
			email_message = request.POST.get('message') if request.POST.get('message') else None
			set_msg(request, 'Thank you for your feedback!', 'We have recieved your input and will react to it appropriately.', 'success')
			if email_message:
				# send email
				send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
			else:
				pass
			return redirect('webapp.views.site.home')
		'''*****************************************************************************
		Display home page
		PATH: webapp.views.site.home; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		return render_to_response('site/home.html', {'header' : generate_header_dict(request, 'Welcome to Pref')}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Show users how to get started using the website
def discovery(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		'''*****************************************************************************
		Display discovery page
		PATH: webapp.views.site.discovery; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		return render_to_response('movie/discovery.html', {'header' : generate_header_dict(request, 'Find Movies')}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display about page and take general suggestions/comments/corrections
def about(request):
	try:
		if request.GET.get('suggestion'):
			logged_in_profile_info = { }
			permission_response = check_and_get_session_info(request, logged_in_profile_info)
			if permission_response != True:
				return permission_response
			if request.method == 'POST':
				'''*****************************************************************************
				Send suggestion/comment/correction email and redirect to home page
				PATH: webapp.views.site.about; METHOD: post; PARAMS: none; MISC: none;
				*****************************************************************************'''
				profile = Profiles.objects.get(id=logged_in_profile_info['id'])
				email_from = settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' 404'
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 'success')
				if email_message:
					# send email
					send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
				else:
					pass
				return redirect('webapp.views.site.home')
			else:
				'''*****************************************************************************
				Display about page
				PATH: webapp.views.site.about; METHOD: none; PARAMS: none; MISC: none;
				*****************************************************************************'''
				return render_to_response('site/suggestion_form.html', {'header' : generate_header_dict(request, 'Suggestion/Comment/Correction')}, RequestContext(request))
		return render_to_response('site/about.html', {'header': generate_header_dict(request, 'About')}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display disclaimers page
def disclaimers(request):
	try:
		'''*****************************************************************************
		Display disclaimers page
		PATH: webapp.views.site.disclaimers; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		return render_to_response('site/disclaimers.html', {'header': generate_header_dict(request, 'Disclaimers')}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display privacy policy page
def privacy(request):
	try:
		'''*****************************************************************************
		Display Privacy Policy page
		PATH: webapp.views.site.privacy; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		return render_to_response('site/privacy.html', {'header': generate_header_dict(request, 'Privacy Policy')}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display channel for Facebook
def channel(request):
	try:
		'''*****************************************************************************
		Display facebook channel page
		PATH: webapp.views.site.channel; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		return render_to_response('site/channel.html', {'header': generate_header_dict(request, 'Channel')}, RequestContext(request))
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Add RT ids to existing people
def rt_conversion(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		if not logged_in_profile_info['id']:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 'warning')
			return redirect('webapp.views.profile.login')
		'''*****************************************************************************
		Add RottenTomatoes IDs to current people in the database
		PATH: webapp.views.site.rt_conversion; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		cast_cache = {}
		type_dict = get_type_dict()
		for person in People.objects.filter(Q(RottenTomatoesId=None) | Q(RottenTomatoesId='')):
			acted_properties = Properties.objects.select_related().filter(ConsumeableTypeId=type_dict['CONSUMEABLE_MOVIE'], PropertyTypeId=type_dict['PROPERTY_ACTOR'], PropertyId=person.id).order_by('-ConsumeableId__Year', 'ConsumeableId__Title')
			for prop in acted_properties:
				movie = prop.ConsumeableId
				cast_list = cast_cache.get(movie.id)
				if not cast_list:
					try:	
						# Query rotten tomatoes API
						req = urllib2.Request('http://api.rottentomatoes.com/api/public/v1.0/movies/'+movie.RottenTomatoesId+'/cast.json?apikey='+settings.API_KEYS['ROTTEN_TOMATOES'])
						res = urllib2.urlopen(req)
						if res.getcode() == 200:
							# Parse json response
							rt_dict = json.loads(res.read())
						else:
							rt_dict = {'Response' : False}
					except Exception:
						rt_dict = {'Response' : False}
					time.sleep(0.1)
					if rt_dict.get('Respone') and rt_dict.get('Response') == False:
						# flag
						email_from = settings.DEFAULT_FROM_EMAIL
						email_subject = 'Failed RT Request - ACTOR: ' + person.Name + ' [' + str(person.id) + '] MOVIE: ' + movie.Title + ' [' + str(movie.id) + ']'
						email_message = 'RT dict was not retrieved for this movie at the time this actor was being examined. Please verify this property is correct.'
						# send email
						send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
						continue
					else:
						cast_cache[movie.id] = rt_dict.get('cast')
						cast_list = rt_dict.get('cast')
				if cast_list:
					found = False
					for person_dict in cast_list:
						if person_dict.get('name') == person.Name:
							found = True
							if not person.RottenTomatoesId:
								person.RottenTomatoesId = person_dict.get('id')
								person.save()
							elif person.RottenTomatoesId != person_dict.get('id'):
								try:
									cur_person = People.objects.get(RottenTomatoesId=person_dict.get('id'))
									prop.PropertyId = cur_person
									prop.save()
								except People.DoesNotExist:
									try:
										new_person = People(Name = person_dict.get('name'), RottenTomatoesId=person_dict.get('id'))
										new_person.full_clean()
										new_person.save()
										create_movie_property(movie, new_person.id, new_person.UrlName, 'ACTOR', logged_in_profile_info['username'])
										# flag to review directing and writing properties
										email_from = settings.DEFAULT_FROM_EMAIL
										email_subject = 'New Person - PERSON: ' + new_person.Name + ' [' + str(new_person.id) + ']'
										email_message = 'It was determined that a new person was needed. Please check all people with this name have the correct directing and writing credits as this was not checked.'
										# send email
										send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
									except ValidationError:
										# flag (with full info)
										email_from = settings.DEFAULT_FROM_EMAIL
										email_subject = 'Failed to Add Person - PERSON: ' + new_person.Name + ' [RT: ' + str(new_person.RottenTomatoesId) + '] MOVIE: ' + movie.Title + ' [' + str(movie.id) + ']'
										email_message = 'Validation failed when creating this person given their name and RT id. Please create manually or check if they already exist and associate this movie with them.'
										# send email
										send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
							break
					if not found:
						# flag
						email_from = settings.DEFAULT_FROM_EMAIL
						email_subject = 'Failed to find Person in RT Dict - ACTOR: ' + person.Name + ' [' + str(person.id) + '] MOVIE: ' + movie.Title + ' [' + str(movie.id) + ']'
						email_message = 'Searching the rt dict of this movie resulted in a failure to find this actor. Please verify that this is correct or correct manually. Think about what will happen in the future with this person.'
						# send email
						send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
				else:
					# flag
					email_from = settings.DEFAULT_FROM_EMAIL
					email_subject = 'Failed to get Cast List - ACTOR: ' + person.Name + ' [' + str(person.id) + '] MOVIE: ' + movie.Title + ' [' + str(movie.id) + ']'
					email_message = 'You should not be seeing this. This means that the cache and the rt request failed to find a cast for the movie specified.'
					# send email
					send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
		return HttpResponse('Success')
	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))
