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
# Checked: 2011/11/01
# ichar@g2.ru
#
import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, AnonymousUser
from django.utils.html import urlize, linebreaks

YES_NO_CHOICES = ( ( 0, _('No'),), (1, _('Yes'),), ) 

DEBUG_CHOICES = (
    ( 0, 'Claim' ),
    ( 1, 'Defect' ),
    ( 2, 'Error' ),
    ( 3, 'Requirements' ),
    ( 4, 'Proposal' ),
    ( 5, 'Warning' ),
    ( 6, 'Question' ),
    ( 7, 'Information' ),
)

debug_choices = list(DEBUG_CHOICES)
debug_choices.sort( lambda x, y: cmp(x[1], y[1]) )

class DebugLog( models.Model ):
    """
        *DebugLog* fields set
    """
    title         = models.CharField( blank=0, null=1, max_length=100, db_index=1 )
    type          = models.IntegerField( default=0, db_index=1, 
                        choices=debug_choices,
                        )
    description   = models.TextField( blank=1, 
                        verbose_name=_("Description") 
                        )

    user          = models.ForeignKey( User, verbose_name=_("Author") )
    received      = models.DateTimeField( blank=1, null=1 )
    finished      = models.DateTimeField( blank=1, null=1 )
    IsDone        = models.BooleanField( verbose_name=_("Is Done (Was completed)"), db_column='IsDone' )

    RD            = models.DateTimeField( blank=1, null=1 )

    def __unicode__( self ):
        return '%s' % self.title

    class Admin:
        pass

    class Meta:
        ordering = ('received', )
        verbose_name = _("Log Item")
        verbose_name_plural = _("Error Records (Debug Logger)")

    def rendered_type( self ):
        return "<nobr><span class=\"rendered_code\">%s</span></nobr>" % DEBUG_CHOICES[ self.type ][ 1 ]
    rendered_type.allow_tags = True
    rendered_type.short_description = _('Type')
    rendered_type.admin_order_field = 'type'

    def rendered_description( self ):
        return "%s" % linebreaks(self.description)
    rendered_description.allow_tags = True
    rendered_description.short_description = _('description')
    rendered_description.admin_order_field = 'description'

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

    def rendered_user( self ):
        return "<nobr><span class=\"rendered_status\">%s</span></nobr>" % self.user
    rendered_user.allow_tags = True
    rendered_user.short_description = _('Author')
    rendered_user.admin_order_field = 'user'

    def rendered_done( self ):
        return self.IsDone
    rendered_done.boolean = True
    rendered_done.allow_tags = True
    rendered_done.short_description = _('Is Done')
    rendered_done.admin_order_field = 'IsDone'

    def rendered_RD( self ):
        return "%s" % self.RD.strftime('<b><nobr>%d %b %Y</nobr></b><br>%H:%M:%S<br>%a') # '%Y-%m-%d %H:%M:%S'<br>%a
    rendered_RD.allow_tags = True
    rendered_RD.short_description = _('RD')
    rendered_RD.admin_order_field = 'RD'
