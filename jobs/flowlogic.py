#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# jobs/flowlogic.py
#
# Checked: 2011/11/03
# ichar@g2.ru
#
import re
import copy
import datetime
import decimal

from django import forms
from django.db import models
from django.conf import settings
from django.db.models import Q
from django.db.models.loading import get_model
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.admin.templatetags.admin_list import _boolean_icon, DOT
from django.shortcuts import render_to_response

from django.http import HttpResponse, HttpResponseRedirect, Http404, QueryDict
from django.utils.html import escape, conditional_escape
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode, smart_str, force_unicode
from django.utils.translation import ugettext_lazy as _
from django.core.serializers import serialize
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.template import loader, RequestContext
from django.template.defaultfilters import slugify

from manage.main import ChangeList, SEARCH_VAR, ALL_VAR, EMPTY_CHANGELIST_VALUE, PAGE_VAR

from jobs.models import Branch, Job, BRANCH_CHOICES, PRICE_CHOICES
from jobs.forms import JobForm
from references.models import Status, PayStructure, MYOB, PAY_CHOICES, MYOB_CHOICES
from widgets import SelectMonthWidget, CheckboxList
from utils import has_add_permission, log_addition, log_change, construct_change_message

CLIENT_LIST_PER_PAGE = 20
JOB_LIST_PER_PAGE = 10
DATE_FIELDS = ('received', 'finished',)
BOOLEAN_FIELDS = ('IsAmendment', 'IsArchive',)

IsDebug = 0
IsDeepTrace = 0

def _get_model_instance( request, admin_site, app_label, model_name ):
    if admin_site is None:
        return None

    admin_site.root(request, '%s/%s/' % (app_label, model_name))
    model = get_model(app_label, model_name)
    model_admin = None
    cl = None

    for entry in admin_site._registry:
        if entry._meta.object_name == model._meta.object_name:
            model_admin = admin_site._registry[entry]

    if IsDebug:
        print '_get_model_instance(model_admin): %s' % repr(model_admin)

    try:
        cl = ChangeList( request, model_admin, 
                model=model,
                #list_display=list(model_admin.list_display), 
                #list_display_links=model_admin.list_display_links,
                #list_filter=model_admin.list_filter, 
                #date_hierarchy=model_admin.date_hierarchy, 
                #search_fields=model_admin.search_fields,
                list_select_related=model_admin.list_select_related, 
                list_per_page=(model_name=='branch' and CLIENT_LIST_PER_PAGE or JOB_LIST_PER_PAGE),
                ordering=(model_name=='job' and ('-RD',) or None),
                query_splitter=','
                )
        cl.formset = None
    except:
        raise

    if IsDebug:
        print '_get_model_instance(search_fields): %s' % str(model_admin.search_fields)
        print 'cl: %s' % repr(cl)
        print 'results: %s' % len(cl.result_list)

    return cl

def _get_job_instance( request ):
    pk = request.POST.get('pk')
    if pk is not None:
        ob = Job.objects.get(pk=pk)
    else:
        ob = None
    return ( pk, ob, )

def _get_form_changes( data, form, ob ):
    #
    # Returns changes list has been maden by given request
    #
    changed_data = []
    for key in form.fields.keys():
        if key in ('RD',):
            continue
        if key in DATE_FIELDS:
            new = data.get(key+'_0') + ' ' + data.get(key+'_1')
            new = new.strip()
        elif key in BOOLEAN_FIELDS:
            new = data.get(key, None)
            if new is None or new in ('', 'False', '0', 'off', 'None'):
                new = '0'
            else:
                new = '1'
        else:
            new = data.get(key, '')
        if not isinstance(new, basestring):
            new = str(new)
        old = getattr(ob, key, None)
        if isinstance(old, models.Model):
            old = str(old.id)
        if old is None:
            old = ''
        elif not isinstance(old, basestring):
            old = str(old)
        if new != old:
            changed_data.append('%s(OLD[%s] - NEW[%s])' % (key, old, new))
    return changed_data

