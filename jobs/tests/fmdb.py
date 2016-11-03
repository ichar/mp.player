#!/usr/bin/env python
#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# FilerMaker DB Source Data Importing (fmdb.py).
#
# Checked: 2010/05/16
# ichar@g2.ru
#
import re
import sys
import random
import datetime
import decimal

from django.conf import settings
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.encoding import force_unicode, smart_str

from jobs.models import Company, Branch, Contact, Job, BRANCH_CHOICES, SALUTATION_CHOICES, PRICE_CHOICES, _get_phone, _get_email, _get_datetime
from references.models import Country, Department, Status, PayStructure, MYOB, PAY_CHOICES
from utils import print_traceback

IsDeepTrace = 1
IsDebug = 0

def _test():
    print 1

if __name__ == "__main__":
    _test()

SOURCE_PATH      = settings.APP_PATH
LOCATION         = '/tmp/'
CLIENTS          = 'client-details'
JOBS             = 'job-details'
EXT              = 'txt'
FIELD_DELIMETER  = "\t"
NEWLINE          = "\r\n"
OUT_NEWLINE      = '|newline|'
RE_NEWLINE       = r'\|newline\|'

"""
    Data Import Settings
    --------------------
"""
#
#   FMDB Fields correspondence: 
#       0 -- <class> - associated DB class
#       1 -- <field> - field name
#       2 -- <type> - source field type
#       3 -- <delimeter> - field parts delimeter
#       4 -- <choices> - 'choices' attribute
#       5 -- <code> - field's setup code
#       6 -- <FK> - foreign key: (<primary class>, <value field>)
#
CLIENTS_FILEDS_MAPPING = {
    'Account Number'      : ( MYOB,         'myobaccount',   '', ),
    'Address1'            : ( Branch,       'address',       'text', '\n', ),
    'Address2'            : ( Branch,       'address',       'text', '\n', ),
    'Address3'            : ( Branch,       'address',       'text', '\n', ),
    'Branch'              : ( Branch,       'title',         '',     ': ',  ),
    'City'                : ( Branch,       'city',          '', ),
    'Code'                : ( Branch,       'code',          '', ),
    'Company Name'        : ( Company,      'title',         '', ),
    'Contact'             : ( Contact,      'name',          '', ),
    'Contact Phone'       : ( Contact,      'phone',         'phone', ),
    'County'              : ( Country,      'title',         '', ),
    'Departments'         : ( Department,   'title',         '', ),
    'Email'               : ( Contact,      'email',         'email', '; ', ),
    'Fax Number'          : ( Branch,       'fax',           'phone', ),
    'Fixed Fee'           : ( PayStructure, 'fixed_fee',     'price', ),
    'Main Phone'          : ( Branch,       'phone1',        'phone', ),
    'Manager  Forename 1' : ( Contact,      'name',          '', ' ', ),
    'Manager  Forename 2' : ( Contact,      'name',          '', ' ', ),
    'Manager Surname 1'   : ( Contact,      'name',          '', ' ', ),
    'Manager Surname 2'   : ( Contact,      'name',          '', ' ', ),
    'Manager Title 1'     : ( Contact,      'salutation',    'choice', None, SALUTATION_CHOICES, "setattr(ob, 'IsManager', 1)", ),
    'Manager Title 2'     : ( Contact,      'salutation',    'choice', None, SALUTATION_CHOICES, "setattr(ob, 'IsManager', 1)", ),
    'Max 10th'            : ( PayStructure, 'max10',         'price', ),
    'Max 1st'             : ( PayStructure, 'max1',          'price', ),
    'Max 2nd'             : ( PayStructure, 'max2',          'price', ),
    'Max 3rd'             : ( PayStructure, 'max3',          'price', ),
    'Max 4th'             : ( PayStructure, 'max4',          'price', ),
    'Max 5th'             : ( PayStructure, 'max5',          'price', ),
    'Max 6th'             : ( PayStructure, 'max6',          'price', ),
    'Max 7th'             : ( PayStructure, 'max7',          'price', ),
    'Max 8th'             : ( PayStructure, 'max8',          'price', ),
    'Max 9th'             : ( PayStructure, 'max9',          'price', ),
    'MYOB Company Name'   : ( MYOB,         'myobcompany',   '', ),
    'MYOB Quantity'       : ( MYOB,         'myobquantity',  'int',   ),
    'Notes'               : ( Branch,       'notes',         'text',  ),
    'Pay type'            : ( PayStructure, 'type',          'choice', None, PAY_CHOICES, ),
    'Postcode'            : ( Branch,       'postcode',      '', ),
    'Price Bracket 10'    : ( PayStructure, 'price10',       'price', ),
    'Price Bracket 2'     : ( PayStructure, 'price2',        'price', ),
    'Price Bracket 3'     : ( PayStructure, 'price3',        'price', ),
    'Price Bracket 4'     : ( PayStructure, 'price4',        'price', ),
    'Price Bracket 5'     : ( PayStructure, 'price5',        'price', ),
    'Price Bracket 6'     : ( PayStructure, 'price6',        'price', ),
    'Price Bracket 7'     : ( PayStructure, 'price7',        'price', ),
    'Price Bracket 8'     : ( PayStructure, 'price8',        'price', ),
    'Price Bracket 9'     : ( PayStructure, 'price9',        'price', ),
    'Type'                : ( Branch,       'type',          'choice', None, BRANCH_CHOICES, ),
    'VAT Code MYOB'       : ( MYOB,         'myobvat',       '', ),
}

