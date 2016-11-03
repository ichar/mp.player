#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# References. Extra tags.
#
# Checked: 2011/11/11
# ichar@g2.ru
#
import datetime
import settings

from manage.main import ALL_VAR, SEARCH_VAR, ORDER_VAR, ORDER_TYPE_VAR, PAGE_VAR, PAGE_SIZE_VAR, SHOW_FILTER_VAR, EMPTY_CHANGELIST_VALUE
from django.core.paginator import Paginator, InvalidPage
from django.template import Library
from django import template

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateformat
from django.utils.html import escape, conditional_escape
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.translation import get_date_formats, get_partial_date_formats, ugettext as _
from django.utils.encoding import smart_unicode, smart_str, force_unicode

LIST_PER_PAGE = 10
DOT = '.'

register = Library()

#
# Admin Template tags overridens ==================================================================
#

def admin_list_filter_extras( cl, spec ):
    x = list(spec.choices(cl))
    return {'title': spec.title(), 'choices' : x, 'size' : len(x) > settings.FILTER_INLINE_SIZE and 1 or 0}
admin_list_filter_extras = register.inclusion_tag('admin/filter.html')(admin_list_filter_extras)

def search_form_extras( cl ):
    return {
        'cl': cl,
        'show_result_count': cl.result_count != cl.full_result_count,
        'search_var': SEARCH_VAR,
        'page_size_var': PAGE_SIZE_VAR,
        'show_filter_var': SHOW_FILTER_VAR,
    }
search_form_extras = register.inclusion_tag('admin/search_form.html')(search_form_extras)

PAGE_SIZE_CHOICES = ( \
    (    0, 'default', ),
    (   10, '10',      ),
    (   20, '20',      ),
    (   30, '30',      ),
    (   40, '40',      ),
    (   50, '50',      ),
    (  100, '100',     ),
    (  500, '500',     ),
   #( 1000, '1000',    ),
)

def paginator_size_extras( cl ):
    html = """<option value="%s"%s>%s</option>"""
    return mark_safe(u'<select name="%s" onchange="%s">%s</select>' % ( \
        PAGE_SIZE_VAR,
        u'this.form.submit();',
        u''.join([html % (value, cl.page_size == value and ' selected' or '', title) for value, title in PAGE_SIZE_CHOICES]))
    )
paginator_size_extras = register.simple_tag(paginator_size_extras)

def paginator_previous_extras( cl ):
    x = 'previous'
    i = cl.page_num
    after = ''
    if i == 0:
        return mark_safe(u'<span class="disabled-page">%s</span>%s' % (x, after))
    else:
        i = i - 1;
        return mark_safe(u'<a class="previous" href="%s">%s</a>%s' % (cl.get_query_string({PAGE_VAR: i}), x, after))
paginator_previous_extras = register.simple_tag(paginator_previous_extras)

def paginator_next_extras( cl ):
    x = 'next'
    i = cl.page_num
    before = ''
    if i == cl.paginator.num_pages - 1:
        return mark_safe(u'%s<span class="disabled-page">%s</span>' % (before, x))
    else:
        i = i + 1;
        return mark_safe(u'%s<a class="next" href="%s">%s</a>' % ( before, cl.get_query_string({PAGE_VAR: i}), x) )
paginator_next_extras = register.simple_tag(paginator_next_extras)

def pagination_extras( cl ):
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
    return {
        'cl': cl,
        'pagination_required': pagination_required,
        'show_all_url': need_show_all_link and cl.get_query_string({ALL_VAR: ''}),
        'is_page_previous': paginator.num_pages > 1 and 1 or 0,
        'page_range': page_range,
        'is_page_next': paginator.num_pages > 1 and 1 or 0,
        'ALL_VAR': ALL_VAR,
        '1': 1,
    }
pagination_extras = register.inclusion_tag('admin/pagination.html')(pagination_extras)

