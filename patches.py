#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# AdminSite global custom overridence and Framework Patches.
#
# Checked: 2011/11/09
# ichar@g2.ru
#
import re
import datetime

from django import forms, template
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django.utils.safestring import mark_safe
from django.utils.encoding import StrAndUnicode, force_unicode, smart_unicode
from django.utils.html import escape, conditional_escape
from django.utils.text import capfirst

FORMLINES_LIST = ('table', 'div', 'box',)
EMPTY_CHOICE_FIELD = settings.EMPTY_CHOICE_FIELD
CALLBACK_REFERERS = ('jobs', 'references', 'services', '',)

IsDebug = 0

#
# Django Admin validator overridens ===============================================================
#

from django.contrib.admin import validation

def _validation_get_field( cls, model, opts, label, field ):
    if field and isinstance(field, (list, tuple)) and len(field) > 0:
        f = field[0]
    else:
        f = field
    try:
        return opts.get_field(f)
    except models.FieldDoesNotExist:
        raise ImproperlyConfigured("'%s.%s' refers to field '%s' that is missing from model '%s'."
                % (cls.__name__, label, f, model.__name__))

validation.get_field = _validation_get_field

#
# Model Choice Clean for new ForeignKeys ==========================================================
#

from django.forms.models import ModelChoiceField
from django.forms.fields import Field as Forms_Field
from django.forms.util import ValidationError

def _modelchoicefield_clean( self, value ):
    Forms_Field.clean(self, value)
    if value in EMPTY_CHOICE_FIELD:
        return None
    try:
        key = self.to_field_name or 'pk'
        value = self.queryset.get(**{key: value})
    except self.queryset.model.DoesNotExist:
        raise ValidationError(self.error_messages['invalid_choice'])
    return value

ModelChoiceField.clean = _modelchoicefield_clean

#
# Admin Datetime widget overridens ================================================================
#

from django.contrib.admin.widgets import AdminSplitDateTime

def _datetime_format_output( self, rendered_widgets ):
    return mark_safe(u'<p class="datetime">%s %s&nbsp;&nbsp;&nbsp;%s %s</p>' % \
        (_('Date:'), rendered_widgets[0], _('Time:'), rendered_widgets[1]))

def _decompress( self, value ):
    if value:
        if isinstance(value, str) and value == 'now':
            now = datetime.datetime.now()
            return [now.date(), now.time().replace(microsecond=0)]
        else:
            return [value.date(), value.time().replace(microsecond=0)]
    return [None, None]

AdminSplitDateTime.format_output = _datetime_format_output
AdminSplitDateTime.decompress = _decompress

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper

def _relatedfieldwidgetwrapper_render( self, name, value, *args, **kwargs ):
    #print "%s:%s" % (name, value)
    rel_to = self.rel.to
    related_url = '../../../%s/%s/' % ( rel_to._meta.app_label, rel_to._meta.object_name.lower() )
    self.widget.choices = self.choices
    output = [ self.widget.render(name, value, *args, **kwargs) ]
    if rel_to in self.admin_site._registry: # If the related object has an admin interface:
        # TODO: "id_" is hard-coded here. This should instead use the correct
        # API to determine the ID dynamically.
        output.append('<nobr>')
        output.append('<a href="%sadd/" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
            ( related_url, name ))
        output.append(u'<img src="%simg/admin/icon_addlink.gif" width="10" height="10" alt="%s"></a>' % \
            ( settings.ADMIN_MEDIA_PREFIX, _('Add Another') ))
        if value:
            output.append(u'<a href="%s%s/" class="related-lookup" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);"> ' % \
                ( related_url, value, name ))
            output.append(u'<img src="%simg/admin/selector-addall.gif" width="16" height="16" alt="%s"></a>' % \
                ( settings.ADMIN_MEDIA_PREFIX, _('Open Item') ))
        output.append('</nobr>')
    return mark_safe(u''.join(output))

RelatedFieldWidgetWrapper.render = _relatedfieldwidgetwrapper_render