def _set_job_form( request, data, ob ):
    #
    # Saves given form into DB
    #
    form = JobForm(data, instance=ob)
    pk = data.get('pk', None)
    IsDone = 0

    if form.is_valid():
        form._changed_data = _get_form_changes(data, form, ob)
        message = construct_change_message(form, 'Jobs FlowLogic Wizard')
        if IsDebug:
            print 'form is valid: %s' % message
        new_item = form.save()
        if not pk:
            log_addition(request, new_item, message)
        else:
            log_change(request, new_item, message)
        IsDone = 1
    else:
        if IsDebug:
            print 'form is not valid: %s' % str(form.errors)
    return ( IsDone, form, )

class JobSearchForm( forms.Form ):
    #
    # Job Flow HTML-form model
    #
    status_choices = [(x.id, mark_safe(x.title),) for x in Status.objects.all().order_by('title')]
    status_choices.insert(0, (-1, '--- Status ---'))
    status = forms.IntegerField( required=False, initial=-1, label="Status",
            widget=forms.Select(choices=status_choices),
        )

    type_choices = list(copy.copy(PRICE_CHOICES))
    type_choices.insert(0, (-1, '--- Type ---'))
    type = forms.IntegerField( required=False, initial=-1, label="Type",
            widget=forms.Select(choices=type_choices),
        )