def result_headers( cl ):
    lookup_opts = cl.lookup_opts
    
    for i, field_name in enumerate(cl.list_display):
        if field_name in ('notes',):
            continue

        attr = None
        try:
            f = lookup_opts.get_field(field_name)
            admin_order_field = None
        except models.FieldDoesNotExist:
            # For non-field list_display values, check for the function
            # attribute "short_description". If that doesn't exist, fall back
            # to the method name. And __str__ and __unicode__ are special-cases.
            if field_name == '__unicode__':
                header = force_unicode(lookup_opts.verbose_name)
            elif field_name == '__str__':
                header = smart_str(lookup_opts.verbose_name)
            else:
                if callable(field_name):
                    attr = field_name # field_name can be a callable
                else:
                    try:
                        attr = getattr(cl.model_admin, field_name)
                    except AttributeError:
                        try:
                            attr = getattr(cl.model, field_name)
                        except AttributeError:
                            raise AttributeError, \
                                "'%s' model or '%s' objects have no attribute '%s'" % \
                                    (lookup_opts.object_name, cl.model_admin.__class__, field_name)
                
                try:
                    header = attr.short_description
                except AttributeError:
                    if callable(field_name):
                        header = field_name.__name__
                    else:
                        header = field_name
                    header = header.replace('_', ' ')

            # It is a non-field, but perhaps one that is sortable
            admin_order_field = getattr(attr, "admin_order_field", None)
            if not admin_order_field:
                yield {"text": header}
                continue

            # So this _is_ a sortable non-field.  Go to the yield
            # after the else clause.
        else:
            header = f.verbose_name

        th_classes = []
        new_order_type = 'asc'
        if field_name == cl.order_field or admin_order_field == cl.order_field:
            th_classes.append('sorted %sending' % cl.order_type.lower())
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[cl.order_type.lower()]

        yield {"text"        : header,
               "sortable"    : True,
               "url"         : cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type}),
               "class_attrib": mark_safe(th_classes and ' class="%s"' % ' '.join(th_classes) or '')}

def _boolean_icon( field_val, id=None ):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    field_id = id and ('id="%s"' % id) or ''
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" width="10px" alt="%s" %s/>' % ( \
        settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], field_val, field_id)
        )

def _notes_icon( id=None ):
    field_id = id and ('id="%s"' % id) or ''
    return mark_safe(u'<img class="notes" src="%simg/admin/notes-1.png" alt="Notes" title="Click to see Notes" %s/>' % ( \
        settings.ADMIN_MEDIA_PREFIX, field_id)
        )

def items_for_result( cl, result ):
    first = True
    pk = cl.lookup_opts.pk.attname

    for field_name in cl.list_display:
        if field_name in ('notes',):
            continue

        row_class = ''
        
        try:
            f = cl.lookup_opts.get_field(field_name)
        except models.FieldDoesNotExist:
            # For non-field list_display values, the value is either a method,
            # property or returned via a callable.
            try:
                if callable(field_name):
                    attr = field_name
                    value = attr(result)
                elif hasattr(cl.model_admin, field_name) and \
                   not field_name == '__str__' and not field_name == '__unicode__':
                    attr = getattr(cl.model_admin, field_name)
                    value = attr(result)
                else:
                    attr = getattr(result, field_name)
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
            field_val = getattr(result, f.attname)

            if isinstance(f.rel, models.ManyToOneRel):
                if field_val is not None:
                    result_repr = escape(getattr(result, f.name))
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
                row_class = ' class="nowrap"'
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

        # If list_display_links not defined, add the link tag to the first field
        if (first and not cl.list_display_links) or field_name in cl.list_display_links:
            table_tag = {True:'th', False:'td'}[first]
            first = False
            url = cl.url_for_result(result)
            # Convert the pk to something that can be used in Javascript.
            # Problem cases are long ints (23L) and non-ASCII strings.
            if cl.to_field:
                attr = str(cl.to_field)
            else:
                attr = pk
            result_id = repr(force_unicode(getattr(result, attr)))[1:]

            yield mark_safe(u'<%s%s><a href="%s"%s>%s</a></%s>' % ( \
                    table_tag, 
                    row_class, 
                    url, 
                    cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or '',
                    conditional_escape(result_repr), 
                    table_tag
                    ))
        else:
            yield mark_safe(u'<td%s>%s</td>' % (row_class, conditional_escape(result_repr)))