#
# Forms Widget overridens =========================================================================
#

from django.forms.widgets import Input, RadioInput, RadioFieldRenderer
from django.forms.util import flatatt

def _input_render( self, name, value, attrs=None ):
    if value is None: value = ''
    final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
    #print '> ', self.input_type, final_attrs
    if value != '':
        # Only add the 'value' attribute if a value is non-empty.
        final_attrs['value'] = force_unicode(value)
    if final_attrs and final_attrs.has_key('disabled'):
        hidden_attrs = final_attrs.copy()
        del hidden_attrs['disabled']
        hidden_attrs['type'] = 'hidden'
        hidden_tag = u'<input%s />' % flatatt(hidden_attrs)
        del final_attrs['id']
        final_attrs['name'] = 'x_%s' % name
    else:
        hidden_tag = ''
    return mark_safe( u'<input%s />%s' % ( flatatt(final_attrs), hidden_tag ) )

Input.render = _input_render

def _radioinput_unicode( self ):
    if 'id' in self.attrs:
        label_for = ' for="%s_%s"' % ( self.attrs['id'], self.index )
    else:
        label_for = ''
    choice_label = conditional_escape(force_unicode( self.choice_label ))
    return mark_safe( u'<td>%s</td><td nowrap><label%s>%s</label></td>' % ( 
        self.tag(), label_for, choice_label ))

def _radiofieldrenderer_render( self ):
    return mark_safe( u'<table class="simple" border="0">\n%s\n</table>' % u'\n'.join(
        [ u'<tr>%s</tr>' % force_unicode(w) for w in self ]
    ))

RadioInput.__unicode__ = _radioinput_unicode
RadioFieldRenderer.render = _radiofieldrenderer_render

#
# Admin Base Model overridens =====================================================================
#

from django.contrib.admin.options import BaseModelAdmin, ModelAdmin
from django.contrib.admin import widgets

HORIZONTAL, VERTICAL = 1, 2
# returns the <ul> class for a given radio_admin field
get_ul_class = lambda x: 'radiolist%s' % ((x == HORIZONTAL) and ' inline' or '')