class JobFlowLogic( object ):
    """
        Jobs Flow logic class
    """
    def __init__( self, admin_site ):
        self.admin_site = admin_site

        if IsDebug:
            print 'JobFlowLogic: %s' % repr(self.admin_site)

    def __repr__( self ):
        return ""

    def __call__( self, request, *args, **kwargs ):
        #
        # Main method that does all the hard work, conforming to the Django view interface
        # 
        if not has_add_permission(request, Job):
            raise PermissionDenied

        return self.render(request)

    def doAmendment( self, request ):
        #
        # Make amendment for the given job
        #
        pk, ob = _get_job_instance( request )
        data = request.POST.copy()
        count = int(data.get('amendments') or '0')
        if IsDeepTrace:
            print 'amendments:%s' % count

        branch_id = data.get('branch')
        limit = 0

        if branch_id:
            branch = Branch.objects.get(pk=int(branch_id))
            if branch is not None:
                if branch.pay is not None:
                    pay_id = branch.pay.pk
                    pay = PayStructure.objects.get(pk=int(pay_id))
                    if pay is not None:
                        limit = pay.amendments
        if IsDebug:
            print 'limit:%s' % limit

        if not limit or count < limit:
            data['amendments'] = count + 1

        if IsDebug and IsDeepTrace:
            print data
        
        return _set_job_form( request, data, ob )

    def doDuplicate( self, request ):
        #
        # Make a copy of the given job
        #
        now = datetime.datetime.now()
        pk, ob = _get_job_instance( request )
        data = request.POST.copy()

        data['pk'] = None
        data['title'] = '%s (copy)' % data['title']
        data['received_0'] = now.strftime('%Y-%m-%d')
        data['received_1'] = now.strftime('%H:%M:%S')
        data['finished_0'] = ''
        data['finished_1'] = ''
        data['amendments'] = 0
        data['IsAmendment'] = 0
        data['IsArchive'] = 0

        if IsDebug and IsDeepTrace:
            print data

        return _set_job_form( request, data, ob=None )

    def doArchive( self, request ):
        #
        # Move the given job to archive
        #
        now = datetime.datetime.now()
        pk, ob = _get_job_instance( request )
        data = request.POST.copy()

        data['IsArchive'] = 1
        data['finished_0'] = now.strftime('%Y-%m-%d')
        data['finished_1'] = now.strftime('%H:%M:%S')

        if IsDebug and IsDeepTrace:
            print data

        return _set_job_form( request, data, ob )

    def doUpdate( self, request ):
        #
        # Update (simple save) the given job
        #
        pk, ob = _get_job_instance( request )
        data = request.POST.copy()

        if IsDebug and IsDeepTrace:
            print data

        return _set_job_form( request, data, ob )

    def doDelete( self, request ):
        #
        # Delete the given job
        #
        now = datetime.datetime.now()
        pk, ob = _get_job_instance( request )

        if ob is not None:
            ob.delete()
            IsDone = 1
        else:
            IsDone = 0

        return (IsDone, None,)

    def render( self, request, mode=None, extra_context=None ):
        "Renders the given Form object, returning an HttpResponse."
        if IsDebug:
            print 'JobFlowLogic.render: %s (%s)' % (request.path, mode)

        context_instance = RequestContext(request)
        context = {}

        if request.POST and mode == 'flow-job-action':
            action = request.POST.get('action')
            IsDone = 0
            if IsDebug:
                print 'action:%s' % action

            if action == 'amendment':
                IsDone, form = self.doAmendment( request )
            elif action == 'duplicate':
                IsDone, form = self.doDuplicate( request )
            elif action == 'archive':
                IsDone, form = self.doArchive( request )
            elif action == 'update':
                IsDone, form = self.doUpdate( request )
            elif action == 'delete':
                IsDone, form = self.doDelete( request )

            context['job_was_saved'] = IsDone
            context['jobform'] = form

            args = {}
            args['q'] = request.POST.get('q') or ''
            args['p'] = request.POST.get('p') or ''
            x = request.POST.get('branch__exact')
            if x:
                args['branch__exact'] = x
            x = request.POST.get('status__id__exact')
            if x:
                args['status__id__exact'] = x
            x = request.POST.get('type__exact')
            if x:
                args['type__exact'] = x

            request.POST = None
            request.GET = QueryDict( '&'.join(['%s=%s' % (x, args[x]) for x in args.keys()]) )

        if mode == 'flow-client-search':
            app_label, model_name = 'jobs', 'branch'
            list_display = ((':Company', 'flow_company',), (':Branch', 'title',), (':Country', 'flow_country',), 'city', (':Phones', 'flow_phones',))
            context = self.search_results( request, app_label, model_name, list_display )

        elif mode in ( 'flow-job-search', 'flow-job-action', ):
            app_label, model_name = 'jobs', 'job'
            list_display = ((':Received', 'rendered_received',),
                            (':Status', 'flow_status',),
                            (':AC', 'rendered_AC',), 
                            (':AR', 'rendered_AR',), 
                            (':Title', 'rendered_title',),
                             'contact',
                             'type',
                            (':Property', 'rendered_property',),
                            (':Area', 'square',),
                            (':Drawn', 'rendered_user',),
                            (':Prices', 'flow_prices',),
                            (':AMD', 'rendered_amendments',),
                            (':Total', 'rendered_amend_total',),
                           )
            context.update( self.search_results( request, app_label, model_name, list_display ) )

        else:
            context = {}

        context.update( extra_context or {} )

        if not mode:
            context['jobsearchform'] = JobSearchForm()

        elif mode in ( 'flow-client-search', 'flow-paystructure-item', ):
            if 'cl' not in context:
                app_label, model_name = 'jobs', 'branch'
                cl = _get_model_instance(request, self.admin_site, app_label, model_name)
            else:
                cl = context['cl']
            try:
                pk = cl.result_list[0].pay.id
            except:
                pk = None

            app_label, model_name = 'references', 'paystructure'
            list_display = ((':Title', 'title',), (':Type', 'type',), 'fixed_fee', 'amendments', (':Registered', 'rendered_RD',),)
            context.update( self.choosen_item( request, app_label, model_name, list_display, pk ) )

        elif mode == 'flow-job-item':
            app_label, model_name = 'jobs', 'job'
            cl = _get_model_instance(request, self.admin_site, app_label, model_name)
            pk = cl.result_list[0].id
            instance = Job.objects.get(pk=pk)
            context['jobform'] = JobForm(instance=instance)

        response = dict(context,
            media=self.media,
            )

        template = self.get_template(mode)

        if IsDebug:
            print "OK"
        return render_to_response(template, response, context_instance=context_instance)

    def get_template( self, mode='' ):
        if mode:
            flow, model, action = mode.split('-')
            return 'forms/%s%s%s.html' % (flow, model, action)
        return 'forms/flowlogic.html'

    def search_results( self, request, app_label, model_name, list_display ):
        #
        # Try to search selected objects.
        #
        cl = _get_model_instance(request, self.admin_site, app_label, model_name)

        if cl is None:
            raise Http404('ModelAdmin for model %s.%s not found' % (app_label, model_name))

        headers, rows = get_model_defs( list_display )
        cl.app_label, cl.model_name = app_label, model_name

        p = pagination(cl)

        context = {
            'title'              : cl.title,
            'is_popup'           : cl.is_popup,
            'cl'                 : cl,
            'headers'            : list(get_headers(cl, headers)),
            'rows'               : list(get_rows(cl, rows)),
            'pagination_required': p['pagination_required'],
            'is_page_previous'   : p['is_page_previous'],
            'is_page_next'       : p['is_page_next'],
            'previous'           : previous_page(cl),
            'pages'              : list(get_pages(cl, tuple(p['page_range']))),
            'next'               : next_page(cl),
            'app_label'          : app_label,
        }

        return context

    def choosen_item( self, request, app_label, model_name, list_display, pk=None ):
        #
        # Try to get object items.
        #
        if pk is not None:
            request.GET = QueryDict('pk__exact=%s' % str(pk))
        else:
            request.GET = QueryDict('')

        cl = _get_model_instance(request, self.admin_site, app_label, model_name)

        if cl is None:
            raise Http404('ModelAdmin for model %s.%s not found' % (app_label, model_name))

        headers, rows = get_model_defs( list_display )

        if not 'pk__exact' in request.GET:
            res = None
            empty = '&nbsp;'*20
        else:
            cl.app_label, cl.model_name = app_label, model_name
            res = cl.result_list[0]
            empty = None

        context = { 'items' : map(None, list(get_headers(cl, headers)), list(get_columns(cl, res, rows, no_html=1, empty=empty))) }

        return context

    def _media( self ):
        js = ['js/flow.updater.js', 'js/timer.widget.js', 'js/calendar.js', 'js/admin/DateTimeShortcuts.js']
        #css = ['css/forms.css']
        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js],
                           #css={'all': tuple(['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in css])}
                           )
    media = property(_media)