def items_for_notes( cl, row ):
    pk = cl.lookup_opts.pk.attname
    id = getattr(row, pk)
    cols = len(cl.list_display)

    if 'notes' in cl.list_display and hasattr(row, 'rendered_notes'): # and getattr(row, 'notes')
        #f = cl.lookup_opts.get_field('notes')
        value = apply(getattr(row, 'rendered_notes'))
        #print value, id #f.attname, 
        return { \
            'data'  : mark_safe(u'<td colspan="%s">%s</td>' % (cols, value)), #conditional_escape(escape(value))
            'class' : not getattr(row, 'notes') and ' hidden' or settings.NOTES_CLASS_DEFAULT and ' '+settings.NOTES_CLASS_DEFAULT or '',
            'id'    : id,
        }
    else:
        return { \
            'data'  : mark_safe(u'<td colspan="%s"></td>' % cols),
            'class' : ' hidden',
            'id'    : id,
        }

"""
def results( cl ):
    for res in cl.result_list:
        yield list(items_for_result(cl,res))
"""

def results( cl ):
    #rows = []
    for row in cl.result_list:
        columns = list(items_for_result(cl, row))
        notes = items_for_notes(cl, row)
        #print notes
        yield {'columns':columns, 'notes':notes}
        #rows.append({'columns':list(items_for_result(cl, row)), 'notes':items_for_notes(cl, row)})
    #return rows

def result_list_extras( cl ):
    return { \
            'cl'            : cl,
            'result_headers': list(result_headers(cl)),
            'results'       : list(results(cl)),
            }
result_list_extras = register.inclusion_tag("admin/change_list_results.html")(result_list_extras)

