import logging, sys
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webapp.tools.misc_tools import generate_header_dict, set_msg
from webapp.models import Profiles

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
				set_msg(request, 'Access Granted!', 'Welcome, you have successfully accessed the site.', 3)
				return redirect('webapp.views.site.home')
			else:
				set_msg(request, 'Access Denied!', 'Password not correct', 4)
				return redirect('webapp.views.site.access')
		else:
			'''*****************************************************************************
			Display access page
			PATH: webapp.views.site.access; METHOD: not post; PARAMS: none; MISC: none;
			*****************************************************************************'''
			# Mandatory check in every function that checks if user is logged in (or has access for a few pages like this one)
			logged_in_profile_id = request.session.get('auth_profile_id')
			logged_in_profile_username = request.session.get('auth_profile_username')
			logged_in_profile_admin = request.session.get('admin')
			if not logged_in_profile_id:
				access = request.session.get('auth_access')
				if not access:
					return render_to_response('site/access.html', {'header' : generate_header_dict(request, 'Access')}, RequestContext(request))
			return redirect('webapp.views.site.home')

	except Exception:
		site_logger.error('Unexpected error: ' + str(sys.exc_info()[0]))
		return render_to_response('500.html', {'header' : generate_header_dict(request, 'Error')}, RequestContext(request))

# Landing page after login or profile creation
def home(request):
	try:
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			access = request.session.get('auth_access')
			if not access:
				set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
				return redirect('webapp.views.site.access')
		if request.GET.get('error') and request.method == 'POST':
			'''*****************************************************************************
			Error page will submit user email here (could be delegated to an error function)
			PATH: webapp.views.site.home; METHOD: post; PARAMS: get - error; MISC: none;
			*****************************************************************************'''
			profile, email_from, email_subject = None, 'Anonymous', 'Error'
			try:
				profile = Profiles.objects.get(id=logged_in_profile_id)
			except Exception:
				pass
			if profile:
				email_from = profile.Email if profile.Email else settings.DEFAULT_FROM_EMAIL
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' Error'
			email_message = request.POST.get('message') if request.POST.get('message') else None
			set_msg(request, 'Thank you for your feedback!', 'We have recieved your input and will react to it appropriately.', 3)
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
		logged_in_profile_id = request.session.get('auth_profile_id')
		logged_in_profile_username = request.session.get('auth_profile_username')
		logged_in_profile_admin = request.session.get('admin')
		if not logged_in_profile_id:
			set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
			return redirect('webapp.views.profile.login')
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
			logged_in_profile_id = request.session.get('auth_profile_id')
			logged_in_profile_username = request.session.get('auth_profile_username')
			logged_in_profile_admin = request.session.get('admin')
			if not logged_in_profile_id:
				set_msg(request, 'Action Failed!', 'You must be logged in to perform that action', 4)
				return redirect('webapp.views.profile.login')
			if request.method == 'POST':
				'''*****************************************************************************
				Send suggestion/comment/correction email and redirect to home page
				PATH: webapp.views.site.about; METHOD: post; PARAMS: none; MISC: none;
				*****************************************************************************'''
				profile = Profiles.objects.get(id=logged_in_profile_id)
				email_from = profile.Email if profile.Email else ''
				email_subject = 'Profile: ' + str(profile.Username) + ' Id: ' + str(profile.id) + ' 404'
				email_message = request.POST.get('message') if request.POST.get('message') else None
				set_msg(request, 'Thank you for your feedback!', 'We have recieved your suggestion/comment/correction and will react to it appropriately.', 3)
				if email_message:
					# send email
					pass
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