def _basemodeladmin_formfield_for_dbfield( self, db_field, **kwargs ):
    # Hook for specifying the form Field instance for a given database Field instance.
    # If kwargs are given, they're passed to the form Field's constructor.
    spec = { 
             'name'          : db_field.get_attname_column()[0],
             'column_type'   : db_field.db_type(),
             'internal_type' : db_field.get_internal_type(),
             'size'          : getattr(db_field, 'max_length', None),
           }

    #if IsDebug:
    #    print 'formfield_for_dbfield', spec #, kwargs

    # If the field specifies choices, we don't need to look for special
    # admin widgets - we just need to use a select widget of some kind.
    if db_field.choices:
        if db_field.name in self.radio_fields:
            # If the field is named as a radio_field, use a RadioSelect
            kwargs['widget'] = widgets.AdminRadioSelect(attrs={ 'class': get_ul_class(
                    self.radio_fields[db_field.name]), })
            kwargs['choices'] = db_field.get_choices( include_blank=db_field.blank, blank_choice=[
                    ('', _('None'))] )
            return db_field.formfield(**kwargs)
        else:
            # Otherwise, use the default select widget.
            return db_field.formfield(**kwargs)

    # For DateTimeFields, use a special field and widget.
    if isinstance(db_field, models.DateTimeField):
        kwargs['form_class'] = forms.SplitDateTimeField
        kwargs['widget'] = widgets.AdminSplitDateTime()
        return db_field.formfield(**kwargs)

    # For DateFields, add a custom CSS class.
    if isinstance(db_field, models.DateField):
        kwargs['widget'] = widgets.AdminDateWidget
        return db_field.formfield(**kwargs)

    # For TimeFields, add a custom CSS class.
    if isinstance(db_field, models.TimeField):
        kwargs['widget'] = widgets.AdminTimeWidget
        return db_field.formfield(**kwargs)
    
    # For TextFields, add a custom CSS class.
    if isinstance(db_field, models.TextField):
        attrs = { 'rows' : 5, 'cols' : 40 }
        kwargs['widget'] = widgets.AdminTextareaWidget( attrs=attrs )
        return db_field.formfield(**kwargs)
    
    # For URLFields, add a custom CSS class.
    if isinstance(db_field, models.URLField):
        kwargs['widget'] = widgets.AdminURLFieldWidget
        return db_field.formfield(**kwargs)
    
    # For IntegerFields, add a custom CSS class.
    if isinstance(db_field, models.IntegerField):
        if spec['name'] in ('id', 'looked'):
            attrs = { 
                'disabled': 'disabled',
            }
        else:
            attrs = {}
        kwargs['widget'] = widgets.AdminIntegerFieldWidget( attrs=attrs )
        return db_field.formfield(**kwargs)

    # For CommaSeparatedIntegerFields, add a custom CSS class.
    if isinstance(db_field, models.CommaSeparatedIntegerField):
        kwargs['widget'] = widgets.AdminCommaSeparatedIntegerFieldWidget
        return db_field.formfield(**kwargs)

    # For TextInputs, add a custom CSS class.
    if isinstance(db_field, models.CharField):
        if spec['name'] in ('title', 'description', 'address',) or spec['size'] > 100:
            attrs = { 
                'class': 'vLargeTextField',
            }
        else:
            attrs = { 
                'class': 'vTextField',
            }
        kwargs['widget'] = widgets.AdminTextInputWidget( attrs=attrs )
        return db_field.formfield(**kwargs)

    # For FileFields and ImageFields add a link to the current file.
    if isinstance(db_field, models.ImageField) or isinstance(db_field, models.FileField):
        kwargs['widget'] = widgets.AdminFileWidget
        return db_field.formfield(**kwargs)

    # For ForeignKey or ManyToManyFields, use a special widget.
    if isinstance(db_field, (models.ForeignKey, models.ManyToManyField)):
        if isinstance(db_field, models.ForeignKey) and db_field.name in self.raw_id_fields:
            kwargs['widget'] = widgets.ForeignKeyRawIdWidget(db_field.rel)
        elif isinstance(db_field, models.ForeignKey) and db_field.name in self.radio_fields:
            attrs = { 
                'class': get_ul_class(self.radio_fields[db_field.name]), 
            }
            kwargs['widget'] = widgets.AdminRadioSelect( attrs=attrs )
            kwargs['empty_label'] = db_field.blank and _('None') or None
        else:
            if isinstance(db_field, models.ManyToManyField):
                # If it uses an intermediary model, don't show field in admin.
                if db_field.rel.through is not None:
                    return None
                elif db_field.name in self.raw_id_fields:
                    kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.rel)
                    kwargs['help_text'] = ''
                elif db_field.name in (list(self.filter_vertical) + list(self.filter_horizontal)):
                    kwargs['widget'] = widgets.FilteredSelectMultiple(db_field.verbose_name, (
                        db_field.name in self.filter_vertical))
        # Wrap the widget's render() method with a method that adds
        # extra HTML to the end of the rendered output.
        formfield = db_field.formfield(**kwargs)
        # Don't wrap raw_id fields. Their add function is in the popup window.
        if not db_field.name in self.raw_id_fields:
            # formfield can be None if it came from a OneToOneField with
            # parent_link=True
            if formfield is not None:
                formfield.widget = widgets.RelatedFieldWidgetWrapper(formfield.widget, db_field.rel, 
                    self.admin_site)
        return formfield

    # For any other type of field, just call its formfield() method.
    return db_field.formfield(**kwargs)

BaseModelAdmin.formfield_for_dbfield = _basemodeladmin_formfield_for_dbfield

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied

