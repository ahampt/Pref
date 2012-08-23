import logging, random, sys
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webapp.tools.misc_tools import logout_command, login_command, generate_header_dict, set_msg, check_and_get_session_info, get_type_dict
from webapp.models import Profiles, Sources, Movies, Associations
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

profile_logger = logging.getLogger('log.profile')
associate_logger = logging.getLogger('log.associate')
source_logger = logging.getLogger('log.source')

# User registration/Profile creation
def register(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info, True)
		if permission_response != True:
			return permission_response
		if request.method == 'POST':
			'''*****************************************************************************
			Create profile and redirect to home on success or back to register on failure
			PATH: webapp.views.profile.register; METHOD: post; PARAMS: none; MISC: none;
			*****************************************************************************'''
			# Defaults
			profile = Profiles()
			profile.FailedLoginAttempts = 0
			profile.NumberOfStars = 4
			profile.SubStars = 2
			profile.StarImage = 0
			profile.StarIndicators = 'Worst,Worser,Worse,Mild,Decent,Good,Better,Best'
			profile.Username = request.POST.get('username')
			profile.Email = request.POST.get('email')
			try:
				# Determines if error_text is to be used when complete (ValidationError still raised)
				has_error = False
				error_text = None
				if request.POST.get('password') != request.POST.get('confirm_password'):
					# Checked later to give appropriate error message (Password = '' if user left blank)
					profile.Password = None
				else:
					if request.POST.get('password'):
						password_input = request.POST.get('password')
						# Don't waste time validating rediculously sized password strings
						if len(password_input) >= 1000:
							has_error = True
							error_text = "Password must contain less than 1000 characters."
							raise ValidationError('')
						# Password validation (No unicode, one upper, one lower, one digit, >eight characters)
						text_password = password_input.encode('ascii', 'ignore')
						if len(password_input) != len(text_password):
							has_error = True
							error_text = "Password must contain only letters and digits."
							raise ValidationError('')
						hasUpper, hasLower, hasDigit = False, False, False
						if text_password:
							for char in text_password:
								if char.isalpha():
									if char.isupper():
										hasUpper = True
									elif char.islower():
										hasLower = True
									else:
										has_error = True
										error_text = "Password must contain only letters and digits."
										raise ValidationError('')
								elif char.isdigit:
									hasDigit = True
								else:
									has_error = True
									error_text = "Password must contain only letters and digits"
									raise ValidationError('')
							if not hasUpper or not hasLower or not hasDigit or not len(text_password) >= 8:
								has_error = True
								error_text = "Password must contain at least eight characters (at least: one capital letter, one lowercase letter, one digit)."
								raise ValidationError('')
						# Hash and salt (randomly generated using ALPHABET defined above) password for storage using SHA-256
						salt = ''.join(random.choice(ALPHABET) for i in range(16))
						profile.Password = make_password(text_password, salt, 'pbkdf2_sha256')
					else:
						profile.Password = ''
				# First profile is always an admin
				if Profiles.objects.all().count() == 0:
					profile.IsAdmin = True
				else:
					profile.IsAdmin = False
				profile.full_clean()
				profile.save()
				profile_logger.info(profile.Username + ' Register Success')
				# Login the new profile
				login_command(request, profile)
				profile_logger.info(profile.Username + ' Login Success')
				set_msg(request, 'Welcome ' + profile.Username + '!', 'Your profile has successfully been created.', 'success')
				return render_to_response('movie/discovery.html', {'header' : generate_header_dict(request, 'Now What?')}, RequestContext(request))
			# Failed validation (Note for all future cases like this)
			except ValidationError as e:
				# For logging, set to anonymouse if None
				username = profile.Username if profile.Username and profile.Username.encode('ascii', 'replace').isalnum() else 'Anonymous'
				profile_logger.info(username + ' Register Failure')
				error_msg = None
				# Custom error
				if has_error:
					error_msg = {'Password' : error_text}
				# Model validation error (Could be custom, look in model)
				else:
					error_msg = e.message_dict
					if profile.Password == None:
						error_msg['Password'][0] = 'The passwords do not match.'
					# Make string to make pretty on display
					for key in error_msg:
						error_msg[key] = str(error_msg[key][0])
				return render_to_response('profile/registration_form.html', {'header' : generate_header_dict(request, 'Registration'), 'profile' : profile, 'error_msg' : error_msg}, RequestContext(request))
		else:
			'''*****************************************************************************
			Display registration page
			PATH: webapp.views.profile.register; METHOD: not post; PARAMS: none; MISC: none;
			*****************************************************************************'''
			return render_to_response('profile/registration_form.html', {'header' : generate_header_dict(request, 'Registration')}, RequestContext(request))
	except Exception:
		profile_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Login user and redirect to appropriate page (access, login, home)