def get_headers( cl, list_display ):
    lookup_opts = cl.lookup_opts
    for i, field_name in enumerate(list_display):
        if IsDeepTrace:
            print 'header:%s' % field_name
        if field_name.startswith(':'):
            header = field_name[1:]
        else:
            f = lookup_opts.get_field(field_name)
            header = f.verbose_name
        yield { \
                "text"    : header,
                "sortable": False,
                "url"     : '',
              }

def get_rows( cl, list_display ):
    pk = cl.lookup_opts.pk.attname
    for res in cl.result_list:
        result_id, class_id = get_row_id( cl, pk, res )
        yield ( class_id, list(get_columns(cl, res, list_display)), )

def get_columns( cl, res, list_display, no_html=None, empty=None ):
    first = True
    pk = cl.lookup_opts.pk.attname
    for i, field_name in enumerate(list_display):
        if IsDeepTrace:
            print 'column:%s' % field_name
        if res is None:
            yield not no_html and '<td><td>' or empty or ''
        else:
            classes = []
            try:
                f = cl.lookup_opts.get_field(field_name)
            except models.FieldDoesNotExist:
                # For non-field list_display values, the value is either a method,
                # property or returned via a callable.
                try:
                    if callable(field_name):
                        attr = field_name
                        value = attr(res)
                    elif hasattr(cl.model_admin, field_name) and \
                            not field_name == '__str__' and not field_name == '__unicode__':
                        attr = getattr(cl.model_admin, field_name)
                        value = attr(res)
                    else:
                        attr = getattr(res, field_name, None)
                        if callable(attr):
                            value = attr()
                        else:
                            value = attr
                    allow_tags = getattr(attr, 'allow_tags', False)
                    boolean = getattr(attr, 'boolean', False)
                    if boolean:
                        allow_tags = True
                        result_repr = _boolean_icon(value)
                    else:
                        result_repr = smart_unicode(value)
                except (AttributeError, ObjectDoesNotExist):
                    result_repr = EMPTY_CHANGELIST_VALUE
                else:
                    # Strip HTML tags in the resulting text, except if the
                    # function has an "allow_tags" attribute set to True.
                    if not allow_tags:
                        result_repr = escape(result_repr)
                    else:
                        result_repr = mark_safe(result_repr)
            else:
                field_val = getattr(res, f.attname)

                if isinstance(f.rel, models.ManyToOneRel):
                    if field_val is not None:
                        result_repr = escape(getattr(res, f.name))
                    else:
                        result_repr = EMPTY_CHANGELIST_VALUE
                # Dates and times are special: They're formatted in a certain way.
                elif isinstance(f, models.DateField) or isinstance(f, models.TimeField):
                    if field_val:
                        (date_format, datetime_format, time_format) = get_date_formats()
                        if isinstance(f, models.DateTimeField):
                            result_repr = capfirst(dateformat.format(field_val, datetime_format))
                        elif isinstance(f, models.TimeField):
                            result_repr = capfirst(dateformat.time_format(field_val, time_format))
                        else:
                            result_repr = capfirst(dateformat.format(field_val, date_format))
                    else:
                        result_repr = EMPTY_CHANGELIST_VALUE
                    classes.append('nowrap')
                # Booleans are special: We use images.
                elif isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
                    result_repr = _boolean_icon(field_val)
                # DecimalFields are special: Zero-pad the decimals.
                elif isinstance(f, models.DecimalField):
                    if field_val is not None:
                        result_repr = ('%%.%sf' % f.decimal_places) % field_val
                    else:
                        result_repr = EMPTY_CHANGELIST_VALUE
                # Fields with choices are special: Use the representation
                # of the choice.
                elif f.choices:
                    result_repr = dict(f.choices).get(field_val, EMPTY_CHANGELIST_VALUE)
                else:
                    result_repr = escape(field_val)

            if force_unicode(result_repr) == '':
                result_repr = mark_safe('&nbsp;')

            result_id, class_id = get_row_id( cl, pk, res )
            column_class = classes and ' class="%s"' % ' '.join([x for x in classes]) or ''
            column_onclick = ' onclick="javascript:onItem(\'%s\',\'%s\');"' % (class_id, get_cl_model_name(cl))

            # If list_display_links not defined, add the link tag to the first field
            if first and not cl.list_display_links or field_name in cl.list_display_links:
                table_tag = { True  : 'th%s%s' % (column_class, column_onclick), 
                              False : 'td%s%s' % (column_class, column_onclick) }[first]
                first = False
                url = get_model_url(cl, res)
                x = mark_safe(u'%s<a target="blank" href="%s"%s>%s</a>%s' % ( \
                    not no_html and ('<%s%s>' % (table_tag, column_class)) or '',
                    url, 
                    ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id,
                    conditional_escape(result_repr), 
                    not no_html and ('</%s>' % table_tag) or '')
                )
            else:
                x = mark_safe(u'%s%s%s' % ( \
                    not no_html and ('<td%s%s>' % (column_class, column_onclick)) or '', 
                    conditional_escape(result_repr), 
                    not no_html and '</td>' or '')
                )

            yield x