def _modeladmin_changelist_view( self, request, extra_context=None ):
    # The 'change list' admin view for this model.
    # from django.contrib.admin.views.main import ChangeList, ERROR_FLAG
    from manage.main import ChangeList, ERROR_FLAG
    opts = self.model._meta
    app_label = opts.app_label
    if not self.has_change_permission(request, None):
        raise PermissionDenied
    try:
        cl = ChangeList(request, 
                        #self.model, self.list_display, self.list_display_links, self.list_filter,
                        #self.date_hierarchy, self.search_fields, self.list_select_related, 
                        #self.list_per_page, 
                        self,
                        )
    except:
        if IsDebug:
            raise
        # Wacky lookup parameters were given, so redirect to the main
        # changelist page, without parameters, and pass an 'invalid=1'
        # parameter via the query string. If wacky parameters were given and
        # the 'invalid=1' parameter was already in the query string, something
        # is screwed up with the database, so display an error page.
        if ERROR_FLAG in request.GET.keys():
            return render_to_response('admin/invalid_setup.html', {'title': _('Database error')})
        return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

    if hasattr(self, 'list_media'):
        media = mark_safe(self.list_media)
    else:
        media = ''

    if hasattr(self, 'extra_html'):
        extra_html = mark_safe(self.extra_html)
    else:
        extra_html = ''

    if hasattr(self, 'extra_submit'):
        extra_submit = mark_safe(self.extra_submit)
    else:
        extra_submit = ''

    context = {
        'title': cl.title,
        'is_popup': cl.is_popup,
        'cl': cl,
        'media': media,
        'extra_html': extra_html,
        'extra_submit': extra_submit,
        'has_add_permission': self.has_add_permission(request),
        'root_path': self.admin_site.root_path,
        'app_label': app_label,
    }
    context.update(extra_context or {})
    return render_to_response(self.change_list_template or [
        'admin/%s/%s/change_list.html' % (app_label, opts.object_name.lower()),
        'admin/%s/change_list.html' % app_label,
        'admin/change_list.html'
    ], context, context_instance=template.RequestContext(request))

ModelAdmin.changelist_view = _modeladmin_changelist_view

#
# Forms Widget overridens ================================================================================
#

from django.forms.forms import BaseForm

def _as_table( self ):
    return self._html_output(
        u'<tr><th align=left valign=top>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>', 
        u'<tr><td colspan="2">%s</td></tr>', 
        u'</td></tr>', 
        u'<br />%s', 
        False
        )

BaseForm.as_table = _as_table

#
# Admin Fieldline overridens =============================================================================
#

from django.contrib.admin.helpers import Fieldset, Fieldline

def _Fieldset_init( self, form, name=None, fields=(), classes=(), description=None, options=None ):
    self.form = form
    self.name, self.fields = name, fields
    self.classes = u' '.join(classes)
    self.description = description
    self.layouts = options and options.get('layouts', None)

def _Fieldset_iter( self ):
    i = 0
    for field in self.fields:
        layout = self.layouts and self.layouts[i] or None
        yield Fieldline( self.form, field, layout )
        i += 1

def _Fieldline_init( self, form, field, layout=None ):
    self.form = form
    if layout:
        self.layout = layout in FORMLINES_LIST and layout or layout.startswith('box:') and layout or 'default'
    else:
        self.layout = 'default'
    if isinstance(field, basestring):
        self.fields = [field]
    else:
        self.fields = field

def _line_as_default( self ):
    return self.layout == 'default' and 1 or 0

def _line_as_table( self ):
    return self.layout == 'table' and 1 or 0

def _line_as_div( self ):
    return self.layout == 'div' and 1 or 0

def _line_as_box( self ):
    return self.layout == 'box' and 1 or 0

def _line_class( self ):
    x = self.layout.split(':')
    return len(x) > 1 and x[1] or ''

Fieldset.__init__ = _Fieldset_init
Fieldset.__iter__ = _Fieldset_iter
Fieldline.__init__ = _Fieldline_init
Fieldline.line_as_default = _line_as_default
Fieldline.line_as_table = _line_as_table
Fieldline.line_as_div = _line_as_div
Fieldline.line_as_box = _line_as_box
Fieldline.line_class = _line_class

