#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# jobs/exporter.py
#
# Checked: 2010/06/27
# ichar@g2.ru
#
import re
import datetime
import decimal
import csv
import xlwt
from StringIO import StringIO

from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminSplitDateTime
from django.shortcuts import render_to_response
from django.db.models import Q
from django.forms import models
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode, smart_str
from django.utils.translation import ugettext as _

from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.core.serializers import serialize
from django.template import loader, RequestContext
from django.template.defaultfilters import slugify
from django.db.models.loading import get_model

from django.contrib.auth.models import User

from widgets import SelectMonthWidget, CheckboxList
from jobs.models import Company, Branch, Contact, Job, PRICE_CHOICES, BRANCH_CHOICES
from references.models import Country, Department, Status, PayStructure, MYOB

IsDebug = 0

re_datetime_format = re.compile(r'(\d\d\d\d)-(\d\d|\d)-(\d\d|\d) (\d\d|\d):(\d\d|\d):(\d\d|\d)')
re_date_format = re.compile(r'(\d\d\d\d)-(\d\d|\d)-(\d\d|\d)')

ALLOWED_EXPORT_TYPES = {
    'txt': {
        'mimetype'  : 'text/plain',
        'filename'  : '%s.txt',
        'template'  : 'export/txt.html',
        'delimeter' : '\t',
        'newline'   : '\n'
    },
    'csv1': {
        'mimetype'  : 'text/csv',
        'filename'  : '%s.csv',
        'template'  : 'export/csv.html',
        'delimeter' : ';',
        'newline'   : '\n'
    },
    'csv2': {
        'mimetype'  : 'text/csv',
        'filename'  : '%s.csv',
        'template'  : 'export/csv.html',
        'delimeter' : ',',
        'newline'   : '\n'
    },
    'xls': {
        'mimetype'  : 'application/vnd.ms-excel',
        'filename'  : '%s.xls',
        'output'    : 'xls',
    },
    'json': {
        'mimetype'  : 'text/json',
        'filename'  : '%s.json',
        'serializer': 'json',
    },
    'xml': {
        'mimetype'  : 'text/xml',
        'filename'  : '%s.xml',
        'serializer': 'xml',
    },
    'yaml': {
        'mimetype'  : 'text/yaml',
        'filename'  : '%s.yaml',
        'serializer': 'yaml',
    },
    'py': {
        'mimetype'  : 'application/python',
        'filename'  : '%s.py',
        'serializer': 'python',
    }
}

REPORT_CHOICES = (
    ( 0, _("Jobs/MYOB monthly Excel Reporting") ),
    ( 1, _("Client Details") ),
    ( 2, _("Job Details") ),
)

YES_NO_CHOICES = ( ( 0, _('No'),), (1, _('Yes'),), ) 

OUTPUT_DATE_FORMAT = '%d.%m.%Y'
OUTPUT_DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_received( ob ):
    return ob.received is not None and ob.received.strftime(OUTPUT_DATE_TIME_FORMAT) or None

def get_finished( ob ):
    return ob.finished is not None and ob.finished.strftime(OUTPUT_DATE_TIME_FORMAT) or None

def myob_received( ob ):
    return ob.received is not None and ob.received.strftime(OUTPUT_DATE_FORMAT) or None

def myob_name( ob ):
    return '%s (%s)' % (ob.company.title, ob.branch.title)

def myob_item_number( ob ):
    if ob.IsArchive:
        return '191'
    elif ob.IsAmendment:
        return '190'
    else:
        return '19'

def myob_total( ob ):
    x = ob.calculated or ob.price or ob.default or decimal.Decimal('0.00')
    if ob.IsArchive and ob.IsAmendment:
        x = x + ob.amend_total
    elif ob.IsArchive:
        pass #x = ob.calculated or ob.price
    elif ob.IsAmendment:
        x = ob.amend_total
    return x
