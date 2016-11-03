#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# Overriden and changes Django default module: django.contrib.admin.views.main
# manage/main.py
#
# Checked: 2010/06/27
# ichar@g2.ru
#
from manage.filterspecs import FilterSpec, RelatedFilterSpec

from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import quote
from django.core.paginator import Paginator, InvalidPage
from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import force_unicode, smart_unicode, smart_str
from django.utils.translation import ugettext
from django.utils.http import urlencode
import operator

try:
    set
except NameError:
    from sets import Set as set   # Python 2.3 fallback

# The system will display a "Show all" link on the change list only if the
# total result count is less than or equal to this setting.
MAX_SHOW_ALL_ALLOWED = 200

# Changelist settings
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
PAGE_SIZE_VAR = 's'
SEARCH_VAR = 'q'
TO_FIELD_VAR = 't'
IS_POPUP_VAR = 'pop'
SHOW_FILTER_VAR = 'f'
ERROR_FLAG = 'e'

QUERY_SPLITTER = '+' # use '' for lookup by default, '+' is like '__exact'

# Text to display within change-list table cells if the value is blank.
EMPTY_CHANGELIST_VALUE = '(None)'

class ChangeList( object ):
    def __init__( self, request, context, 
                  model=None, list_display=None, list_display_links=None, list_filter=None, date_hierarchy=None, search_fields=None, 
                  list_select_related=None, list_per_page=None, filter_panel_width=None, change_list_style=None, editable=None,
                  ordering=None, query_splitter=None
                ):
        if request is None or context is None:
            return
        #
        #   Explicit attributes
        #
        self.model_admin = self.context = context
        #
        #   Implicit default attributes
        #
        self.model = model or context.model
        self.opts = self.model._meta
        self.lookup_opts = self.opts

        self.list_display = list_display or getattr(context, 'list_display', None) or ()
        self.list_display_links = list_display_links or getattr(context, 'list_display_links', None) or ()
        self.date_hierarchy = date_hierarchy or getattr(context, 'date_hierarchy', None) or None
        self.search_fields = search_fields or getattr(context, 'search_fields', None) or ()
        self.list_select_related = list_select_related or getattr(context, 'list_select_related', False)
        self.list_per_page = list_per_page or getattr(context, 'list_per_page', None) or 10
        self.filter_panel_width = filter_panel_width or getattr(context, 'filter_panel_width', None) or '150px'
        self.change_list_style = change_list_style or getattr(context, 'change_list_style', None) or 'width:750px;'
        #
        #   Editable object property
        #
        if editable is not None:
            self.editable = editable and True or False
        elif hasattr(context, 'editable'):
            self.editable = context.editable and True or False
        else:
            self.editable = True
        self.root_query_set = context.queryset(request)
        #
        #   Custom list filter
        #
        self.list_filter = []
        self.list_filter_attrs = []
        for i, filter in enumerate(list_filter or getattr(context, 'list_filter')):
            if isinstance(filter, (list, tuple)):
                field, attrs = filter
                self.list_filter.append(field)
                self.list_filter_attrs.append(attrs)
            else:
                self.list_filter.append(filter)
                self.list_filter_attrs.append(None)
        #
        #   Get search parameters from the query string
        #
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.show_all = ALL_VAR in request.GET
        self.is_popup = IS_POPUP_VAR in request.GET
        self.to_field = request.GET.get(TO_FIELD_VAR)
        #
        #   Custom list per page
        #
        try:
            self.page_size = int(request.GET.get(PAGE_SIZE_VAR) or 0)
        except:
            self.page_size = 0
        if self.page_size:
            self.list_per_page = self.page_size
        self.has_page_size = 1
        #
        #   Custom show-filter specification
        #
        x = request.GET.get(SHOW_FILTER_VAR, None)
        self.show_filter = x is None and 1 or x and x != '0' and 1 or 0
        #
        #   Cleaning the request
        #
        self.params = dict(request.GET.items())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if TO_FIELD_VAR in self.params:
            del self.params[TO_FIELD_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]
        if ALL_VAR in self.params and PAGE_SIZE_VAR in self.params:
            del self.params[ALL_VAR]
        #
        #   Filtering and Custom request validation
        #
        self.filter_specs, self.has_filters, self.filter_choices = self.get_filters(request)
        self._request_attribute_validation()
        #
        #   Custom force results ordering
        #
        self.ordering = ordering
        self.order_field, self.order_type = self.get_ordering()
        #
        #   Get results
        #
        self.query = request.GET.get(SEARCH_VAR, '')
        self.query_set = self.get_query_set(query_splitter)
        self.get_results(request)
        self.title = (self.is_popup and ugettext('Select %s') % force_unicode(self.opts.verbose_name) or 
            ugettext('Select %s to change') % force_unicode(self.opts.verbose_name))
        self.pk_attname = self.lookup_opts.pk.attname
        #
        #   Preload images
        #
        self.preload_images = getattr(context, 'preload_images', None) or []
        self.preload_images.append('mp-item-history.png')

    def _request_attribute_validation( self ):
        drop = []
        for key in self.params.keys():
            attrs = key.split('__')
            if len(attrs) > 2 and attrs[2] == 'exact':
                field = attrs[0]
                value = self.params[key]
                if field in self.filter_choices:
                    if not value in self.filter_choices[field][0]:
                        setattr(self.filter_choices[field][1], 'lookup_val', None)
                        drop.append( key )
        for key in drop:
            del self.params[key]

    def get_filters( self, request ):
        filter_specs = []
        filter_choices = {}
        if self.list_filter:
            filter_fields = [self.lookup_opts.get_field(field_name) for field_name in self.list_filter]
            for i, f in enumerate(filter_fields):
                extra_attrs = self.list_filter_attrs[i]
                spec = FilterSpec.create(f, request, self.params, self.model, self.context, extra_attrs=extra_attrs)
                if spec and spec.has_output():
                    filter_specs.append(spec)
                    if isinstance(spec, RelatedFilterSpec) and hasattr(spec, 'lookup_choices'):
                        try:
                            filter_choices[f.name] = ([smart_unicode(x[0]) for x in spec.lookup_choices], spec,)
                        except:
                            pass
        return filter_specs, bool(filter_specs), filter_choices

    def get_query_string( self, new_params=None, remove=None ):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(p)

    def get_results( self, request ):
        paginator = Paginator(self.query_set, self.list_per_page)
        # Get the number of objects, with admin filters applied.
        result_count = paginator.count

        # Get the total number of objects, with no admin filters applied.
        # Perform a slight optimization: Check to see whether any filters were
        # given. If not, use paginator.hits to calculate the number of objects,
        # because we've already done paginator.hits and the value is cached.
        if not self.query_set.query.where:
            full_result_count = result_count
        else:
            full_result_count = self.root_query_set.count()

        can_show_all = result_count <= MAX_SHOW_ALL_ALLOWED
        multi_page = result_count > self.list_per_page

        # Get the list of objects to display on this page.
        if (self.show_all and can_show_all) or not multi_page:
            result_list = list(self.query_set)
        else:
            try:
                result_list = paginator.page(self.page_num + 1).object_list
            except InvalidPage:
                result_list = ()

        self.result_count = result_count
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator

    def get_ordering( self ):
        lookup_opts, params = self.lookup_opts, self.params
        # For ordering, first check the "ordering" parameter in the admin
        # options, then check the object's default ordering. If neither of
        # those exist, order descending by ID by default. Finally, look for
        # manually-specified ordering from the query string.
        if self.ordering:
            ordering = self.ordering
        else:
            ordering = self.context.ordering or lookup_opts.ordering or ['-' + lookup_opts.pk.name]

        if ordering[0].startswith('-'):
            order_field, order_type = ordering[0][1:], 'desc'
        else:
            order_field, order_type = ordering[0], 'asc'
        if ORDER_VAR in params:
            try:
                field_name = self.list_display[int(params[ORDER_VAR])]
                try:
                    f = lookup_opts.get_field(field_name)
                except models.FieldDoesNotExist:
                    # See whether field_name is a name of a non-field
                    # that allows sorting.
                    try:
                        if callable(field_name):
                            attr = field_name
                        elif hasattr(self.context, field_name):
                            attr = getattr(self.context, field_name)
                        else:
                            attr = getattr(self.model, field_name)
                        order_field = attr.admin_order_field
                    except AttributeError:
                        pass
                else:
                    order_field = f.name
            except (IndexError, ValueError):
                pass # Invalid ordering specified. Just use the default.
        if ORDER_TYPE_VAR in params and params[ORDER_TYPE_VAR] in ('asc', 'desc'):
            order_type = params[ORDER_TYPE_VAR]
        return order_field, order_type

    def get_query_set( self, query_splitter=None ):
        qs = self.root_query_set
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, PAGE_SIZE_VAR, SHOW_FILTER_VAR):
            if i in lookup_params:
                del lookup_params[i]
        for key, value in lookup_params.items():
            if not isinstance(key, str):
                # 'key' will be used as a keyword argument later, so Python
                # requires it to be a string.
                del lookup_params[key]
                lookup_params[smart_str(key)] = value

            # if key ends with __in, split parameter into separate values
            if key.endswith('__in'):
                lookup_params[key] = value.split(',')

        # Apply lookup parameters from the query string.
        try:
            qs = qs.filter(**lookup_params)
        # Naked except! Because we don't have any other way of validating "params".
        # They might be invalid if the keyword arguments are incorrect, or if the
        # values are not in the correct type, so we might get FieldError, ValueError,
        # ValicationError, or ? from a custom field that raises yet something else 
        # when handed impossible data.
        except:
            raise IncorrectLookupParameters

        # Use select_related() if one of the list_display options is a field
        # with a relationship.
        if self.list_select_related:
            qs = qs.select_related()
        else:
            for field_name in self.list_display:
                try:
                    f = self.lookup_opts.get_field(field_name)
                except models.FieldDoesNotExist:
                    pass
                else:
                    if isinstance(f.rel, models.ManyToOneRel):
                        qs = qs.select_related()
                        break

        # Set ordering.
        if self.order_field:
            qs = qs.order_by('%s%s' % ((self.order_type == 'desc' and '-' or ''), self.order_field))

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.search_fields and self.query:
            sp = query_splitter is None and QUERY_SPLITTER or query_splitter
            for bit in self.query.split(sp):
                or_queries = [models.Q(**{construct_search(field_name): bit.strip()}) for field_name in self.search_fields]
                other_qs = QuerySet(self.model)
                other_qs.dup_select_related(qs)
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                qs = qs & other_qs
            for field_name in self.search_fields:
                if '__' in field_name:
                    qs = qs.distinct()
                    break

        if self.opts.one_to_one_field:
            qs = qs.complex_filter(self.opts.one_to_one_field.rel.limit_choices_to)

        return qs

    def url_for_result( self, result ):
        return "%s/" % quote(getattr(result, self.pk_attname))
