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
# Checked: 2010/05/01
# ichar@g2.ru
#
import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, AnonymousUser

YES_NO_CHOICES = ( ( 0, _('No'),), (1, _('Yes'),), ) 

STATUS_TYPE_CHOICES = (
    ( 0, 'Standard' ),
    ( 1, 'Priority' ),
)

STATUS_CHOICES = (
    ( 0, 'Standard' ),
    ( 1, 'Priority' ),
    ( 2, 'On Hold'  ),
    ( 3, 'In Quere' ),
    ( 4, 'Pending'  ),
    ( 5, 'Allocated' ),
    ( 6, 'Draft sent' ),
    ( 7, 'Waiting for client' ),
    ( 8, 'Approved' ),
    ( 9, 'Urgent' ),
)

PAY_CHOICES = (
    ( 0, 'Fixed Fee' ),
    ( 1, 'Footage + Basic' ),
    ( 2, 'Price Bands' ),
    ( 3, 'Other' ),
)

MYOB_CHOICES = (
    ( 0, 'Private' ),
    ( 1, 'Public' ),
    ( 2, '...' ),
)

class Country( models.Model ):
    """
        *Country* fields set
    """
    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % self.title

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr><br>%H:%M:%S</b>') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

class Department( models.Model ):
    """
        *Department* fields set
    """
    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % self.title

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

class Status( models.Model ):
    """
        *Status* fields set
    """
    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    type          = models.IntegerField( default=0, max_length=20, db_index=1, 
                        choices=STATUS_TYPE_CHOICES,
                        )
    structure     = models.CharField( blank=1, null=1, max_length=10,
                        verbose_name=_("Status structure"),
                        help_text="It's optional.",
                        )
    sortkey       = models.IntegerField( default=0, db_index=1 )

    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % self.title

    class Admin:
        pass

    class Meta:
        ordering = ('title', ) # 'sortkey', 
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

class PayStructure( models.Model ):
    """
        *PayStructure* fields set
    """
    title         = models.CharField( blank=0, null=1, max_length=250, db_index=1 )
    type          = models.IntegerField( default=0, db_index=1, 
                        choices=PAY_CHOICES,
                        )
    code          = models.CharField( blank=1, null=1, max_length=40, db_index=1,
                        help_text="It's optional.",
                        )
    fixed_fee     = models.DecimalField( verbose_name=_("Fixed Fee"), default=0, max_digits=10, decimal_places=2 )
    amendments    = models.IntegerField( verbose_name=_("Amendments Limit"), default=0, blank=1,
                        help_text="For Amendments job's limitation enter this value!",
                        )

    price1        = models.DecimalField( verbose_name=_("Price Bracket 1"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price2        = models.DecimalField( verbose_name=_("Price Bracket 2"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price3        = models.DecimalField( verbose_name=_("Price Bracket 3"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price4        = models.DecimalField( verbose_name=_("Price Bracket 4"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price5        = models.DecimalField( verbose_name=_("Price Bracket 5"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price6        = models.DecimalField( verbose_name=_("Price Bracket 6"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price7        = models.DecimalField( verbose_name=_("Price Bracket 7"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price8        = models.DecimalField( verbose_name=_("Price Bracket 8"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price9        = models.DecimalField( verbose_name=_("Price Bracket 9"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    price10       = models.DecimalField( verbose_name=_("Price Bracket 10"), blank=1, default=0, max_digits=10, decimal_places=2 )

    max1          = models.DecimalField( verbose_name=_("Max 1st"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max2          = models.DecimalField( verbose_name=_("Max 2nd"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max3          = models.DecimalField( verbose_name=_("Max 3rd"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max4          = models.DecimalField( verbose_name=_("Max 4th"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max5          = models.DecimalField( verbose_name=_("Max 5th"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max6          = models.DecimalField( verbose_name=_("Max 6th"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max7          = models.DecimalField( verbose_name=_("Max 7th"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max8          = models.DecimalField( verbose_name=_("Max 8th"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max9          = models.DecimalField( verbose_name=_("Max 9th"),  blank=1, default=0, max_digits=10, decimal_places=2 )
    max10         = models.DecimalField( verbose_name=_("Max 10th"), blank=1, default=0, max_digits=10, decimal_places=2 )

    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % ( self.title or "...", )

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("Pay Structure")
        verbose_name_plural = _("Pay Structures")

    def rendered_code( self ):
        html = """<nobr><span class=\"rendered_code\">%s</span></nobr>"""
        return self.code and html % self.code.strip() or ''
    rendered_code.allow_tags = True
    rendered_code.short_description = _('Code')
    rendered_code.admin_order_field = 'code'

    def rendered_type( self ):
        value = ''
        klass = ''
        for i, x in PAY_CHOICES:
            if self.type == i:
                value = x
                klass = '_' + x.split(' ')[0].lower()
                break
        html = """<nobr><span class=\"rendered_type%s\">%s</span></nobr>"""
        return html % (klass, value)
    rendered_type.allow_tags = True
    rendered_type.short_description = _('Type')
    rendered_type.admin_order_field = 'type'

    def rendered_amendments( self ):
        return """<nobr><span class=\"AMD\">%s</span></nobr>""" % self.amendments
    rendered_amendments.allow_tags = True
    rendered_amendments.short_description = _('Amendments')
    rendered_amendments.admin_order_field = 'amendments'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'

class MYOB( models.Model ):
    """
        *MYOB* fields set
    """
    title         = models.CharField( blank=0, null=1, max_length=250, db_index=1 )
    type          = models.IntegerField( default=0, max_length=10, db_index=1, 
                      choices=MYOB_CHOICES,
                      )
    code          = models.CharField( blank=1, null=1, max_length=40, db_index=1,
                        help_text="It's optional.",
                        )

    myobaccount   = models.CharField( verbose_name=_("Account Number"), max_length=20, blank=1 )
    myobvat       = models.CharField( verbose_name=_("VAT Code"), max_length=10, blank=1, default='S' )
    myobcompany   = models.CharField( verbose_name=_("MYOB Company Name"), max_length=50, blank=1 )
    myobquantity  = models.IntegerField( verbose_name=_("Quantity"), default=1, blank=1 )

    RD            = models.DateTimeField( verbose_name=_("Registered"), blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % ( self.title or "..." )

    class Admin:
        pass

    class Meta:
        ordering = ('title', )
        verbose_name = _("MYOB Information")
        verbose_name_plural = _("MYOBs")

    def rendered_code( self ):
        html = """<nobr><span class=\"rendered_code\">%s</span></nobr>"""
        return self.code and html % self.code.strip() or ''
    rendered_code.allow_tags = True
    rendered_code.short_description = _('Code')
    rendered_code.admin_order_field = 'code'

    def rendered_type( self ):
        value = ''
        for i, x in MYOB_CHOICES:
            if self.type == i:
                value = x
                break
        html = """<nobr><span class=\"rendered_type\">%s</span></nobr>"""
        return html % value
    rendered_type.allow_tags = True
    rendered_type.short_description = _('Type')
    rendered_type.admin_order_field = 'type'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S') # '%Y-%m-%d %H:%M:%S'
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'