JOBS_FILEDS_MAPPING = {
    'Amendments'          : ( PayStructure, 'amendments',    'int',    None, None, "rendered_value and setattr(ob, 'IsAmendment', 1)", ),
    'AmendTotal'          : ( Job,          'amend_total',   'price', ),
    'Archive'             : ( Job,          'IsArchive',     'boolean', ),
    'Branch'              : ( Branch,       'title',         '', ),
    'Calculated Price'    : ( Job,          'calculated',    'price', ),
    'Client'              : ( Company,      'title',         '', ),
    'Code'                : ( Branch,       'code',          '', ),
    'Contact'             : ( Contact,      'title',         '', ),
    'Date Entered'        : ( Job,          'received',      'date', ),
    'Date Finished'       : ( Job,          'finished',      'date', ),
    'Drawn?'              : ( User,         'username',      '', ),
    'Price'               : ( Job,          'price',         'price', ),
    'Property Address'    : ( Job,          'title',         '', ),
    'Property Area'       : ( Job,          'square',        '', ),
    'Property Value'      : ( Job,          'property',      'price', ),
    'Status'              : ( Status,       'title',         '', ),
    'Time'                : ( Job,          'received',      'time', ' ', ),
}

OBJECT_IDENTIFIERS = ('Code', 'Fax Number', 'Main Phone', 'Email', 'Contact', 'Drawn?', 'Property Address', 'Postcode', 
                      'County', 'Company Name', 'Branch', 'Departments', 'Status',
                      'Client')

VALIDATION_RULES = {
    PayStructure : (
        ( "not ob.title.startswith('PS') and setattr(ob, 'title', 'PS: %s' % ob.title)", 1, ),
    ),
    MYOB : (
        ( "not ob.title.startswith('MYOB') and setattr(ob, 'title', 'MYOB: %s' % ob.title)", 1, ),
        ( "setattr(ob, 'myobvat', ob.myobvat.upper())", 1, ),
    ),
    Branch : (
        ( "not ob.title and setattr(ob, 'title', 'Head Office') or ob.title == 'Head Office' and setattr(ob, 'IsHeadOffice', 1)", 1 ),
    ),
    Contact : (
        ( "not ob.title and ob.name and setattr(ob, 'title', ob.name)", 2, ),
    ),
    User : (
        ( "setattr(ob, 'title', ob.username)", 1, ),
        ( "setattr(ob, 'is_staff', 1)", 1, ), 
    ),
    Job : (
        ( "setattr(ob, 'received', _get_datetime(ob.received))", 1, ),
        ( "setattr(ob, 'RD', ob.received)", 1, ),
    ),
}

STACKED_ATTRS = {
    'address'  : ( Branch,  ),
    'name'     : ( Contact, ),
    'notes'    : ( Branch,  ),
    'title'    : ( PayStructure, MYOB, ),
    'phone'    : ( Contact, ),
    'email'    : ( Contact, ),
    'received' : ( Job, ),
}