#
# Admin User overridens ==================================================================================
#

from django.contrib.auth.models import User

User._meta.ordering = ('username',)

#
# Admin LogEntry overridens ==============================================================================
#

from django.contrib.admin.models import LogEntry

def _action_time( self ):
    return str(self.action_time)

LogEntry.action_time = _action_time

#
# AdminSite ModelPage overridens =========================================================================
#

from django import http
from django.contrib.admin.sites import AdminSite
from django.views.decorators.cache import never_cache

def get_referer_callback( request ):
    # Get referer arguments for given path in session.
    # We should check either previous referer is the same with current path.
    # ----------------------------------------------------
    # print "-> PATH_INFO: %s" % request.META['PATH_INFO']
    # ----------------------------------------------------
    referer = request.META.get('HTTP_REFERER')
    if not referer:
        return
    path = request.META['PATH_INFO']
    if settings.APPS_ROOT and settings.APPS_ROOT in path:
        path = path.replace(settings.APPS_ROOT, '')
    if path in request.session:
        args = request.session[path] or ''
        del request.session[path]
        referer = request.META['HTTP_REFERER'].split('?')
        if referer[0].endswith(path):
            args = ''
    else:
        args = ''
    # --------------------------------------------------
    if IsDebug:
        print "-> get callback: %s[%s]" % ( path, args )
    # --------------------------------------------------
    return args

def set_referer_callback( request ):
    # Set referer arguments for given path in session.
    # Key of item is a referer path.
    # ----------------------------------------------------------
    # print "-> HTTP_REFERER: %s" % request.META['HTTP_REFERER']
    # print "-> HTTP_HOST: %s" % request.META['HTTP_HOST']
    # ----------------------------------------------------------
    referer = request.META.get('HTTP_REFERER')
    if not referer:
        return
    if settings.APPS_ROOT and settings.APPS_ROOT in referer:
        referer = referer.replace(settings.APPS_ROOT, '')
    host = request.META['HTTP_HOST']
    h = referer.find(host)
    a = referer.find('?')
    if a > -1:
        args = referer[a:]
        path = referer[h+len(host):len(referer)-len(args)]
    else:
        path = referer[h+len(host):]
        args = ''
    if not path:
        return
    if args:
        request.session[path] = args
        # --------------------------------------------------
        if IsDebug:
            print "-> set callback: %s[%s]" % ( path, args )
        # --------------------------------------------------
    elif path in request.session:
        del request.session[path]
        # ------------------------------------
        if IsDebug:
            print "-> del callback: %s" % path
        # ------------------------------------
"""
def _adminsite_model_page( self, request, app_label, model_name, rest_of_url=None ):
    # Handles the model-specific functionality of the admin site, delegating
    # to the appropriate ModelAdmin class.

    # Hook for callback referer.
    # We should redirect to referer with the valid early saved request arguments.
    # ------------------------------------------
    # print "-> request.path: %s" % request.path
    # print "-> app_label: [%s]" % app_label
    # print "-> model: %s" % model_name
    # ------------------------------------------
    if app_label in CALLBACK_REFERERS:
        callback = get_referer_callback(request)
        if callback:
            return http.HttpResponseRedirect(request.path + callback)
        set_referer_callback(request)
    # ===============================

    model = models.get_model(app_label, model_name)
    if model is None:
        raise http.Http404("App %r, model %r, not found." % (app_label, model_name))
    try:
        admin_obj = self._registry[model]
    except KeyError:
        raise http.Http404("This model exists but has not been registered with the admin site.")
    return admin_obj(request, rest_of_url)
_adminsite_model_page = never_cache(_adminsite_model_page)

AdminSite.model_page = _adminsite_model_page
"""