#
#   Field types: 0 - attribute, 1 - callable, 2 - value
#
FIELD_TITLE   = 0
FIELD_MODEL   = 1
FIELD_TYPE    = 2
FIELD_VALUE   = 3
FIELD_ORDER   = 4
FIELD_PK      = 5
FIELD_CHOICES = 6
#
# Report columns description: title, object, type, attr, order, pk, choices
#
MYOB_FIELDS_DESCRIPTION = {
    'date'       : ('Date',             None,   22,  None,             'A',  None,     None ), # myob_received
   #'received'   : ('received',         None,    1,  myob_received,    'A',  None,     None ),
    'branch'     : ('Co./Last Name',    None,    1,  myob_name,        'B',  None,     None ),
    'item_number': ('Item Number',      None,    1,  myob_item_number, 'C',  None,     None ),
    'quantity'   : ('Quantity',         MYOB,    2,  1,                'D',  None,     None ),
    'description': ('Description',      None,    0, 'title',           'E',  None,     None ),
    'total'      : ('Total',            None,    1,  myob_total,       'F',  None,     None ),
    'vat_code'   : ('VAT Code',         None,    2, 'S',               'G',  None,     None ),
    'job'        : ('Job',              User,    0, 'username',        'H', 'user',    None ),
}

MYOB_FIELDS_CHOICES = ( 
    'date', 'branch', 'item_number', 'quantity', 'description', 'total', 'vat_code', 'job',
)

CLIENT_FIELDS_DESCRIPTION = {
    'company'    : ('Company',          Company, 0,  'title',          'A', 'company', None ),
    'country'    : ('Country',          Country, 0,  'title',          'B', 'country', None ),
    'branch'     : ('Branch',           None,    0,  'title',          'C',  None,     None ),
    'type'       : ('Type',             None,    3,  'type',           'D',  None,     BRANCH_CHOICES ),
    'postcode'   : ('Postcode',         None,    0,  'postcode',       'E',  None,     None ),
    'city'       : ('City',             None,    0,  'city',           'F',  None,     None ),
    'address'    : ('Address',          None,    0,  'address',        'G',  None,     None ),
    'phone1'     : ('Phone1',           None,    0,  'phone1',         'H',  None,     None ),
    'phone2'     : ('Phone2',           None,    0,  'phone2',         'I',  None,     None ),
    'fax'        : ('Fax',              None,    0,  'fax',            'J',  None,     None ),
    'email'      : ('Email',            None,    0,  'email',          'K',  None,     None ),
    'notes'      : ('Notes',            None,    0,  'notes',          'L',  None,     None ),
}

choices = CLIENT_FIELDS_DESCRIPTION.items()
choices.sort( lambda x, y, item=FIELD_ORDER: cmp(x[1][item], y[1][item]) )
CLIENT_FIELDS_CHOICES = tuple([x[0] for x in choices])

JOB_FIELDS_DESCRIPTION = {
    'company'    : ('Company',          Company, 0,  'title',          'A', 'company', None ),
    'branch'     : ('Branch',           Branch,  0,  'title',          'B', 'branch',  None ),
    'contact'    : ('Contact',          Contact, 0,  'title',          'C', 'contact', None ),
    'status'     : ('Status',           Status,  0,  'title',          'D', 'status',  None ),
    'title'      : ('Property Address', None,    0,  'title',          'E',  None,     None ),
    'type'       : ('Type',             None,    3,  'type',           'F',  None,     PRICE_CHOICES ),
    'received'   : ('Received',         None,    1,   get_received,    'G',  None,     None ),
    'finished'   : ('Finished',         None,    1,   get_finished,    'H',  None,     None ),
    'property'   : ('Property',         None,    0,  'property',       'I',  None,     None ),
    'square'     : ('Square',           None,    0,  'square',         'J',  None,     None ),
    'default'    : ('Default Price',    None,    0,  'default',        'K',  None,     None ),
    'price'      : ('Plan Price',       None,    0,  'price',          'L',  None,     None ),
    'calculated' : ('Calculated',       None,    0,  'calculated',     'M',  None,     None ),
    'amendments' : ('Amendments',       None,    0,  'amendments',     'N',  None,     None ),
    'amend_total': ('AmendTotal',       None,    0,  'amend_total',    'O',  None,     None ),
    'runtime'    : ('Runtime',          None,    0,  'runtime',        'P',  None,     None ),
    'IsArchive'  : ('Archive',          None,    0,  'IsArchive',      'Q',  None,     None ),
    'drawn'      : ('Drawn by',         User,    0,  'username',       'C', 'user',    None ),
}