def get_pages( cl, pages ):
    for i in pages:
        if IsDeepTrace:
            print 'page:' + str(i)
        if i == DOT:
            x = u'... '
        elif i == cl.page_num:
            x = mark_safe(u'<span class="this-page">%d</span> ' % (i+1))
        else:
            id = 'flow-page-%s-%s' % (get_cl_model_name(cl), i)
            x = mark_safe(u'<a href="#" onclick="javascript:onItem(\'%s\',\'\');return false;"%s>%d</a> ' % ( \
                id, (i == cl.paginator.num_pages-1 and ' class="end"' or ''), i+1)
            )
        yield x

def previous_page( cl ):
    s = 'previous'
    i = cl.page_num
    after = ''
    if i == 0:
        return mark_safe(u'<span class="disabled-page">%s</span>%s' % (s, after))
    else:
        i = i - 1;
        id = 'flow-page-%s-%s' % (get_cl_model_name(cl), i)
        return mark_safe(u'<a href="#" onclick="javascript:onItem(\'%s\',\'\');return false;">%s</a> ' % (id, s))

def next_page( cl ):
    s = 'next'
    i = cl.page_num
    before = ''
    if i == cl.paginator.num_pages - 1:
        return mark_safe(u'%s<span class="disabled-page">%s</span>&nbsp;' % (before, s))
    else:
        i = i + 1;
        id = 'flow-page-%s-%s' % (get_cl_model_name(cl), i)
        return mark_safe(u'<a href="#" onclick="javascript:onItem(\'%s\',\'\');return false;">%s</a> ' % (id, s))