def _adminsite_root( self, request, url ):
    # Handles main URL routing for the admin app.
    # `url` is the remainder of the URL -- e.g. 'comments/comment/'.
    if request.method == 'GET' and not request.path.endswith('/'):
        return http.HttpResponseRedirect(request.path + '/')
    if settings.DEBUG:
        self.check_dependencies()

    # Figure out the admin base URL path and stash it for later use
    self.root_path = re.sub(re.escape(url) + '$', '', request.path)
    url = url.rstrip('/') # Trim trailing slash, if it exists.

    # The 'logout' view doesn't require that the person is logged in.
    if url == 'logout':
        return self.logout(request)
    # Check permission to continue or display login form.
    if not self.has_permission(request):
        return self.login(request)

    # Hook for callback referer.
    # We should redirect to referer with the valid early saved request arguments.
    args = url.split('/', 2)
    # ------------------------------------
    if IsDebug:
        print "-> url: %s" % url
        print "-> app_label: %s" % args[0]
    # ------------------------------------
    if args[0] in CALLBACK_REFERERS and not (request.GET or request.POST):
        callback = get_referer_callback(request)
        if callback:
            return http.HttpResponseRedirect(request.path + callback)
        set_referer_callback(request)
    # ===============================

    if url == '':
        return self.index(request)
    elif url == 'password_change':
        return self.password_change(request)
    elif url == 'password_change/done':
        return self.password_change_done(request)
    elif url == 'jsi18n':
        return self.i18n_javascript(request)
    # URLs starting with 'r/' are for the "View on site" links.
    elif url.startswith('r/'):
        from django.contrib.contenttypes.views import shortcut
        return shortcut(request, *url.split('/')[1:])
    elif '/' in url:
        return self.model_page(request, *args)

    return self.app_index(request, url)

def _adminsite_index( self, request, extra_context=None ):
    # Displays the main admin index page, which lists all of the installed
    # apps that have been registered in this site.
    app_dict = {}
    user = request.user

    for model, model_admin in self._registry.items():
        app_label = model._meta.app_label
        has_module_perms = user.has_module_perms(app_label)

        if has_module_perms:
            perms = {
                'add'      : model_admin.has_add_permission(request),
                'change'   : model_admin.has_change_permission(request),
                'delete'   : model_admin.has_delete_permission(request),
            }

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True not in perms.values():
                continue

            model_dict = {
                'model'    : model,
                'name'     : capfirst(model._meta.verbose_name_plural),
                'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
                'perms'    : perms,
            }
            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
                continue

            app_dict[app_label] = {
                'name'     : app_label.title(),
                'app_url'  : app_label + '/',
                'models'   : [model_dict],
            }
            app_dict[app_label]['has_module_perms'] = has_module_perms

    # Sort the apps alphabetically.
    app_list = app_dict.values()
    app_list.sort(lambda x, y: cmp(x['name'], y['name']))

    # Sort the models alphabetically within each app.
    for app in app_list:
        app['models'].sort(lambda x, y: cmp(x['name'], y['name']))

    context = {
        'title': _('Site administration'),
        'app_list' : app_list,
        'root_path': self.root_path,
    }
    context.update(extra_context or {})
    return render_to_response(self.index_template or 'admin/index.html', context,
        context_instance=template.RequestContext(request)
    )

AdminSite.root = _adminsite_root
AdminSite.index = _adminsite_index