DEFAULTS = (
   (Country, 'title', 'UK'), 
   (Department, 'title', 'London'), 
   (Status, 'title', 'Pending'),
)

IMPORT_SCENARIO = (
   ('Country',      CLIENTS, Country,      ('County#1',),        (), ),
   #('Department',   CLIENTS, Department,   ('Departments#1',),   (), ),
   #('Status',       JOBS,    Status,       ('Status#1',),        (), ),
   # ------------ #
   ('Company',      CLIENTS, Company,      ('Company Name#1',),  ( ('County', Country, 'country', 'UK',), ), ),
   # ------------ #
   ('PayStructure', CLIENTS, PayStructure, ( \
                                            'Code#1', 
                                            'Company Name', 
                                            'Branch', 
                                            'Pay type', 
                                            'Fixed Fee', 
                                            'startswith:Price Bracket', 
                                            'startswith:Max', 
                                           ),                  (), ),
   ('MYOB',         CLIENTS, MYOB,         ( \
                                            'Code#1', 
                                            'Company Name', 
                                            'Branch', 
                                            'contains:MYOB', 
                                           ),                  (), ),
   # ------------ #
   ('Branch',       CLIENTS, Branch,       ( \
                                            'Code#1', 
                                            'Postcode', 
                                            'Main Phone', 
                                            'Fax Number', 
                                            'Email', 
                                            'startswith:Address', 
                                            'Departments', 
                                            'Branch', 
                                            'Type', 
                                            'City', 
                                            'Notes', 
                                           ),
                          ( \
                            ('Company Name', Company,      'company',    '',       ), 
                            ('County',       Country,      'country',    'UK',     ), 
                            ('Departments',  Department,   'department', 'London', ), 
                            ('Code',         MYOB,         'account',    '',       ), 
                            ('Code',         PayStructure, 'pay',        '',       ), 
                          ),
        ),
   # ------------ #
   #('Contact',      CLIENTS, Contact,      ('Contact#1', 'Contact Phone', 'Email#1', ),
   #                       ( \
   #                         ('Company Name', Company, 'company', '', ),
   #                         ('Code',         Branch,  'branch',  '', ),
   #                       ),
   #     ),
   #('Contact-1',    CLIENTS, Contact,      ('Manager  Forename 1', 'Manager Surname 1', 'Manager Title 1', ),
   #                       ( \
   #                         ('Company Name', Company, 'company', '', ),
   #                         ('Code',         Branch,  'branch',  '', ),
   #                       ),
   #     ),
   #('Contact-2',    CLIENTS, Contact,      ('Manager  Forename 2', 'Manager Surname 2', 'Manager Title 2', ),
   #                       ( \
   #                         ('Company Name', Company, 'company', '', ),
   #                         ('Code',         Branch,  'branch',  '', ),
   #                       ),
   #     ),
   # ------------ # 
   #('User',         JOBS,    User,         ('Drawn?#1', ),       (), ),
   # ------------ # 
   #('Job-Company',  JOBS,    Company,      ('Client#1', ),
   #                       ( \
   #                         ( None,          Country,      'country',    'UK', ), 
   #                       ), 
   #     ),
   #('Job-Branch',   JOBS,    Branch,       ( \
   #                                         'Code#1', 
   #                                         'Branch', 
   #                                        ), 
   #                       ( \
   #                         ('Client',       Company,      'company',    '',   ), 
   #                         ( None,          Country,      'country',    'UK', ),
   #                       ),
   #     ),
   ('Job-Contact',  JOBS,    Contact,      ('Contact#1', ), 
                          ( \
                            ('Client',       Company,      'company',    '', ),
                            ('Code',         Branch,       'branch',     '', ),
                          ),
        ),
   # ------------ # 
   ('Job',          JOBS,    Job,          ( \
                                            'Property Address', 
                                            'Calculated Price', 
                                            'Price', 
                                            'Date Entered', 
                                            'Time', 
                                            'Date Finished', 
                                            'Property Area', 
                                            'Property Value', 
                                            'AmendTotal', 
                                            'Amendments', 
                                            'Archive', 
                                           ),
                          ( \
                            ('Client',       Company,      'company',    '', ), 
                            ('Code',         Branch,       'branch',     '', ), 
                            ('Contact',      Contact,      'contact',    '', ), 
                            ('Status',       Status,       'status',     '', ), 
                            ('Drawn?',       User,         'user',       '', ), 
                          ),
        ),
)

