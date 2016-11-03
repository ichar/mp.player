#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
#
# Checked: 2016/10/12
# ichar@g2.ru
#
import re
import datetime
import settings
from string import lower

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils.html import urlize, escape, linebreaks, conditional_escape
#from django.utils.safestring import mark_safe
#from django.utils.encoding import force_unicode
#from django.contrib.admin.templatetags.admin_list import _boolean_icon
from references.templatetags.extras import _boolean_icon, _notes_icon

from references.models import *

YES_NO_CHOICES = ( ( 0, _('No'),), (1, _('Yes'),), ) 

BRANCH_CHOICES = (
    ( 0, 'Company' ),
    ( 1, 'Private' ),
    ( 2, 'Council' ),
    ( 3, 'Other'   ),
)

SALUTATION_CHOICES = (
    ( 0, 'Miss' ),
    ( 1, 'Mrs.' ),
    ( 2, 'Ms'   ),
    ( 3, 'Mr'   ),
    ( 4, ''     ),
)

PRICE_CHOICES = (
    ( 0, 'Fixed Price' ),
    ( 1, 'Variable price based upon the value of the property' ),
    ( 2, 'Variable price based upon area of property' ),
    ( 3, 'Manual Individual Price' ),
    ( 4, 'Other' ),
)

PHONE_MASK = '%d%d%d%d%d.%d%d%d.%d%d%d.%d%d%d%d%d%d%d%d%d'

def _get_phone( value, prefix=None ):
    if value[0] == '+':
        sign = value[:2] + ' '
        v = value[2:]
    else:
        sign = ''
        v = value
    v = [ int(x) for x in v.strip()[:20] if x != ' ' and x.isdigit() ]
    m = ''
    n = len(v)
    for i in range(len(PHONE_MASK)):
        x = PHONE_MASK[i]
        if n == 0:
            break
        if x not in (' ', '.', '-', '%',):
            n = n - 1
        m += x
    try:
        return '%s%s' % (prefix and prefix+':' or '', sign + (m % tuple(v)))
    except:
        return '%s%s' % (prefix and prefix+':' or '', value)

def _get_email( value, delimeter=';' ):
    return [re.sub(r'[\s]+', '', x) for x in value.split(delimeter) if x]

def _get_datetime( s ):
    if isinstance(s, basestring):
        r_date = re.compile(r'(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)')
        matched = r_date.search(s)
        if matched:
            g = matched.groups()
            x = datetime.datetime(int(g[0]), int(g[1]), int(g[2]), int(g[3]), int(g[4]), int(g[5]))
            return x
    return s

class Company( models.Model ):
    """
        *Company* fields set
    """
    country       = models.ForeignKey( Country )

    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1, unique=1 )
    name          = models.CharField( blank=1, default='', max_length=250 )
    code          = models.CharField( blank=1, null=1, max_length=40, db_index=1,
                        help_text="It's optional.",
                        )
    description   = models.TextField( blank=1 )

    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 ) # auto_now=True

    def __unicode__( self ):
        return '%s' % self.title or self.name or "..."

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    def rendered_name( self ):
        return self.name and "<nobr><span class=\"rendered_name\">%s</span></nobr>" % self.name or ''
    rendered_name.allow_tags = True
    rendered_name.short_description = _('Company Name')
    rendered_name.admin_order_field = 'name'

    def rendered_description( self ):
        return "%s" % linebreaks(self.description)
    rendered_description.allow_tags = True
    rendered_description.short_description = _('description')
    rendered_description.admin_order_field = 'description'

    def rendered_country( self ):
        html = """<span class=\"rendered_country\">%s</span>"""
        return self.country and html % self.country.title.strip() or ''
    rendered_country.allow_tags = True
    rendered_country.short_description = _('Country')
    rendered_country.admin_order_field = 'country'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

