#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# References. Admin logger tags.
#
# Checked: 2011/11/07
# ichar@g2.ru
#
from django import template
from django.contrib.auth.models import User
#from django.contrib.admin.models import LogEntry
from manage.models import LogEntry
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.safestring import mark_safe
from django.utils import dateformat

from settings import DATE_FORMAT, TIME_FORMAT, NO_USERS

register = template.Library()

#
# Admin Logger tags overridens ====================================================================
#

class AdminLogNode( template.Node ):
    def __init__( self, limit, varname, user ):
        self.limit, self.varname, self.user = limit, varname, user

    def __repr__( self ):
        return "<GetAdminLog Node>"

    def render( self, context ):
        if self.user is None:
            context[self.varname] = LogEntry.objects.all().select_related('content_type', 'user')[:self.limit]
            return ''

        if not self.limit:
            if self.user in context:
                id = context.get(self.user).id
                user = User.objects.get(id=id)
            else:
                user = None
            if user is not None and not user.is_superuser:
                self.limit = 25
            else:
                self.limit = 10

        user_id = self.user
        if not user_id.isdigit():
            user_id = context[self.user].id
        context[self.varname] = LogEntry.objects.filter(user__id__exact=user_id).select_related('content_type', 'user')[:self.limit]
        return ''

class DoGetUsers( template.Node ):
    def __init__( self ):
        pass

    def render( self, context ):
        logged_user = context['user'].username
        no_users = [x for x in NO_USERS]
        no_users.append(logged_user)
        users = User.objects.all()
        context['users'] = tuple([ x for x in users if x.username not in no_users ])
        return ''

def get_users_list( parser, token ):
    return DoGetUsers()
register.tag('get_users_list', get_users_list)

class DoGetApps( template.Node ):
    def __init__( self ):
        pass

    def render( self, context ):
        apps = []
        admin = None
        services = None
        for app in context['app_list']:
            #app_url, models, has_module_perms, name
            name = app['name']
            if name.lower() == 'manage':
                admin = app.copy()
            elif name.lower() == 'services':
                services = app
            else:
                apps.append(app)
        if admin and services:
            services['models'].extend(admin['models'])
        if services:
            apps.append(services)
        for app in apps:
            if not app or not app['models']:
                continue
            for model in app['models']:
                model['sname'] = force_unicode(model['name'])
                if not 'model' in model:
                    model['info'] = mark_safe('<div class="info-permissions">&nbsp;</div>')
                    continue
                m = model['model']
                o = m.objects.all()
                rows = '<span class="info-rows">%s</span> rows' % o.count()
                try:
                    x = o.order_by('-RD')[0]
                    title = '<span class="info-title">%s%s</span>, ' % (x.title[0:45], len(x.title) > 45 and '...' or '')
                    M = dateformat.format(x.RD, 'm') # 'M/m'
                    Y = dateformat.format(x.RD, 'Y')
                    D = dateformat.format(x.RD, 'd') # 'j/d'
                    T = dateformat.format(x.RD, 'H:i')
                    last_update = ', <b><span class="info-last-update">%s-%s</span></b>, %s' % (M, D, T)
                    p = model['perms']
                    media_url = '/media/img'
                    s = '<img src="%s/spacer.gif" alt="" width="16">' % media_url
                    a = p['add'] and '<img src="%s/perm_add.png" title="add permission" alt="add">' % media_url or s
                    u = p['change'] and '<img src="%s/perm_change.png" title="change permission" alt="change">' % media_url or s
                    d = p['delete'] and '<img src="%s/perm_delete.png" title="delete permission" alt="delete">' % media_url or s
                    perm = '<div class="info-permissions"><span>%s</span><span>%s</span><span>%s</span></div>' % (a, u, d)
                except:
                    title = ''
                    last_update = ''
                    perm = ''
                model['info'] = mark_safe('%s%s%s%s' % (title, rows, last_update, perm))
        context['apps'] = apps
        return ''

def get_apps_list( parser, token ):
    return DoGetApps()
register.tag('get_apps_list', get_apps_list)

class DoGetAdminLog:
    """
    Populates a template variable with the admin log for the given criteria.

    Usage::

        {% get_admin_log [limit] as [varname] for_user [context_var_containing_user_obj] %}

    Examples::

        {% get_admin_log 10 as admin_log for_user 23 %}
        {% get_admin_log 10 as admin_log for_user user %}
        {% get_admin_log 10 as admin_log %}

    Note that ``context_var_containing_user_obj`` can be a hard-coded integer
    (user ID) or the name of a template context variable containing the user
    object whose ID you want.
    """
    def __init__( self, tag_name ):
        self.tag_name = tag_name

    def __call__( self, parser, token ):
        tokens = token.contents.split()
        if len(tokens) < 4:
            raise template.TemplateSyntaxError, "'%s' statements require two arguments" % self.tag_name
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError, "First argument in '%s' must be an integer" % self.tag_name
        if tokens[2] != 'as':
            raise template.TemplateSyntaxError, "Second argument in '%s' must be 'as'" % self.tag_name
        if len(tokens) > 4:
            if tokens[4] != 'for_user':
                raise template.TemplateSyntaxError, "Fourth argument in '%s' must be 'for_user'" % self.tag_name

        limit = int(tokens[1] or 0)
        varname = tokens[3]
        user = len(tokens) > 5 and tokens[5] or None
        return AdminLogNode(limit, varname, user)

register.tag('get_admin_log', DoGetAdminLog('get_admin_log'))