"""
    Decoder Implementation
    ----------------------
"""

def rstrip_line( s ):
    #if not mode:
    #    return re.sub(r'(\r\n)+', '', s)
    return re.sub(r'[\r\n]+', '', s)

def decode_string( s ):
    s = re.sub(r'[\xff]+', ' ', s)
    s = re.sub(r'[\x92]+', "'", s)
    s = re.sub(r'[\xa0]+', ' ', s)
    s = re.sub(r'[\x94]+', "'", s)
    s = re.sub(r'[\x85]+', '', s)
    return force_unicode(s.strip())

def convertor( mode, count=None, IsTrace=None, rows_only=None ):
    fin = file('%s%s%s.%s' % (SOURCE_PATH, LOCATION, mode, EXT), 'rb')
    fout = file('%s%s%s-converted.%s' % (SOURCE_PATH, LOCATION, mode, EXT), 'w')
    n = 0
    line = ''
    IsContinue = 0
    for s in fin:
        if not IsContinue:
            if s and not s.strip():
                continue
            if not s:
                break
        if s and not s.endswith(NEWLINE):
            line = line + rstrip_line(s) + OUT_NEWLINE
            IsContinue = 1
            continue
        else:
            IsContinue = 0
            line += s[0:len(s)-len(NEWLINE)]
        if count and n >= count:
            break
        columns = line.split(FIELD_DELIMETER)
        output = ''
        for i, x in enumerate(columns):
            if x.find(OUT_NEWLINE) > -1:
                x = re.sub(r'^"(.*)"$', r'\1', x)
            output += decode_string(x)
            if i < len(columns) - 1:
                 output += FIELD_DELIMETER
        output = '%05d:%s\n' % (n, output)
        fout.write(output)
        if IsTrace:
            if rows_only and n not in rows_only:
                pass
            else:
                print '--> %s' % repr(line)
                print '--> %s' % str(columns)
                print '--> %s' % len(columns)
                print '--> %s' % repr(output)
        line = ''
        n += 1
    fout.close()
    fin.close()

def clients( count=None, IsTrace=None, rows_only=None ):
    #
    #   Arguments:
    #       count     -- exported records count
    #       IsTrace   -- trace mode
    #       rows_only -- list of row numbers to export
    #
    #   Usage: fmdb.clients()
    #
    convertor( CLIENTS, count, IsTrace, rows_only )

def jobs( count=None, IsTrace=None, rows_only=None ):
    #
    #   Arguments:
    #       count     -- exported records count
    #       IsTrace   -- trace mode
    #       rows_only -- list of row numbers to export
    #
    #   Usage: fmdb.jobs()
    #
    convertor( JOBS, count, IsTrace, rows_only )

""" 
    Database Import Implementation
    ------------------------------
"""

def get_line( fin ):
    s = fin.readline()
    if not s:
        return (0, None,)
    sn = s[0:5]
    sline = rstrip_line(s[6:])
    return (sn, sline,)

def get_values( mode, mask, columns, values ):
    attrs = []
    if mask:
        if mode == CLIENTS:
            field_mappings = CLIENTS_FILEDS_MAPPING
        else:
            field_mappings = JOBS_FILEDS_MAPPING
        if '#' in mask:
            key, unique = mask.split('#')
            unique = bool(unique)
        else:
            key = mask
            unique = False
        if ':' in key:
            action, keyword = key.split(':')
            if action == 'startswith':
                attrs.extend([x for x in field_mappings.keys() if x.startswith(keyword)])
            elif action == 'contains':
                attrs.extend([x for x in field_mappings.keys() if keyword in x])
            elif action == 'endswith':
                attrs.extend([x for x in field_mappings.keys() if x.endswith(keyword)])
        else:
            attrs.append(key)

        for i, column_name in enumerate(columns):
            if column_name in attrs:
                value = values[i]
                yield (column_name, value, unique)
    else:
        yield (None, None, None)