class Branch( models.Model ):
    """
        *Branch* fields set
    """
    company       = models.ForeignKey( Company, verbose_name=_("Company") )
    country       = models.ForeignKey( Country, verbose_name=_("Country"), blank=1, null=1 )
    department    = models.ForeignKey( Department, blank=1, null=1, default=None )
    account       = models.ForeignKey( MYOB, blank=1, null=1, default=None )
    pay           = models.ForeignKey( PayStructure, blank=1, null=1, default=None )

    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    code          = models.CharField( blank=1, null=1, max_length=40, db_index=1,
                        help_text="It's optional.",
                        )
    type          = models.IntegerField( default=0, db_index=1, 
                        choices=BRANCH_CHOICES,
                        )
    postcode      = models.CharField( blank=1, null=1, max_length=10 )
    city          = models.CharField( blank=1, null=1, max_length=50, db_index=1, default='', verbose_name=_("City") )
    address       = models.CharField( blank=1, null=1, max_length=250, db_index=1 )
    phone1        = models.CharField( blank=1, null=1, max_length=25 )
    phone2        = models.CharField( blank=1, null=1, max_length=25 )
    fax           = models.CharField( blank=1, null=1, max_length=20 )
    email         = models.EmailField( db_index=1, max_length=75,
                        help_text="We should define it before client will be served!",
                        )
    notes         = models.TextField( blank=1 )
    IsHeadOffice  = models.BooleanField( verbose_name=_("Company's Head Office (HO)"), 
                        db_column='IsHeadOffice' 
                        )

    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % ( self.title or "...", )

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("Company's Branch")
        verbose_name_plural = _("Company Branches (Client main Records)")

    def rendered_company( self ):
        html = """
<div class=\"rendered_company\">
<div><a title=\"company\" href=\"%(company_href)s\" class=\"rlink\" id=\"lookup_id_%(company_id)s\" onclick=\"return showRelatedObjectLookupPopup(this);\">%(company)s</a></div>
</div>
"""
        app_label = '../../%s' % self._meta.app_label
        return html % { 
            'company' : self.company, 'company_id' : self.company.id, 'company_href' : '%s/company/%s' % ( app_label, str(self.company.id) ),
            }
    rendered_company.allow_tags = True
    rendered_company.short_description = _("Client's Company")
    rendered_company.admin_order_field = 'company'

    def rendered_title( self ):
        html = """<span class=\"rendered_title\"><nobr>%s</nobr></span>"""
        return self.title and html % self.title.strip() or ''
    rendered_title.allow_tags = True
    rendered_title.short_description = _('Title')
    rendered_title.admin_order_field = 'title'

    def rendered_country( self ):
        html = """<span class=\"rendered_country\">%s</span>"""
        return self.country and html % self.country.title.strip() or ''
    rendered_country.allow_tags = True
    rendered_country.short_description = _('Country')
    rendered_country.admin_order_field = 'country'

    def rendered_city( self ):
        html = """<span class=\"rendered_city\">%s</span>"""
        return self.city and html % self.city.strip() or ''
    rendered_city.allow_tags = True
    rendered_city.short_description = _('City')
    rendered_city.admin_order_field = 'city'

    def rendered_code( self ):
        html = """<span class=\"rendered_code\"><nobr>%s</nobr></span>"""
        return self.code and html % self.code.strip() or ''
    rendered_code.allow_tags = True
    rendered_code.short_description = _('Code')
    rendered_code.admin_order_field = 'code'

    def rendered_phones( self ):
        if self.phone1 or self.phone2:
            html = """<div class="rendered_phone"><nobr>%s</nobr></div>"""
            return '<div>%s%s</div>' % ( \
                self.phone1 and html % _get_phone(self.phone1) or '',
                self.phone2 and html % _get_phone(self.phone2) or '',
            )
        else:
            return ''
    rendered_phones.allow_tags = True
    rendered_phones.short_description = _('Phones')
    rendered_phones.admin_order_field = 'phone1'

    def rendered_fax( self ):
        if self.fax:
            html = """<div class=\"rendered_fax\"><nobr>%s</nobr></div>"""
            return html % _get_phone(self.fax)
        else:
            return ''
    rendered_fax.allow_tags = True
    rendered_fax.short_description = _('Fax')
    rendered_fax.admin_order_field = 'fax'

    def rendered_email( self ):
        if self.email:
            html = """<div class=\"rendered_email\"><nobr>%s</nobr></div>"""
            return '<div>%s</div>' % ( \
                ''.join([html % x.strip() for x in _get_email(self.email)])
            )
        else:
            return ''
    rendered_email.allow_tags = True
    rendered_email.short_description = _('Email')
    rendered_email.admin_order_field = 'email'

    def rendered_HO( self ):
        return self.IsHeadOffice # _boolean_icon(self.IsHeadOffice)
    rendered_HO.boolean = True
    rendered_HO.allow_tags = True
    rendered_HO.short_description = _('HO')
    rendered_HO.admin_order_field = 'IsHeadOffice'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S<br>%a'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

    def flow_company( self ):
        html = """<a title=\"company\" href=\"%(company_href)s\" class=\"rlink\" id=\"lookup_id_%(company_id)s\" onclick=\"return showRelatedObjectLookupPopup(this);\">%(company)s</a>"""
        app_label = '../%s' % self._meta.app_label
        return html % { 
            'company' : self.company, 'company_id' : self.company.id, 'company_href' : '%s/company/%s' % ( app_label, str(self.company.id) ),
            }
    flow_company.allow_tags = True

    def flow_country( self ):
        return self.country or ''

    def flow_phones( self ):
        html = """<div class=\"rendered_phone\"><nobr>%s</nobr></div>"""
        return '%s' % ( \
                (self.phone1 and html % _get_phone(self.phone1, 'B')) or 
                (self.phone2 and ' ' + html % _get_phone(self.phone2, 'B')) or '',
            )
    flow_phones.allow_tags = True