#
# AdminSite RelatedFilterSpec overridens =================================================================
#
"""
from django.contrib.admin.filterspecs import RelatedFilterSpec

def _relatedfilterspec_init( self, f, request, params, model, model_admin ):
    super(RelatedFilterSpec, self).__init__(f, request, params, model, model_admin)
    if isinstance(f, models.ManyToManyField):
        self.lookup_title = f.rel.to._meta.verbose_name
    else:
        self.lookup_title = f.verbose_name
    self.lookup_kwarg = '%s__%s__exact' % (f.name, f.rel.to._meta.pk.name)
    self.lookup_val = request.GET.get(self.lookup_kwarg, None)
    self.lookup_emptyarg = '%s__%s__isnull' % (f.name, f.rel.to._meta.pk.name)
    self.lookup_isnull = request.GET.get(self.lookup_emptyarg, None)
    self.lookup_choices = f.get_choices(include_blank=False)

def _relatedfilterspec_choices( self, cl ):
    yield {'selected': self.lookup_val is None and not self.lookup_isnull,
           'query_string': cl.get_query_string({}, [self.lookup_kwarg, self.lookup_emptyarg]),
           'display': _('All')}
    for pk_val, val in self.lookup_choices:
        yield {'selected': self.lookup_val == smart_unicode(pk_val),
               'query_string': cl.get_query_string({self.lookup_kwarg: pk_val}, [self.lookup_emptyarg]),
               'display': '= %s' % val}
    yield {'selected': self.lookup_val is None and self.lookup_isnull,
           'query_string': cl.get_query_string({self.lookup_emptyarg: 1}, [self.lookup_kwarg]),
           'display': _('No value')}

RelatedFilterSpec.__init__ = _relatedfilterspec_init
RelatedFilterSpec.choices = _relatedfilterspec_choices
"""
#
# Django Forms overridens ================================================================================
#

from django.forms.forms import BoundField
from django.forms.widgets import TextInput

def _boundfield_as_disabled_widget( self ):
    attrs = { 'disabled':True }
    return self.as_widget(attrs=attrs)

def _boundfield_as_disabled_radio( self ):
    attrs = { 'disabled':True, 'style':'margin:3px 2px 0 2px;' }
    return self.as_widget(attrs=attrs)

def _boundfield_as_disabled_text( self ):
    attrs = { 'disabled':True }
    return self.as_text(attrs=attrs)

def _boundfield_as_disabled_short_text( self ):
    attrs = { 'disabled':True, 'style':'width:30px;text-align:center;' }
    return self.as_text(attrs=attrs)

BoundField.as_disabled_widget = _boundfield_as_disabled_widget
BoundField.as_disabled_radio = _boundfield_as_disabled_radio
BoundField.as_disabled_text = _boundfield_as_disabled_text
BoundField.as_disabled_short_text = _boundfield_as_disabled_short_text

#
# Django Field overridens ================================================================================
#

from django.db.models.fields import Field as Models_Field, BLANK_CHOICE_DASH

def _field_get_choices( self, include_blank=True, blank_choice=BLANK_CHOICE_DASH, model=None, **extra ):
    #
    #   Returns choices with a default blank choices included, 
    #   for use as SelectField choices for this field
    #
    first_choice = include_blank and blank_choice or []
    if self.choices:
        return first_choice + list(self.choices)
    #
    #   Custom choice attrs
    #
    if 'choice_attrs' in extra and extra['choice_attrs'] is not None:
        choice_attrs = extra['choice_attrs']
    else:
        choice_attrs = self.rel.limit_choices_to or {}
    if IsDebug:
        print 'choice_attrs:%s' % choice_attrs
    #
    #   Select choices from the model
    #
    rel_model = self.rel.to
    if hasattr(self.rel, 'get_related_field'):
        lst = [[getattr(x, self.rel.get_related_field().attname), smart_unicode(x)] \
                    for x in rel_model._default_manager.complex_filter(choice_attrs)]
    else:
        lst = [[x._get_pk_val(), smart_unicode(x)] for x in rel_model._default_manager.complex_filter(choice_attrs)]
    #
    #   Count choice values
    #
    if (settings.FILTER_CHOICES_COUNTER or settings.FILTER_INLINE_SIZE > len(lst) + 2) and model is not None:
        name = '%s__id__exact' % self.name
        for i, x in enumerate(lst):
            kw = { name:x[0] }
            try:
                x = model._default_manager.filter(**kw).count() or 0
            except:
                x = 0
            if not x:
                lst[i][1] += ' [<span class="choices_zero">%s</span>]' % x
            elif x > 1000:
                lst[i][1] += ' [<span class="choices_extra">%s</span>]' % x
            else:
                lst[i][1] += ' [<span class="choices_counter">%s</span>]' % x
    return first_choice + lst

Models_Field.get_choices = _field_get_choices