def get_mapping( mode, column_name, attr=None ):
    res = None
    if mode == CLIENTS:
        field_mappings = CLIENTS_FILEDS_MAPPING
    else:
        field_mappings = JOBS_FILEDS_MAPPING
    #
    # Get Fields Mapping attribute value
    #
    if column_name in field_mappings:
        res = field_mappings[column_name]
        lm = len(res)
        if not lm or not attr:
            pass
        elif attr == 'class':
            res = res[0] 
        elif attr == 'field':
            res = lm >= 2 and res[1]
        elif attr == 'type':
            res = lm >= 3 and res[2]
        elif attr == 'delimeter':
            res = lm >= 4 and res[3]
        elif attr == 'choices':
            res = lm >= 5 and res[4]
        elif attr == 'code':
            res = lm >= 6 and res[5]
        elif attr == 'FK':
            res = lm >= 7 and res[6]
    if IsDebug and IsDeepTrace:
        print '--> mapping[%s]: %s=[%s], mode:%s' % (attr, column_name, res, mode)
    return res

class dbo(object):
    #
    #   New Database Abstract Object
    #
    def __init__( self, mode, klass, IsTrace=None ):
        self.ob = None
        self.mode = mode
        self.klass = klass
        self.IsTrace = IsTrace
        self.attrs = []
        self.is_attr = False
        self.is_changed = False

    def has_object( self ):
        return self.ob is not None and True or False

    def has_attrs( self ):
        return ( self.is_attr or self.attrs ) and True or False

    def init_default( self ):
        if self.ob is not None:
            return
        ob = apply(self.klass)
        setattr(ob, 'title', '')
        setattr(ob, 'RD', datetime.datetime.now())
        self.is_changed = True
        self.ob = ob

    def init_object_by_fieldname( self, column_name, value, unique, default=None ):
        #
        # Find existing DB Object
        #
        if self.ob is not None:
            self.set_object_attr(column_name, value)
        elif unique and column_name in OBJECT_IDENTIFIERS:
            attr = get_mapping(self.mode, column_name, 'field')
            if not attr:
                if self.IsTrace and IsDebug:
                    print "--> No 'field' attribute: %s (init_object_by_fieldname)" % column_name
                raise
            if self.ob is None:
                rendered_value = self.render_value(column_name, value, default='')
                if rendered_value:
                    kw = { attr:rendered_value }
                    res = self.klass.objects.filter(**kw)
                    if res and len(res) > 0:
                        self.ob = res[0]
                        if self.IsTrace and IsDebug:
                            print '--> DBO: %s, column:%s[%s], count:%s' % (repr(self.ob), column_name, rendered_value, len(res))
                        return
        #
        # If not, save an attribute value to change later
        #
        if self.ob is None:
            self.attrs.append(( column_name, value, default, ))

    def set_object_attr( self, column_name, value, default=None ):
        attr = get_mapping(self.mode, column_name, 'field')
        if not attr:
            if self.IsTrace and IsDebug:
                print "--> No 'field' attribute: %s (set_object_attr)" % column_name
            raise
        #
        # Rendered value
        #
        rendered_value = self.render_value(column_name, value, default)
        #
        # Set attribute value
        #
        o = str(getattr(self.ob, attr, None) or '')
        n = str(rendered_value or '')
        if n and o != n:
            if o and attr in STACKED_ATTRS and self.klass in STACKED_ATTRS[attr]:
                if n not in o:
                    delimeter = get_mapping(self.mode, column_name, 'delimeter') or ' '
                    rendered_value = o + delimeter + n
                else:
                    return
            setattr(self.ob, attr, rendered_value)
            self.is_changed = True
        code = get_mapping(self.mode, column_name, 'code')
        if code:
            ob = self.ob
            eval(code)
        self.is_attr = True

    def render_value( self, column_name, value, default=None ):
        if not column_name or value is None:
            return None
        #
        # Data source type
        #
        source_type = get_mapping(self.mode, column_name, 'type')
        #
        # Check the type and render value
        #
        if not source_type or source_type == 'string':
            rendered_value = (re.sub(RE_NEWLINE, ' ', value)).strip()
        elif source_type == 'text':
            rendered_value = re.sub(RE_NEWLINE, r'\n', value)
        elif source_type == 'boolean':
            rendered_value = value and True or False
        elif source_type == 'int':
            rendered_value = value and value.isdigit() and int(value) or 0
        elif source_type == 'choice':
            choices = get_mapping(self.mode, column_name, 'choices')
            rendered_value = 0
            if choices and value:
                for i, v in choices:
                    if value.lower() == v.lower():
                        rendered_value = i
                        break
        elif source_type == 'price':
            try:
                rendered_value = value and decimal.Decimal(value) or 0
            except:
                rendered_value = 0
        elif source_type == 'date':
            try:
                d, m, y = value.split('.')
                rendered_value = datetime.date(int(y),int(m),int(d))
            except:
                if isinstance(value, basestring) and 'not completed' in value.lower():
                    pass
                elif self.IsTrace:
                    print '--> No Date: %s' % value
                rendered_value = None
            else:
                rendered_value = rendered_value.strftime(settings.DATE_FORMAT)
        elif source_type == 'time':
            try:
                h, m, s = value.split(':')
                rendered_value = datetime.time(int(h),int(m),int(s))
            except:
                if self.IsTrace:
                    print '--> No Time: %s' % value
                rendered_value = None
            else:
                rendered_value = rendered_value.strftime(settings.TIME_FORMAT)
        elif source_type == 'phone':
            rendered_value = _get_phone(value)
        elif source_type == 'email':
            rendered_value = ';'.join([x for x in _get_email(value, ',') if x])
        else:
            rendered_value = value or default
        if self.IsTrace and IsDebug:
            print '--> Rendered value[%s]: type:%s, value:%s' % (column_name, source_type, rendered_value)
        return rendered_value

    def set_ferignkey_value( self, column_name, reference, field, value, default=None ):
        self.init_default()
        #
        # Get Foreign Key attributes
        #
        attr = get_mapping(self.mode, column_name, 'FK')
        if not column_name:
            ferignkey_class = reference
            ferignkey_field = 'title'
        elif not attr:
            ferignkey_class = reference
            ferignkey_field = get_mapping(self.mode, column_name, 'field')
        else:
            ferignkey_class, ferignkey_field = attr
        #
        # Find linked DB Object (ROB)
        #
        rendered_value = self.render_value(column_name, value, default=None)
        kw = { ferignkey_field: (rendered_value or default) }
        ROB = None
        res = ferignkey_class.objects.filter(**kw)
        if res is not None and len(res) > 0:
            ROB = res[0]
        else:
            if self.IsTrace and IsDeepTrace:
                print '--> No Foreign Key item: %s %s %s %s' % (column_name, repr(ferignkey_class), field, value)
            return
        #
        # Get Given Object Primary Key
        #
        pk = ROB.pk
        if not pk:
            if self.IsTrace and IsDeepTrace:
                print '--> No PK: %s' % repr(ferignkey_class)
            return
        #
        # Set Foregn Key value
        #
        self.init_default()
        try:
            rob = getattr(self.ob, field, None)
        except:
            rob = None
        if rob is not None:
            if value:
                if getattr(rob, 'pk', None) == pk:
                    return
            elif default:
                #
                # For Default value rendering only. Object has valid reference
                #
                if getattr(rob, 'pk', None) is not None:
                    return
        setattr(self.ob, field, ROB)
        self.is_changed = True
        if self.IsTrace and IsDebug:
            print '--> New %s: %s=%s' % (repr(self.klass), field, pk)
        self.is_attr = True

    def save_object( self, IsTrace=None ):
        self.init_default()
        IsSaved = 0
        #
        # Set attribute values
        #
        for attr, value, default in self.attrs:
            self.set_object_attr(attr, value, default)
        #
        # Object forced validation
        #
        if self.klass in VALIDATION_RULES:
            ob = self.ob
            for code, is_save in VALIDATION_RULES[self.klass]:
                eval(code)
                if is_save == 1:
                    #
                    # Object was changed
                    #
                    self.is_changed = True
                elif is_save == 2:
                    #
                    # Identify the object by title repeatedly
                    #
                    if getattr(ob, 'title', None):
                        kw = { 'title':ob.title }
                        res = self.klass.objects.filter(**kw)
                        if res and len(res) > 0:
                            ob = res[0]
                            for x in self.ob.__dict__:
                                v = getattr(self.ob, x, None)
                                if v is not None and v != getattr(ob, x, None):
                                    setattr(ob, x, v)
                            self.ob = ob
                        self.is_changed = True
                else:
                    return
        if not getattr(self.ob, 'title', None):
            if self.IsTrace and IsDeepTrace:
                print '--> No title: %s' % repr(self.ob)
            return None
        #
        # Save DB Object
        #
        try:
            if self.is_changed:
                self.ob.save()
                if self.IsTrace and IsDebug:
                    print '--> Saved: %s' % repr(self.ob)
                IsSaved = 1
        except:
            print '!!! %s DB Exception: %s' % (self.klass.__name__, repr(self.ob))
            raise
        return IsSaved