choices = JOB_FIELDS_DESCRIPTION.items()
choices.sort( lambda x, y, item=FIELD_ORDER: cmp(x[1][item], y[1][item]) )
JOB_FIELDS_CHOICES = tuple([x[0] for x in choices])

CLEAN_FIELDS_LIST = ('Description', 'Property Address',)

FORMAT_CHOICES = (
    ( 'txt',  "TXT (tabulated text)" ),
    ( 'csv1', "CSV (with semicolon)" ),
    ( 'csv2', "CSV (with comma)" ),
    ( 'xls',  "XLS (MS Excel)" ),
    #( 'json', "JSON" ),
    #( 'xml',  "XML" ),
)

def _get_datetime( s ):
    s = s.strip()
    match = re_datetime_format.match(s)
    if match is None:
        match = re_date_format.match(s)
        if match is None:
            return None
    args = tuple([x.isdigit() and int(x) or 0 for x in match.groups()])
    if IsDebug:
        print args
    return datetime.datetime(*args)

def _get_string( s, format, IsClean ):
    if IsClean:
        s = re.sub(r'(.*)\(.*\)', r'\1', s).strip()
    if format in ('txt', 'csv1', 'csv2'):
        return mark_safe(re.sub(ur'[\;\,\t\n]+', ur'', force_unicode(s)))
    return mark_safe(s)

def excel_workbook( rows, title, IsHeaders ):
    output = StringIO()
    wb = xlwt.Workbook()

    font0 = xlwt.Font()
    font0.name = 'Verdana'
    font0.height = 0x00C8 # size: 0x00A0-8 0x00B4-9 0x00C8-10
    font0.bold = True

    style0 = xlwt.XFStyle() # Headers style
    style0.font = font0

    font1 = xlwt.Font()
    font1.name = 'Verdana'
    font1.bold = False

    style1 = xlwt.XFStyle() # Cells style (default)
    style1.font = font1

    al = xlwt.Alignment()
    al.horz = xlwt.Formatting.Alignment.HORZ_RIGHT

    style2 = xlwt.XFStyle() # Cells style (alignment right)
    style2.font = font1
    style2.alignment = al

    ws = wb.add_sheet(title)
    for i, columns in enumerate(rows):
        for j, column in enumerate(columns):
            style = i==0 and style0 or style1
            ws.write(i, j, column, style)
    wb.save(output)
    output.seek(0)
    return output.read()

class ClientExportForm( forms.Form ):
    fields  = forms.MultipleChoiceField( choices=[(x, CLIENT_FIELDS_DESCRIPTION[x][FIELD_TITLE]) for x in CLIENT_FIELDS_CHOICES], 
        widget=CheckboxList(extra_attrs={'checked':1}) 
    )

class JobExportForm( forms.Form ):
    fields  = forms.MultipleChoiceField( choices=[(x, JOB_FIELDS_DESCRIPTION[x][FIELD_TITLE]) for x in JOB_FIELDS_CHOICES], 
        widget=CheckboxList(extra_attrs={'checked':1}) 
    )