def pagination( cl ):
    paginator, page_num = cl.paginator, cl.page_num

    pagination_required = (not cl.show_all or not cl.can_show_all) and cl.multi_page
    if not pagination_required:
        page_range = []
    else:
        ON_EACH_SIDE = 3
        ON_ENDS = 2

        # If there are 10 or fewer pages, display links to every page.
        # Otherwise, do some fancy
        if paginator.num_pages <= 10:
            page_range = range(paginator.num_pages)
        else:
            # Insert "smart" pagination links, so that there are always ON_ENDS
            # links at either end of the list of pages, and there are always
            # ON_EACH_SIDE links at either end of the "current page" link.
            page_range = []
            if page_num > (ON_EACH_SIDE + ON_ENDS):
                page_range.extend(range(0, ON_EACH_SIDE - 1))
                page_range.append(DOT)
                page_range.extend(range(page_num - ON_EACH_SIDE, page_num + 1))
            else:
                page_range.extend(range(0, page_num + 1))
            if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS - 1):
                page_range.extend(range(page_num + 1, page_num + ON_EACH_SIDE + 1))
                page_range.append(DOT)
                page_range.extend(range(paginator.num_pages - ON_ENDS, paginator.num_pages))
            else:
                page_range.extend(range(page_num + 1, paginator.num_pages))

    need_show_all_link = cl.can_show_all and not cl.show_all and cl.multi_page
    if IsDeepTrace:
        print page_range
    return {
        'pagination_required': pagination_required,
        'is_page_previous': paginator.num_pages > 1 and 1 or 0,
        'page_range': page_range,
        'is_page_next': paginator.num_pages > 1 and 1 or 0,
    }

def get_model_url( cl, res ):
    return '../%s/%s/%s' % (cl.app_label, cl.model_name, cl.url_for_result(res))

def get_model_defs( list_display ):
    headers = []
    rows = []

    for x in list_display:
        if isinstance(x, (list, tuple)):
            headers.append(x[0])
            rows.append(x[1])
        else:
            headers.append(x)
            rows.append(x)

    return ( tuple(headers), tuple(rows), )

def get_row_id( cl, pk, res ):
    # Convert the pk to something that can be used in Javascript.
    # Problem cases are long ints (23L) and non-ASCII strings.
    if cl.to_field:
        attr = str(cl.to_field)
    else:
        attr = pk
    id = force_unicode(getattr(res, attr, None))
    result_id = repr(id)[1:]
    class_id = 'flow-row-%s-%s' % (cl.model_name in ('company', 'branch', 'contact') and 'client' or cl.model_name, id)
    return ( result_id, class_id, )

def get_cl_model_name( cl ):
    return cl.model_name in ('company', 'branch', 'contact') and 'client' or cl.model_name