def set_defaults():
    #
    #   This should be run once before new database importing.
    #   Usage: fmdb.set_defaults()
    #
    for klass, field, value in DEFAULTS:
        kw = { field:value }
        res = klass.objects.filter(**kw)
        if res and len(res) > 0:
            continue
        ob = apply(klass)
        setattr(ob, field, value)
        setattr(ob, 'RD', datetime.datetime.now())
        ob.save()

def run( IsTrace=None, steps=None ):
    #
    #   Arguments:
    #       IsTrace -- trace mode (integer, trace cycle's step)
    #       steps -- step name's list for import: ['Branch', ...].
    #
    #   Usage: fmdb.run()
    #
    flog = file('%s%slog.txt' % (SOURCE_PATH, LOCATION), 'a')
    
    for step, mode, klass, sfields, rfields in IMPORT_SCENARIO:
        if steps:
            if isinstance(steps, basestring):
                if not ( step == steps or step.startswith(steps) ):
                    continue
            elif step not in steps:
                continue
        print '--> %s: Started' % step
        #
        # Open Data Source input file
        #
        fin = file('%s%s%s-converted.%s' % (SOURCE_PATH, LOCATION, mode, EXT), 'rb')
        #
        # Data fields structure (headers)
        #
        sn, sline = get_line(fin)
        columns = sline.split(FIELD_DELIMETER)
        saved_objects = 0
        #
        # Source Data scanning
        #
        while 1:
            sn, sline = get_line(fin)
            if not sline:
                break
            if IsTrace and (int(sn)%IsTrace == 0):
                print '--> %s:%s' % (step, sn)
            #
            # New Object value
            #
            values = sline.split(FIELD_DELIMETER)
            ob = dbo(mode, klass, IsTrace)
            #
            # Simple fields list importing
            #
            for mask in sfields:
                for column_name, value, unique in get_values(mode, mask, columns, values):
                    if not value:
                        continue
                    elif not ob.has_object():
                        ob.init_object_by_fieldname(column_name, value, unique)
                    else:
                        ob.set_object_attr(column_name, value, default=None)
            #
            # Object is not identified
            #
            if not ob.has_object():
                if IsTrace and IsDebug:
                    print '--> No object: %s' % sn
            #
            # Foreign Key fields list importing
            #
            for mask, reference, field, default in rfields:
                for column_name, value, unique in get_values(mode, mask, columns, values):
                    if not value and not default:
                        continue
                    if IsTrace and IsDebug:
                        print '--> Reference: %s %s[%s] %s' % (column_name, reference, field, value)
                    ob.set_ferignkey_value(column_name, reference, field, value, default)

            if ob.has_attrs():
                try:
                    if ob.save_object( IsTrace ) == 1:
                        saved_objects += 1
                except Exception, msg:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    now = datetime.datetime.now().strftime(settings.DATE_FORMAT + ' ' + settings.TIME_FORMAT)
                    flog.write('%s %s[%s]: %s\n' % (now, exc_type, exc_value, str(msg)))
                    flog.write('class: %s, title: %s\n' % (repr(ob.klass), getattr(ob, 'title', None)))
                    if IsDebug:
                        flog.write(print_traceback(exc_traceback))
                        flog.write('\n')
                    flog.write('%s\n' % ('-'*40))
            else:
                if IsTrace and IsDebug:
                    print '--> No attributes'

            del ob
        #
        # Close Source Data input file
        #
        fin.close()
        #
        # Commit DB transaction
        #
        transaction.commit_unless_managed()

        print '--> %s: Finished. Total saved: %s' % (step, saved_objects)

    flog.close()

    print '--> OK'