class Contact( models.Model ):
    """
        *Contact* fields set
    """
    company       = models.ForeignKey( Company, verbose_name=_("Company") )
    branch        = models.ForeignKey( Branch, verbose_name=_("Branch"), blank=1, null=1, default=None )

    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    salutation    = models.IntegerField( blank=0, null=1, default=4,
                        choices=SALUTATION_CHOICES,
                        )
    name          = models.CharField( blank=1, null=1, max_length=50,
                        verbose_name=_("Brief Name")
                        )
    phone         = models.CharField( blank=1, null=1, max_length=200 )
    mobile        = models.CharField( blank=1, null=1, max_length=20 )
    email         = models.CharField( blank=1, null=1, db_index=1, max_length=250,
                        help_text="Email addresses list separated with ';'.",
                        )
    IsManager     = models.BooleanField( verbose_name=_("Office Manager (OM)"), 
                        db_column='IsManager' 
                        )
    notes         = models.TextField( blank=1 )

    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % ( self.title or self.name or "..." )

    def city( self ):
        return self.branch.city

    def country( self ):
        return self.branch.country

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("Client's Contact")
        verbose_name_plural = _("Contacts (Persons)")

    def rendered_branch( self ):
        has_branch = self.branch is not None and 1 or 0
        html = """
<div class=\"rendered_branch\">
<div><a title=\"company\" href=\"%(company_href)s\" class=\"rlink\" id=\"lookup_id_%(company_id)s\" onclick=\"return showRelatedObjectLookupPopup(this);\"><nobr>%(company)s</nobr></a></div>
<div class="bordered">%(branch_href)s</div>
</div>
"""
        app_label = '../../%s' % self._meta.app_label
        if has_branch:
            branch_href = '<a title="branch" href="%s/branch/%s" class="rlink" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);">%s</a>' % ( \
                    app_label, str(self.branch.id), self.branch_id, self.branch,
                )
        else:
            branch_href = '<span class="rendered_none">---</span>'
        options = { 
            'company'      : self.company,
            'company_id'   : self.company.id,
            'company_href' : '%s/company/%s' % (app_label, str(self.company.id)),
            'branch'       : has_branch and self.branch or '',
            'branch_id'    : has_branch and self.branch.id or '',
            'branch_href'  : branch_href,
        }
        return html % options
    rendered_branch.allow_tags = True
    rendered_branch.short_description = _("Client's Company & Branch")
    rendered_branch.admin_order_field = 'company'

    def rendered_salutation( self ):
        return "%s" % SALUTATION_CHOICES[ self.salutation ][ 1 ]
    rendered_salutation.short_description = _('Sl.')
    rendered_salutation.admin_order_field = 'salutation'

    def rendered_title( self ):
        html = """<span class=\"rendered_title\"><nobr>%s</nobr></span>"""
        return self.title and html % self.title.strip() or ''
    rendered_title.allow_tags = True
    rendered_title.short_description = _('Title (Person Name)')
    rendered_title.admin_order_field = 'title'

    def rendered_city( self ):
        html = """<span class=\"rendered_city\">%s</span>"""
        return self.branch is not None and self.branch.city and html % self.branch.city.strip() or ''
    rendered_city.allow_tags = True
    rendered_city.short_description = _('City')

    def rendered_phone( self ):
        if self.phone:
            phones = self.phone.replace(';',',').split(',')
            html = """<div class=\"rendered_phone\"><nobr>%s</nobr></div>"""
            return '<div>%s</div>' % ( \
                ''.join([html % _get_phone(x.strip()) for x in phones])
            )
        else:
            return ''
    rendered_phone.allow_tags = True
    rendered_phone.short_description = _('Phone')
    rendered_phone.admin_order_field = 'phone'

    def rendered_mobile( self ):
        if self.mobile:
            html = """<div class=\"rendered_mobile\"><nobr>%s</nobr></div>"""
            return html % _get_phone(escape(self.mobile))
        else:
            return ''
    rendered_mobile.allow_tags = True
    rendered_mobile.short_description = _('Mobile')
    rendered_mobile.admin_order_field = 'mobile'

    def rendered_email( self ):
        if self.email:
            html = """<div class=\"rendered_email\"><nobr>%s</nobr></div>"""
            return '<div>%s</div>' % ( \
                ''.join([html % x.strip() for x in _get_email(self.email)])
            )
        else:
            return ''
    rendered_email.allow_tags = True
    rendered_email.short_description = _('Email')
    rendered_email.admin_order_field = 'email'

    def rendered_OM( self ):
        return self.IsManager
    rendered_OM.boolean = True
    rendered_OM.allow_tags = True
    rendered_OM.short_description = _('OM')
    rendered_OM.admin_order_field = 'IsManager'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S'<br>%a
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