def login(request):
	try:
		if request.method == 'POST':
			'''*****************************************************************************
			Login to profile and redirect to home on success or back to login/access on failure
			PATH: webapp.views.profile.login; METHOD: post; PARAMS: none; MISC: none;
			*****************************************************************************'''
			profile = Profiles.objects.get(Username = request.POST.get('username'))
			# Don't waste time validating rediculously sized password strings
			text_password = request.POST.get('password')
			# Use check_password to compare hashed password correctly
			if profile.FailedLoginAttempts < settings.MAX_LOGIN_ATTEMPTS and len(text_password) < 1000 and check_password(text_password, profile.Password):
				login_command(request, profile)
				profile.FailedLoginAttempts = 0
				profile.save()
				profile_logger.info(profile.Username + ' Login Success')
				set_msg(request, 'Welcome back ' + profile.Username + '!', 'You have successfully logged in.', 'success')
				return redirect('webapp.views.site.home')
			# Redirect to login if currently logged in (as different profile) or to access otherwise
			else:
				profile_logger.info(profile.Username + ' Login Failure')
				profile.FailedLoginAttempts = profile.FailedLoginAttempts + 1 if profile.FailedLoginAttempts < settings.MAX_LOGIN_ATTEMPTS else profile.FailedLoginAttempts
				profile.save()
				logged_in_profile_info = { }
				permission_response = check_and_get_session_info(request, logged_in_profile_info, True, False)
				if permission_response != True:
					if profile.FailedLoginAttempts < settings.MAX_LOGIN_ATTEMPTS:
						set_msg(request, 'Login Failed!', 'Username or Password not correct', 'danger')
					else:
						set_msg(request, 'Login Failed!', 'Account locked out. Contact system administrator to unlock account.', 'danger')
					return permission_response
				if profile.FailedLoginAttempts < settings.MAX_LOGIN_ATTEMPTS:
					return render_to_response('profile/login.html', {'header' : generate_header_dict(request, 'Login'), 'error' : True}, RequestContext(request))
				else:
					return render_to_response('profile/login.html', {'header' : generate_header_dict(request, 'Login'), 'lockout_error' : True}, RequestContext(request))
		else:
			'''*****************************************************************************
			Display login page if logged in or have access otherwise back to access
			PATH: webapp.views.profile.login; METHOD: not post; PARAMS: none; MISC: none;
			*****************************************************************************'''
			logged_in_profile_info = { }
			permission_response = check_and_get_session_info(request, logged_in_profile_info, True)
			if permission_response != True:
				return permission_response
			return render_to_response('profile/login.html', {'header' : generate_header_dict(request, 'Login')}, RequestContext(request))
	except ObjectDoesNotExist:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info, True, False)
		if permission_response != True:
			set_msg(request, 'Login Failed!', 'Username or Password not correct', 'danger')
			return permission_response
		return render_to_response('profile/login.html', {'header' : generate_header_dict(request, 'Login'), 'error' : True}, RequestContext(request))
	except Exception:
		profile_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Logout user and redirect to home