def date_hierarchy_extras( cl ):
    if cl.date_hierarchy:
        field_name = cl.date_hierarchy
        year_field = '%s__year' % field_name
        month_field = '%s__month' % field_name
        day_field = '%s__day' % field_name
        field_generic = '%s__' % field_name
        year_lookup = cl.params.get(year_field)
        month_lookup = cl.params.get(month_field)
        day_lookup = cl.params.get(day_field)
        year_month_format = 'Y F'
        month_day_format = 'd F'
        year_format = 'Y'
        month_format = 'F'
        selected_month_format = 'F, Y'
        day_format = 'F j, Y - l'

        qs = cl.root_query_set # cl.query_set
        link = lambda d: mark_safe(cl.get_query_string(d, [field_generic]))

        if year_lookup and month_lookup and day_lookup:
            selected_month = datetime.datetime(int(year_lookup), int(month_lookup), 1)
            selected_day = datetime.date(int(year_lookup), int(month_lookup), int(day_lookup))
            days = qs.filter(**{year_field: year_lookup, month_field: month_lookup}).dates(field_name, 'day')
            options = {
                'show' : True,
                'backs': [{
                    'link' : link({}),
                    'title': _('All dates')
                },{
                    'link' : link({year_field: year_lookup}),
                    'title': year_lookup
                },{
                    'link' : link({year_field: year_lookup, month_field: month_lookup}),
                    'title': dateformat.format(selected_month, month_format)
                },{
                    'link' : None, #link({year_field: year_lookup, month_field: month_lookup, day_field: day_lookup}),
                    'title': dateformat.format(selected_day, day_format)
                },
                ],
                'choices': [{
                    'link' : link({year_field: year_lookup, month_field: month_lookup, day_field: day.day}),
                    'title': dateformat.format(day, month_day_format)
                } for day in days],
                'range'  : 'Date ranges',
            }
            """
            next_day = selected_day
            while( next_day.month = int(month_lookup) ):
                next_day += datetime.timedelta(1)
                if next_day in days:
                   next_day.month = int(month_lookup)
                   break
            """
            if (selected_day + datetime.timedelta(1)).month == int(month_lookup):
                options['next'] = {
                    'link' : link({year_field: year_lookup, month_field: month_lookup, day_field: int(day_lookup) + 1}),
                }
            if (selected_day - datetime.timedelta(1)).month == int(month_lookup):
                options['previous'] = {
                    'link' : link({year_field: year_lookup, month_field: month_lookup, day_field: int(day_lookup) - 1}),
                }

        elif year_lookup and month_lookup:
            selected_month = datetime.datetime(int(year_lookup), int(month_lookup), 1)
            days = qs.filter(**{year_field: year_lookup, month_field: month_lookup}).dates(field_name, 'day')
            options = {
                'show' : True,
                'backs': [{
                    'link' : link({}),
                    'title': _('All dates')
                },{
                    'link' : link({year_field: year_lookup}),
                    'title': year_lookup
                },{
                    'link' : None, #link({year_field: year_lookup, month_field: month_lookup}),
                    'title': dateformat.format(selected_month, selected_month_format)
                },
                ],
                'choices': [{
                    'link' : link({year_field: year_lookup, month_field: month_lookup, day_field: day.day}),
                    'title': dateformat.format(day, month_day_format)
                } for day in days],
                'range'  : 'Date ranges'
            }
            if int(month_lookup) < 12:
                options['next'] = {
                    'link' : link({year_field: year_lookup, month_field: int(month_lookup) + 1}),
                }
            if int(month_lookup) > 1:
                options['previous'] = {
                    'link' : link({year_field: year_lookup, month_field: int(month_lookup) - 1}),
                }
        elif year_lookup:
            months = qs.filter(**{year_field: year_lookup}).dates(field_name, 'month')
            options = {
                'show' : True,
                'backs': [{
                    'link' : link({}),
                    'title': _('All dates')
                },{
                    'link' : None, #link({year_field: year_lookup}),
                    'title': year_lookup
                },
                ],
                'choices': [{
                    'link' : link({year_field: year_lookup, month_field: month.month}),
                    'title': dateformat.format(month, year_month_format)
                } for month in months],
                'range'  : 'Month ranges'
            }
            if int(year_lookup) < 2099:
                options['next'] = {
                    'link' : link({year_field: int(year_lookup) + 1}),
                }
            if int(year_lookup) > 1990:
                options['previous'] = {
                    'link' : link({year_field: int(year_lookup) - 1}),
                }
        else:
            years = list(qs.dates(field_name, 'year'))
            years.sort()
            years.reverse()
            options = {
                'show'   : True,
                'choices': [{
                    'link' : link({year_field: year.year}),
                    'title': year.year
                } for year in years],
                'range'  : 'Year ranges'
            }
        now = datetime.datetime.now()
        options['current_date'] = {
            'link' : link({year_field: str(now.year), month_field: str(now.month), day_field: str(now.day)}),
        }
        return options
date_hierarchy_extras = register.inclusion_tag('admin/date_hierarchy.html')(date_hierarchy_extras)

#
# Custom tags =====================================================================================
#

def total_estimated_time( cl ):
    if cl.model._meta.module_name == 'job':
        now = datetime.datetime.now()
        value = 0
        #print "%s:%s" % (cl.order_field, cl.order_type)

        if cl.order_field == 'received' and cl.order_type == 'desc':
            query_set = cl.query_set
            IsOrdered = 1
            #print 1
        else:
            requested_order = (cl.order_field, cl.order_type,)
            cl.order_field, cl.order_type = 'received', 'desc'
            query_set = cl.get_query_set()
            #res.sort( lambda x, y: cmp(x.received, y.received) )
            #res.reverse()
            IsOrdered = 0
            #print 2

        IsBreak = 0
        paginator = Paginator(query_set, LIST_PER_PAGE)
        page = 0

        while not IsBreak:
            page += 1
            try:
                res = paginator.page(page).object_list
            except InvalidPage:
                break
            for ob in res:
                if now - ob.received <= datetime.timedelta(1):
                    if ob.status.title.lower() == 'pending':
                        if ob.runtime:
                            value += ob.runtime
                else:
                    IsBreak = 1
                    break
            del res

        if not IsOrdered:
            cl.order_field, cl.order_type = requested_order
        return {'title': 'Total estimated time:', 'value': "%02d:%02d" % (value/60, value%60)}
    return {'title': '', 'value': ''}
total_estimated_time = register.inclusion_tag('admin/total_estimated_time.html')(total_estimated_time)
