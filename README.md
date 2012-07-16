# Pref

Rate, rank, and keep track of media consumed or desired to be consumed. This site will serve as the one stop spot for any and all things related to personalized preferences data. This project will use rottentomatoes, IMDb, Netflix, and Wikipedia API's for data gathering including more in the future.

## Access

Access password is "movies" if you want to use the site. I have it locked to prevent spammers and unwanted access for now.

## Installation

Install Pref yourself to contrubute to the site and use it for your own organizational needs. There's plenty to add and fix.

### Dependencies

1. Install [Python](http://www.python.org/) 2.7.3+.

2. Install [setuptools](http://pypi.python.org/pypi/setuptools), [MySQL-Python](http://sourceforge.net/projects/mysql-python/), [URLEncoding](http://code.daaku.org/python-urlencoding/), and [Oauth](http://code.daaku.org/python-oauth/) python modules in this order. Let me know if you need any of the packages as I think some of them have lost support.

3. Install Apache Stack for [Linux](http://www.unixmen.com/install-lamp-with-1-command-in-ubuntu-1010-maverick-meerkat/), [Windowns](http://www.wampserver.com/en/), or [Mac](http://www.mamp.info/en/index.html) if you don't have Apache and MySQL.

4. Install [Django](https://www.djangoproject.com/download/) 1.4

### Website

1. Download the project code from master or fork if you plan on possibly contributing later.

2. Create your own settings file to preserve the global file.
    * Copy settings.py where it lies and name the copy "new_settings.py" (**Make sure you use this exact filename**).

3. Inital commit.
    * Modify manage.py to import new_settings instead of settings.
    * `git commit -m 'Local settings'`

4. Configure the settings page to work with your system.
    * Get your own API keys if you wish (or leave as is) from [Rotten Tomatoes](http://developer.rottentomatoes.com/) and [Netflix](http://developer.netflix.com/) (Key and Secret). Put these keys into the appropriate place in the settings file.
    * Create DB using [phpmyadmin](http://127.0.0.1/phpmyadmin) with whatever name you want, just be sure to put the name of it here. (Set the collation to utf8_bin)
    * Set your own username and password for said database. Leave password blank ('') if no password.
    * Set the time zone correctly for you or leave alone.
    * Change the PREFIX_URL as you see fit (This means to get to the site you will have to go to http://localhost/PREFIX_URL)
    * Change LOGGING_DIR to wherever you have a folder to keep all of the log files from this project (Default is to folder in /var/log/pref). Be sure that the folder already exists or you make it beforehand.

5. cd into the project root directory (it has manage.py in it). Run the command:
     `python manage.py runserver`

6. If you have any difficulties getting setup, let me know about and I may be able to help.

7. Last commit before pull request.
    * Modify manage.py to import settings instead of new_settings (Let me know if changes are needed to settings to run your code)
    * `git commit -m 'Global settings'`