def logout(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		'''*****************************************************************************
		Logout any logged in profile and redirect to home page (five minutes access given)
		PATH: webapp.views.profile.logout; METHOD: none; PARAMS: none; MISC: none;
		*****************************************************************************'''
		profile = logout_command(request)
		profile_logger.info(profile.Username + ' Logout Success')
		set_msg(request, 'Tata For Now ' + profile.Username + '!', 'You have successfully logged out.', 'warning')
		return redirect('webapp.views.site.home')
	except Exception:
		profile_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Display profile list and provied alternative way to registration page
def view_list(request):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		# Note genre and person don't have this option because they have to be added through a movie to be relevant
		if request.GET.get('add'):
			'''*****************************************************************************
			Display registration page
			PATH: webapp.views.profile.view_list; METHOD: none; PARAMS: get - add; MISC: none;
			*****************************************************************************'''
			return render_to_response('profile/registration_form.html', {'header' : generate_header_dict(request, 'Registration')}, RequestContext(request))
		else:
			'''*****************************************************************************
			Display profile list page
			PATH: webapp.views.profile.view_list; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			profiles = None
			profile_list = Profiles.objects.all().order_by('Username')
			# Standard pagination code that will be seen later as well, default length to 25, max of 100
			length = int(request.GET.get('length')) if request.GET.get('length') and request.GET.get('length').isdigit() else 25
			length = length if length <= 100 else 100
			paginator = Paginator(profile_list, length)
			page = request.GET.get('page')
			try:
				profiles = paginator.page(page)
			# Default to first page
			except PageNotAnInteger:
				profiles = paginator.page(1)
			# Fallback to last page
			except EmptyPage:
				profiles = paginator.page(paginator.num_pages)
			return render_to_response('profile/view_list.html', {'header' : generate_header_dict(request, 'Profile List'), 'profiles' : profiles}, RequestContext(request))
	except Exception:
		profile_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Profile tools including view, edit, delete, drag and drop rankings, view associated movies, and suggestions
def view(request, username):
	try:
		logged_in_profile_info = { }
		permission_response = check_and_get_session_info(request, logged_in_profile_info)
		if permission_response != True:
			return permission_response
		type_dict = get_type_dict()
		profile = Profiles.objects.get(Username=username)
		admin_rights = logged_in_profile_info['id'] and (logged_in_profile_info['id'] == profile.id or logged_in_profile_info['admin'])
		if logged_in_profile_info['id'] == profile.id and request.GET.get('rank'):
			if request.method == 'POST' and request.POST.get('hiddenMovieIds'):
				'''*****************************************************************************
				Save drag and drop ranks and redirect back to drag and drop page
				PATH: webapp.views.profile.view username; METHOD: post; PARAMS: get/post - rank/hiddenMovieIds; MISC: logged_in_profile_info['username'] = username;
				*****************************************************************************'''
				movies, unranked_movies = [], []
				ids_string = request.POST.get('hiddenMovieIds')
				ids = ids_string.split(',')
				# For each movie in order of ranking on page
				for i in range(len(ids)):
					# If unranked, ignore
					if ids[i][0] == "u":
						try:
							association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = ids[i][1:], ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
							unranked_movies.append(association.ConsumeableId)
						except Exception:
							continue
					# Else, update rank according to iteration number of for loop
					else:
						try:
							association = Associations.objects.get(ProfileId = logged_in_profile_info['id'], ConsumeableId = ids[i], ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'])
							if association.Rank != i+1:
								association.Rank = i+1
								association.save()
								associate_logger.info(association.ConsumeableId.UrlTitle + ' Update rank to ' + str(association.Rank) + ' Success')
							movies.append(association.ConsumeableId)
						except Exception:
							continue
				size = len(movies) + len(unranked_movies)
				set_msg(request, 'Rankings Updated!', 'Your rankings have successfully been updated.', 'success')
				return render_to_response('profile/dnd_rank.html', {'header' : generate_header_dict(request, profile.Username + '\'s Rankings'), 'profile' : profile, 'movies' : movies, 'unranked_movies' : unranked_movies, 'size' : size}, RequestContext(request))
			else:
				'''*****************************************************************************
				Display drag and drop page
				PATH: webapp.views.profile.view username; METHOD: not post; PARAMS: get - rank; MISC: logged_in_profile_info['username'] = username;
				*****************************************************************************'''
				movies, unranked_movies = [], []
				# Get all ranked and unranked (watched with no rank) titles and sort by rank followed by descending year followed by title (same for almost all lists)
				associations = Associations.objects.select_related().filter(ProfileId = logged_in_profile_info['id'], ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE'], Consumed = True).order_by('Rank', '-ConsumeableId__Year', 'ConsumeableId__Title')
				for assoc in associations:
					if assoc.Rank:
						movies.append(assoc.ConsumeableId)
					else:
						unranked_movies.append(assoc.ConsumeableId)
				size = len(movies) + len(unranked_movies)
				return render_to_response('profile/dnd_rank.html', {'header' : generate_header_dict(request, profile.Username + '\'s Rankings'), 'profile' : profile, 'movies' : movies, 'unranked_movies' : unranked_movies, 'size' : size}, RequestContext(request))
		elif request.GET.get('movies'):
			'''*****************************************************************************
			Display all movies associated with a profile
			PATH: webapp.views.profile.view username; METHOD: none; PARAMS: get - movies; MISC: none;
			*****************************************************************************'''
			movies, unranked_movies, unseen_movies = [], [], []
			associations = Associations.objects.select_related().filter(ProfileId = logged_in_profile_info['id'], ConsumeableTypeId = type_dict['CONSUMEABLE_MOVIE']).order_by('Rank', '-ConsumeableId__Year', 'ConsumeableId__Title')
			for assoc in associations:
				if assoc.Rank:
					movies.append(assoc.ConsumeableId)
				elif assoc.Consumed:
					unranked_movies.append(assoc.ConsumeableId)
				else:
					unseen_movies.append(assoc.ConsumeableId)
			return render_to_response('profile/movies.html', {'header' : generate_header_dict(request, profile.Username + '\'s Movies'), 'profile' : profile, 'movies' : movies, 'unranked_movies' : unranked_movies, 'unseen_movies' : unseen_movies}, RequestContext(request))
		elif request.GET.get('suggestion'):
			if request.method == 'POST':
				'''*****************************************************************************
				Send suggestion/comment/correction email and redirect to profile page
				PATH: webapp.views.profile.view username; METHOD: post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				email_from = settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id)
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 'success')
				if email_message:
					# send email
					send_mail(email_subject, email_message, email_from, [settings.DEFAULT_TO_EMAIL], fail_silently=False)
				else:
					pass
				return redirect('webapp.views.profile.view', username=profile.Username)
			else:
				'''*****************************************************************************
				Display suggestion/comment/correction page
				PATH: webapp.views.profile.view username; METHOD: not post; PARAMS: get - suggestion; MISC: none;
				*****************************************************************************'''
				return render_to_response('site/suggestion_form.html', {'header' : generate_header_dict(request, 'Suggestion/Comment/Correction'), 'profile' : profile}, RequestContext(request))
		elif admin_rights and request.GET.get('edit'):
			if request.method == 'POST':
				'''*****************************************************************************
				Save changes made to profile and redirect to profile page
				PATH: webapp.views.profile.view username; METHOD: post; PARAMS: get - edit; MISC: logged_in_profile_info['username'] = username OR logged_in_profile.IsAdmin;
				*****************************************************************************'''
				has_error = False
				error_text = None
				try:
					profile = Profiles.objects.get(Username=username)
					profile.Username = request.POST.get('username')
					profile.Email = request.POST.get('email')
					old_num = profile.NumberOfStars
					profile.NumberOfStars = request.POST.get('star_numbers')
					old_sub = profile.SubStars
					profile.SubStars = request.POST.get('substars')
					profile.StarImage = request.POST.get('stars')
					profile.full_clean()
					same_sub = old_sub == profile.SubStars and old_num == profile.NumberOfStars
					indicators = ""
					# Set indicators to text if no change in number of indicators otherwise set to arbitrary numbers (0.5, 1.0, ...)
					for i in range(profile.NumberOfStars):
						for j in range(profile.SubStars):
							lookup = 'indicator_' + str(i) + '_' + str(j)
							if same_sub and request.POST.get(lookup):
								indicators += request.POST.get(lookup)
							else:
								indicators += str(i + (float(j + 1) / profile.SubStars))
							indicators += ','
					profile.StarIndicators = indicators[0:-1]
					if logged_in_profile_info['admin']:
						profile.IsAdmin = request.POST.get('admin') == 'IsAdmin'
					# Validate password same as before
					if len(request.POST.get('password')) >= 1000:
						has_error = True
						error_text = "Password must contain less than 1000 characters."
						raise ValidationError('')
					if request.POST.get('password') == '':
						pass
					elif request.POST.get('password') != request.POST.get('confirm_password'):
						profile.Password = None
					else:
						if request.POST.get('password'):
							password_input = request.POST.get('password')
							if len(password_input) != len(text_password):
								has_error = True
								error_text = "Password must contain only letters and digits."
								raise ValidationError('')
							text_password = password_input.encode('ascii', 'ignore')
							hasUpper, hasLower, hasDigit = False, False, False
							if text_password:
								for char in text_password:
									if char.isalpha():
										if char.isupper():
											hasUpper = True
										elif char.islower():
											hasLower = True
										else:
											has_error = True
											error_text = "Password must contain only letters and digits."
											raise ValidationError('')
									elif char.isdigit:
										hasDigit = True
									else:
										has_error = True
										error_text = "Password must contain only letters and digits"
										raise ValidationError('')
								if not hasUpper or not hasLower or not hasDigit or not len(text_password) >= 8:
									has_error = True
									error_text = "Password must contain at least eight characters (at least: one capital letter, one lowercase letter, one digit)."
									raise ValidationError('')
							salt = ''.join(random.choice(ALPHABET) for i in range(16))
							profile.Password = make_password(text_password, salt, 'pbkdf2_sha256')
						else:
							profile.Password = ''
					profile.full_clean()
					profile.save()
					profile_logger.info(profile.Username + ' Update Success by ' + logged_in_profile_info['username'])
					set_msg(request, 'Profile Updated!', 'Your profile has successfully been updated.', 'success')
					return redirect('webapp.views.profile.view', username=profile.Username)
				except ValidationError as e:
					username = profile.Username if profile.Username and profile.Username.encode('ascii', 'replace').isalnum() else 'Anonymous'
					profile_logger.info(username + ' Register Failure')
					error_msg = None
					if has_error:
						error_msg = {'Password' : error_text}
					else:
						error_msg = e.message_dict
						if profile.Password == None:
							error_msg['Password'][0] = 'The passwords do not match.'
						for key in error_msg:
							error_msg[key] = str(error_msg[key][0])
					# Used in displaying default rating in starbox (see template)
					rate_range, index_list, lookup_list = [], [], []
					for i in range(profile.NumberOfStars):
						for j in range(profile.SubStars):
							rate_range.append(str(i + (float(j + 1) / profile.SubStars)))
					index_list = range(0, len(rate_range), 2) if profile.SubStars != 1 else range(0, len(rate_range), 1)
					i = 0
					while i < len(index_list):
						if profile.SubStars == 1:
							lookup_list.append((index_list[i], i, 0, None))
						elif profile.SubStars == 2:
							lookup_list.append((index_list[i], i, 0, 1))
						elif profile.SubStars == 4:
							lookup_list.append((index_list[i], i / 2, 0, 1))
							lookup_list.append((index_list[i+1], i / 2, 2, 3))
							i = i + 1
						i = i + 1
					return render_to_response('profile/edit.html', {'header' : generate_header_dict(request, 'Settings'), 'profile' : profile, 'indicators' : profile.StarIndicators.split(','), 'rate_range' : rate_range, 'lookup_list' : lookup_list, 'error_msg' : error_msg}, RequestContext(request))
			else:
				'''*****************************************************************************
				Display edit page
				PATH: webapp.views.profile.view username; METHOD: not post; PARAMS: get - edit; MISC: logged_in_profile_info['username'] = username OR logged_in_profile.IsAdmin;
				*****************************************************************************'''
				rate_range, index_list, lookup_list = [], [], []
				for i in range(profile.NumberOfStars):
					for j in range(profile.SubStars):
						rate_range.append(str(i + (float(j + 1) / profile.SubStars)))
				index_list = range(0, len(rate_range), 2) if profile.SubStars != 1 else range(0, len(rate_range), 1)
				i = 0
				while i < len(index_list):
					if profile.SubStars == 1:
						lookup_list.append((index_list[i], i, 0, None))
					elif profile.SubStars == 2:
						lookup_list.append((index_list[i], i, 0, 1))
					elif profile.SubStars == 4:
						lookup_list.append((index_list[i], i / 2, 0, 1))
						lookup_list.append((index_list[i+1], i / 2, 2, 3))
						i = i + 1
					i = i + 1
				return render_to_response('profile/edit.html', {'header' : generate_header_dict(request, 'Settings'), 'profile' : profile, 'indicators' : profile.StarIndicators.split(','), 'rate_range' : rate_range, 'lookup_list' : lookup_list}, RequestContext(request))
		elif admin_rights and request.GET.get('delete'):
			'''*****************************************************************************
			Delete profile and redirect to home
			PATH: webapp.views.profile.view username; METHOD: none; PARAMS: get - delete; MISC: logged_in_profile_info['username'] = username OR logged_in_profile.IsAdmin;
			*****************************************************************************'''
			if logged_in_profile_info['id'] == profile.id:
				prof = logout_command(request)
				profile_logger.info(prof.Username + ' Logout Success')
			# Delete all associations
			Associations.objects.filter(ProfileId=profile).delete()
			# Delete all sources
			Sources.objects.filter(ProfileId=profile).delete()
			profile.delete()
			profile_logger.info(profile.Username + ' Delete Success by ' + logged_in_profile_info['username'])
			set_msg(request, 'Goodbye ' + profile.Username + '!', 'Your profile has successfully been deleted.', 'danger')
			return redirect('webapp.views.site.home')
		else:
			'''*****************************************************************************
			Display profile page
			PATH: webapp.views.profile.view username; METHOD: none; PARAMS: none; MISC: none;
			*****************************************************************************'''
			indicators = profile.StarIndicators.split(',')
			return render_to_response('profile/view.html', {'header' : generate_header_dict(request, profile.Username), 'profile' : profile, 'admin_rights' : admin_rights, 'indicators' : indicators}, RequestContext(request))
	except ObjectDoesNotExist:
		raise Http404
	except Exception:
		profile_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