class Job( models.Model ):
    """
        *Job* fields set
    """
    company       = models.ForeignKey( Company, verbose_name=_("Company") )
    branch        = models.ForeignKey( Branch, verbose_name=_("Branch") )
    contact       = models.ForeignKey( Contact, verbose_name=_("Contact"), blank=1, null=1, default=None )
    status        = models.ForeignKey( Status, verbose_name=_("Status"), default=settings.DEFAULT_STATUS_ID )
    user          = models.ForeignKey( User, verbose_name=_("Drawn"), blank=1, null=1, default=None )

    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    code          = models.CharField( blank=1, null=1, max_length=40, db_index=1,
                        help_text="It's optional.",
                        )
    type          = models.IntegerField( default=0, db_index=1, 
                        choices=PRICE_CHOICES,
                        )
    received      = models.DateTimeField( blank=1, null=1 )
    finished      = models.DateTimeField( blank=1, null=1 )
    property      = models.DecimalField( verbose_name=_("Property Value"), default=0, max_digits=8, decimal_places=0 )
    square        = models.DecimalField( verbose_name=_("Property Area"), blank=1, null=1, default=0, max_digits=10, decimal_places=2,
                        help_text="Only know after drawn!",
                        )
    default       = models.DecimalField( verbose_name=_("Plan Default"), default=0, max_digits=10, decimal_places=2 )
    price         = models.DecimalField( verbose_name=_("Plan Price"), default=0, max_digits=10, decimal_places=2 )
    calculated    = models.DecimalField( verbose_name=_("Calculated Price"), default=0, max_digits=10, decimal_places=2, db_column='calculated_price' )
    amendments    = models.IntegerField( verbose_name=_("Amendments Count"), blank=1, default=0 )
    amend_total   = models.DecimalField( verbose_name=_("Amend Total"), default=0, max_digits=10, blank=1, null=1, decimal_places=2 )
    runtime       = models.IntegerField( verbose_name=_("Estimated time"), default=0 )
    IsAmendment   = models.BooleanField( verbose_name=_("Has Amendments (AC)"), db_column='IsAmendment' )
    IsArchive     = models.BooleanField( verbose_name=_("Archive (AR)"), db_column='IsArchive' )

    notes         = models.TextField( blank=1 )
    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % ( self.title or "..." )

    class Admin:
        pass

    #class Media:
    #    js = ( '/media/js/status.updater.js', )

    class Meta:
        ordering = ('title', )
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs (Job List)")

    def rendered_job( self ):
        html = """
<div class="rendered_job" id="%(job_id)s">
<div><a title="company" href="%(company_href)s" class="rlink" id="lookup_id_%(company_id)s" onclick="return showRelatedObjectLookupPopup(this);"><nobr>%(company)s</nobr></a></div>
<div class="bordered"><a title="branch" href="%(branch_href)s" class="rlink" id="lookup_id_%(branch_id)s" onclick="return showRelatedObjectLookupPopup(this);"><nobr>%(branch)s</nobr></a></div>
<div class="bordered">%(contact_href)s</div>
</div>
"""
        has_contact = self.contact is not None and 1 or 0
        app_label = '../../%s' % self._meta.app_label
        job_id = 'job_%s' % self.pk
        if has_contact and self.contact.email:
            emails = _get_email(self.contact.email)
            mailto = ', '.join(['%s' % x for x in emails]) or ''
            if mailto:
                status_id = 'mail-status_%s_%s' % (self.pk, self.status.id)
                mailto = """<a class="rlink" title="contact" href="mailto:%s" id="%s" name="mail_job" onclick="return false;">%s</a>""" % ( \
                    escape(mailto), status_id, self.contact.title
                )
        else:
            mailto = ''
        options = { 
            'job_id'       : job_id,
            'company'      : self.company,
            'company_id'   : self.company.id,
            'company_href' : '%s/company/%s' % (app_label, str(self.company.id)),
            'branch'       : self.branch,
            'branch_id'    : self.branch.id,
            'branch_href'  : '%s/branch/%s'  % (app_label, str(self.branch.id)), 
            'contact'      : has_contact and self.contact or '', 
            'contact_id'   : has_contact and self.contact.id or '', 
            'contact_href' : mailto or has_contact and '<span class="rendered_nomail">%s</span>' % self.contact.title or 
                             '<span class="rendered_none">---</span>', 
        }
        return html % options
    rendered_job.allow_tags = True
    rendered_job.short_description = _('Client')
    rendered_job.admin_order_field = 'company'

    def rendered_notes( self ):
        value = self.notes or ''
        return "<div id=\"notesbox_%s\">%s</div>" % (self.pk, value and linebreaks(value) or '')
    rendered_notes.allow_tags = True
    rendered_notes.short_description = _('Notes')
    rendered_notes.admin_order_field = 'notes'

    def rendered_title( self ):
        return "<div class=\"tracker\" id=\"tracker_%s\"><div class=\"title\">%s</div>%s</div>" % ( 
                self.pk,
                self.title,
                self.notes and _notes_icon(id='nic_%s' % self.pk) or '',
                #self.branch.city and '<br>'+self.branch.city or '', 
                #self.branch.country and '<br>'+self.branch.country.title or '', 
                #self.branch.postcode and '<br>'+self.branch.postcode or '', 
            )
    rendered_title.allow_tags = True
    rendered_title.short_description = _('Property Address')
    rendered_title.admin_order_field = 'title'

    def rendered_status( self ):
        status_id = 'status_%s_%s' % (self.pk, self.status.id)
        html = """<nobr><span id=\"%s\" name=\"old_status\" class=\"rendered_status %s\">%s</span></nobr>"""
        return html % ( status_id, lower(self.status.title), self.status )
    rendered_status.allow_tags = True
    rendered_status.short_description = _('Status')
    rendered_status.admin_order_field = 'status'

    def rendered_user( self ):
        html = """<nobr><span id=\"user_%s_%s\" name=\"old_user\" class=\"custom_user\">%s</span></nobr>"""
        if self.user is not None:
            return html % ( self.pk, self.user.id, self.user.username in settings.NO_USERS and '-' or self.user )
        return html % ( self.pk, '0', '---' )
    rendered_user.allow_tags = True
    rendered_user.short_description = _('Drawn')
    rendered_user.admin_order_field = 'user'

    def rendered_phones( self ):
        phones = set()
        phone_prefix = ''
        branch_phone_prefix = 'Branch'
        fax_prefix = 'Fax'
        mobile_prefix = 'Mob'
        if self.contact is not None:
            if self.contact.phone:
                for x in self.contact.phone.replace(';',',').split(','):
                    phones.add((phone_prefix, x,))
            if self.contact.mobile:
                phones.add((mobile_prefix, self.contact.mobile,))
        if self.branch is not None:
            phones.add((branch_phone_prefix, self.branch.phone1,))
            phones.add((branch_phone_prefix, self.branch.phone2,))
            phones.add((fax_prefix, self.branch.fax,))
        if phones:
            html = """<div class=\"rendered_phone%s\"><nobr>%s</nobr></div>"""
            return '<div>%s</div>' % ( \
                ''.join([html % (not p and '_active' or '', _get_phone(x.strip(), p)) for p, x in sorted(phones, reverse=0) if x])
            )
        else:
            return ''
    rendered_phones.allow_tags = True
    rendered_phones.short_description = _('Phones/Fax/Mobile')
    rendered_phones.admin_order_field = None

    def rendered_code( self ):
        html = """<nobr><span class=\"rendered_code\">%s</span></nobr>"""
        return self.code and html % self.code.strip() or ''
    rendered_code.allow_tags = True
    rendered_code.short_description = _('Code')
    rendered_code.admin_order_field = 'code'

    def rendered_property( self ):
        return "%s" % self.property
    rendered_property.short_description = _('Value')
    rendered_property.admin_order_field = 'property'

    def rendered_square( self ):
        return "%s" % self.square
    rendered_square.short_description = _('Area')
    rendered_square.admin_order_field = 'square'

    def rendered_default( self ):
        return "%s" % self.default
    rendered_default.short_description = _('Default')
    rendered_default.admin_order_field = 'default'

    def rendered_price( self ):
        return "%s" % self.price
    rendered_price.short_description = _('Price')
    rendered_price.admin_order_field = 'price'

    def rendered_prices( self ):
        html = """
<table class=\"rendered_prices\">
<tr><td nowrap><span title=\"default\">%(default)s</span></td></tr>
<tr><td nowrap><span title=\"plan\">%(price)s</span></td></tr>
<tr><td %(calculated_style)s nowrap><span title=\"calculated\">%(calculated)s</span></td></tr>
</table>
"""
        return html % {
                'default'    : self.default,
                'price'      : self.price,
                'calculated' : self.calculated, 'calculated_style' : ( 
                    self.calculated and ( 
                        self.calculated < self.price and 'style="background-color:#f88"' or
                        self.calculated > self.price and 'style="background-color:#8e8"' ) or 
                        '' )
            }
    rendered_prices.allow_tags = True
    rendered_prices.short_description = _('Prices')
    rendered_prices.admin_order_field = 'calculated'

    def rendered_received( self ):
        return "%s" % ( self.received and self.received.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S<br>%a') or '-')
    rendered_received.allow_tags = True
    rendered_received.short_description = _('Received')
    rendered_received.admin_order_field = 'received'

    def rendered_finished( self ):
        return "%s" % ( self.finished and self.finished.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S<br>%a') or 
                        '<span>Not<br>completed</span>' )
    rendered_finished.allow_tags = True
    rendered_finished.short_description = _('Finished')
    rendered_finished.admin_order_field = 'finished'

    def rendered_AC( self ):
        return _boolean_icon(self.IsAmendment and True or False, id='AC_%s' % self.pk)
        #return self.IsAmendment and True or False
    #rendered_AC.boolean = True
    rendered_AC.allow_tags = True
    rendered_AC.short_description = _('AC')
    rendered_AC.admin_order_field = 'IsAmendment'

    def rendered_AR( self ):
        return self.IsArchive
    rendered_AR.boolean = True
    rendered_AR.allow_tags = True
    rendered_AR.short_description = _('AR')
    rendered_AR.admin_order_field = 'IsArchive'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S<br>%a') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

    def CDT( self ):
        if not self.received:
            return ''
        else:
            x = datetime.datetime.now() - self.received
            if x > datetime.timedelta(1):
                return ''
            else:
                x = datetime.timedelta(1) - x
                output = "%02d:%02d" % (x.seconds/3600, x.seconds%3600/60)
        html = """<nobr><span class=\"CDT\">%s</span></nobr>"""
        return html % output
    CDT.allow_tags = True
    CDT.short_description = _('*CDTm*')
    CDT.admin_order_field = 'received'

    def RT( self ):
        if not self.runtime:
            return ''
        html = """<nobr><span class=\"RT\">%s</span></nobr>"""
        return html % "%02d:%02d" % (self.runtime/60, self.runtime%60)
    RT.allow_tags = True
    RT.short_description = _('*ERTm*')
    RT.admin_order_field = 'runtime'

    def rendered_amendments( self ):
        id = 'amendments_%s' % self.pk
        return """<nobr><span class=\"AMD\" id=\"%s\" title=\"updated automatically\">%s</span></nobr>""" % (id, self.amendments)
    rendered_amendments.allow_tags = True
    rendered_amendments.short_description = _('AMD')
    rendered_amendments.admin_order_field = 'amendments'

    def rendered_amend_total( self ):
        html = """
<table class=\"rendered_prices\">
<tr><td nowrap><span title=\"amend total\">%(amend_total)s</span></td></tr>
</table>
"""
        return html % {
                'amend_total': self.amend_total,
            }
    rendered_amend_total.allow_tags = True
    rendered_amend_total.short_description = _('Total')
    rendered_amend_total.admin_order_field = 'amend_total'

    def flow_received( self ):
        return "%s" % ( self.received and self.received.strftime('<b><nobr>%d %b %Y</nobr></b>') or '-')
    flow_received.allow_tags = True

    def flow_status( self ):
        html = """<nobr><span class=\"rendered_status %s\">%s</span></nobr>"""
        return html % ( lower(self.status.title), self.status )
    flow_status.allow_tags = True

    def flow_prices( self ):
        html = """
<table width="50px" class=\"rendered_prices\">
<tr><td nowrap><span title=\"default\">%(default)s</span></td></tr>
<tr><td nowrap><span title=\"plan\">%(price)s</span></td></tr>
<tr><td %(calculated_style)s nowrap><span title=\"calculated\">%(calculated)s</span></td></tr>
</table>
"""
        return html % {
                'default'    : self.default,
                'price'      : self.price,
                'calculated' : self.calculated, 'calculated_style' : ( 
                    self.calculated and ( 
                        self.calculated < self.price and 'style="background-color:#f88"' or
                        self.calculated > self.price and 'style="background-color:#8e8"' ) or 
                        '' )
            }
    flow_prices.allow_tags = True
