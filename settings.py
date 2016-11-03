#######################################################################################
# MakingPlans Job Details Database. Django settings for mp project.
# -----------------------------------------------------------------
# settings.py
#
# Checked: 2016/10/20
# ichar@g2.ru
#
import os.path

DEBUG = True
TEMPLATE_DEBUG = False

IsDeepDebug = 0

basedir = os.path.abspath(os.path.dirname(__file__))
errorlog = os.path.join(basedir, 'traceback.log').replace('\\', '/')

LOCAL_FULL_TIMESTAMP = '%d-%m-%Y %H:%M:%S'

ADMINS = ()

MANAGERS = ADMINS

DATABASE_ENGINE   = 'mysql'       # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME     = 'mpbase'      # Or path to database file if using sqlite3. mp mpnew mpbase
DATABASE_USER     = ''            # Not used with sqlite3.
DATABASE_PASSWORD = ''            # Not used with sqlite3.
DATABASE_HOST     = 'localhost'   # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT     = '3306'        # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = os.path.join(os.path.dirname(__file__), 'media').replace('\\','/')

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3t58r72qsk6k-$y8q%l^yk)+#!6x8@1^uai#$7ju2oac!5f#px'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
   #'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
   #'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'references',
    'services',
    'jobs',
)

#
# Custom application settings
# ---------------------------

# Empty choice settings (Data Entry Wizard)
EMPTY_CHOICE_FIELD = (None, '', u'-1')

# Count of maximum select choices uploaded by forms
CHOICES_UPLOAD_LIMIT = 1000

# Root object name, used in Apache case
APPS_ROOT = ''

# Application's Date/Time formats
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'

# Application path
APP_PATH = os.path.dirname(__file__).replace('\..\mp','').replace('\\','/')

# Default status ID
DEFAULT_STATUS_ID = 1
EMAILED_STATUS_ID = 2

# Enable/Disable background color selecting list view
ENABLE_ITEM_BACKGROUND = False

# Filter inline max size
FILTER_INLINE_SIZE = 25

# Enable/Disable filter choices counter
FILTER_CHOICES_COUNTER = False

# List of statuses to deal with mail
MAIL_STATUS_LIST = [ (3, 'Draft Sent',), (2, 'Email Approved',) ]

# Invisible user list
NO_USERS = ['xxxxx', 'DoNotDeleteUser']

# Default query strings
DEFAULT_QUERY_STRING = { \
    'job' : '?f=0&ot=asc&o=6&status__id__exact=1'
}

# Default list per page
LIST_PER_PAGE_DEFAULT = 20

# Default Notes class
NOTES_CLASS_DEFAULT = '' #hidden