class MYOBExportForm( forms.Form ):
    #
    # MYOB Export HTML-form model
    #
    start   = forms.SplitDateTimeField( required=False, widget=AdminSplitDateTime() )
    finish  = forms.SplitDateTimeField( required=False, widget=AdminSplitDateTime() )
    month   = forms.CharField( widget=SelectMonthWidget(), initial=datetime.datetime.now() )
    report  = forms.IntegerField( widget=forms.Select( choices=REPORT_CHOICES ), initial=0 )
    fields  = forms.MultipleChoiceField( choices=[(x, MYOB_FIELDS_DESCRIPTION[x][FIELD_TITLE]) for x in MYOB_FIELDS_CHOICES], 
        widget=CheckboxList(extra_attrs={'checked':1}) 
    )
    format  = forms.ChoiceField( choices=FORMAT_CHOICES, widget=forms.Select(attrs={'class':'mono'}), initial='xls' )
    headers = forms.IntegerField( widget=forms.CheckboxInput(), initial=1 )
    clean = forms.IntegerField( widget=forms.CheckboxInput(), initial=0 )

class ExcelReport( object ):
    """
        Create and Export excel-based report 
    """
    def __init__( self, report=None, format=None ):
        self.report = report or 'myob'
        self.format = format or 'csv'

    def __repr__( self ):
        return "%s.%s" % (self.report, self.format)

    def __call__( self, request, *args, **kwargs ):
        #
        # Main method that does all the hard work, conforming to the Django view interface
        # 
        if request.POST.getlist('fields'):
            return self.done( request )
        return self.render(request)

    def render( self, request, context=None ):
        "Renders the given Form object, returning an HttpResponse."
        if IsDebug:
            print "render: %s" % step

        context = context or {}
        context_instance = RequestContext(request)

        if 'loader' in context:
            template = 'forms/report-columns.html'
            id = int(request.GET.get('id', None) or '0')
        else:
            template = self.get_template()
            id = None

        if id == 2:
            form = JobExportForm()
        elif id == 1:
            form = ClientExportForm()
        else:
            form = MYOBExportForm()

        response = dict(context,
            form=form,
            label_width='190px',
            media=self.media,
            )

        if IsDebug:
            print "OK"
        return render_to_response(template, response, context_instance=context_instance)

    def done( self, request ):
        #
        # Format and requested dates period
        #
        format = request.POST.get('format') or self.format
        period = int(request.POST.get('period', 0))

        if not period:
            start = _get_datetime('%s %s' % ( \
                request.POST.get('start_0', '').strip(), (request.POST.get('start_1', '').strip() or '00:00:00'),)
                )
            finish = _get_datetime('%s %s' % ( \
                request.POST.get('finish_0', '').strip(), (request.POST.get('finish_1', '').strip() or '23:59:59'),)
                )
            if start >= finish:
                raise 1
        else:
            month = int(request.POST.get('month_month'))
            year = int(request.POST.get('month_year'))
            if month == 0:
                raise 1
            start = datetime.datetime(year, month, 1, 0, 0, 0)
            x = month == 12 and datetime.datetime(year+1, 1, 1, 23, 59, 59) or datetime.datetime(year, month+1, 1, 23, 59, 59)
            finish = x - datetime.timedelta(1)

        fields = request.POST.getlist('fields')
        if not fields:
            raise 1

        context = RequestContext(request)
        context['args'] = { \
                'period': period,
                'start' : start,
                'finish': finish,
                'fields': fields,
                'format': format,
            }
        #
        # Report type
        #
        report = int(request.POST.get('report') or '0')
        output_start = start.strftime(OUTPUT_DATE_FORMAT)
        output_finish = finish.strftime(OUTPUT_DATE_FORMAT)
        rows = []
        #
        # Data Query set
        #
        if report == 2:
            qset = ( Q(received__gte=start) & Q(received__lte=finish) )
            res = Job.objects.filter(qset).order_by('received')
            fields_description = JOB_FIELDS_DESCRIPTION
            headers = JOB_FIELDS_CHOICES
            self.report = 'job'
        elif report == 1:
            qset = ( Q(RD__gte=start) & Q(RD__lte=finish) )
            res = Branch.objects.filter(qset).order_by('RD')
            fields_description = CLIENT_FIELDS_DESCRIPTION
            headers = CLIENT_FIELDS_CHOICES
            self.report = 'client'
        else:
            qset = ( Q(received__gte=start) & Q(received__lte=finish) )
            res = Job.objects.filter(qset).order_by('company__title', 'branch__title', 'received')
            fields_description = MYOB_FIELDS_DESCRIPTION
            headers = MYOB_FIELDS_CHOICES
            self.report = 'myob'

        l = len(res)

        if request.POST.get('headers') == 'on':
            rows.append(tuple([fields_description[x][FIELD_TITLE] for x in headers if x in fields]))
            IsHeaders = 1
        else:
            IsHeaders = 0

        IsClean = request.POST.get('clean') == 'on' and 1 or 0
        branch = None

        for source in res:
            columns = []
            #
            #   Print rows delimeter
            #
            if report == 0:
                if source.branch != branch:
                    rows.append([''])
                    branch = source.branch
            #
            #   Print row
            #
            for key in fields:
                title, ob, typ, attr, order, pk, choices = fields_description[key]
                if ob is None:
                    ob = source
                elif pk is not None:
                    #
                    # Reference
                    #
                    x = getattr(source, pk, None)
                    if x is not None:
                        ob = ob.objects.get(pk=x.id)
                    else:
                        typ, attr = 2, None
                #
                # Attrubute reading and validation
                #
                if typ == 3 and choices:
                    #
                    # Choices field value
                    #
                    value = getattr(ob, attr, None)
                    for x in choices:
                        if x[0] == value:
                            value = x[1]
                            break
                elif typ == 2:
                    #
                    # Simple value from description
                    #
                    value = attr
                elif typ == 22:
                    #
                    # Finish date
                    #
                    value = output_finish
                elif typ == 21:
                    #
                    # Start date
                    #
                    value = output_start
                elif typ == 1:
                    #
                    # Callable attribute (a local function with 'ob' as the first argument)
                    #
                    if attr is not None:
                        value = attr(ob)
                    else:
                        value = None
                else:
                    #
                    # Attribute as given source's property (maybe missing)
                    #
                    value = getattr(ob, attr, None)
                    if callable(value):
                        value = value()
                #
                # Rendering output value
                #
                if value is None:
                    value = ''
                elif isinstance(value, basestring):
                    value = _get_string(value, format, IsClean=(IsClean and title in CLEAN_FIELDS_LIST and 1 or 0))
                #elif type(value) is datetime.datetime:
                #    value = str(value)

                columns.append(value)

            rows.append(columns)

        if 'template' in ALLOWED_EXPORT_TYPES[format]:
            context['rows'] = rows
            context['delimeter'] = ALLOWED_EXPORT_TYPES[format]['delimeter']
            context['newline'] = ALLOWED_EXPORT_TYPES[format]['newline']
            t = loader.get_template(ALLOWED_EXPORT_TYPES[format]['template'])
            responseContents = t.render(context)
        elif 'output' in ALLOWED_EXPORT_TYPES[format]:
            responseContents = excel_workbook(rows, self.report+'s', IsHeaders)
        elif 'serializer' in ALLOWED_EXPORT_TYPES[format]:
            responseContents = serialize(ALLOWED_EXPORT_TYPES[format]['serializer'], rows)
        else:
            raise Http404('Export type for %s must have value for template or serializer' % format)

        response = HttpResponse(responseContents, mimetype=ALLOWED_EXPORT_TYPES[format]['mimetype'])
        response['Content-Disposition'] = 'attachment; filename=%s' % (ALLOWED_EXPORT_TYPES[format]['filename'] % slugify(self.report))

        del source

        return response

    def get_template( self ):
        return 'forms/reporting.html'

    def _media( self ):
        js = ['js/calendar.js', 'js/admin/DateTimeShortcuts.js', 'js/report.updater.js']
        #css = ['css/forms.css']
        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js],
                           #css={'all': tuple(['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in css])}
                           )
    media = property(_media)
