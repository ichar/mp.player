#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# jobs/forms.py
#
# Checked: 2011/11/09
# ichar@g2.ru
#
import re
import datetime
import decimal
import settings

from django import forms
from django.forms import models
from django.contrib.admin.widgets import AdminSplitDateTime

from references.models import Country, Department, Status, PayStructure, MYOB
from jobs.models import Company, Branch, Contact, Job, PRICE_CHOICES
from django.forms.widgets import Widget, Select

from widgets import AdvSelect, CountDownTimer

IsDebug = 0

TOPIC_CHOICES = (
    ( 'general',    'General enquiry' ),
    ( 'bug',        'Bug report'      ),
    ( 'suggestion', 'Suggestion'      ),
    ( 'other',      'Other'           ),
)

#
# ========================================================================================================
#

class FeedbackForm( forms.Form ):
    #
    # Contact HTML-form model
    #
    """
    class Media:
        js = ( \
                '/media/../../../jsi18n/', 
                '/media/js/jquery.min.js', 
                '/media/js/foreignkey.updater.js', 
                '/media/js/core.js', 
                '/media/js/admin/RelatedObjectLookups.js', 
                '/media/js/calendar.js', 
                '/media/js/admin/DateTimeShortcuts.js',
                '/media/js/admin/CollapsedFieldsets.js',
             )
        css = {
            'all': ('/media/css/base.css', '/media/css/forms.css',),
        }
    """
    def _media( self ):
        js = [ \
                '../../../jsi18n/', 
                'js/jquery.min.js', 'js/foreignkey.updater.js', 'js/timer.widget.js',
                'js/core.js', 'js/admin/RelatedObjectLookups.js', 
                'js/calendar.js', 'js/admin/DateTimeShortcuts.js',
                'js/admin/CollapsedFieldsets.js',
               ]
        css = ['css/forms.css']
        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js],
                           css={'all': tuple(['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in css])}
                           )
    media = property(_media)

    topic   = forms.ChoiceField(
                    choices=TOPIC_CHOICES, 
                    widget=forms.TextInput(attrs={'style': 'width:100%'})
        )
    message = forms.CharField(
                    widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'cols':100, 'rows':5, 'style': 'width:100%'}),
                    initial="Replace with your feedback"
        )
    sender  = forms.EmailField(
                    required=False, 
                    widget=forms.TextInput(attrs={'style': 'width:50%'})
        )
    finish  = forms.SplitDateTimeField( required=False,
                    widget=AdminSplitDateTime(),
        )

    def clean_message( self ):
        message = self.cleaned_data.get('message', '')
        num_words = len(message.split())
        if num_words < 4:
            raise forms.ValidationError("Not enough words!")
        return message

#
# ========================================================================================================
#

class BaseModelForm( models.ModelForm ):
    def clean_RD( self ):
        #RD = self.cleaned_data.get('RD', None)
        #if RD is None:
        RD = datetime.datetime.now()
        return RD

    def __init__( self, *args, **kwargs ):
        super(BaseModelForm, self).__init__(*args, **kwargs)
        self.label_suffix = ''

    class Media:
        js = ('/media/js/foreignkey.updater.js', '/media/js/timer.widget.js',)

class CompanyForm( BaseModelForm ):
    name = forms.CharField( 
            required=False, 
            widget=forms.TextInput(attrs={'class': 'vLargeTextField'}),
            label="Company Name",
            initial=''
        )

    class Meta:
        model = Company

    def clean_name( self ):
        return self.cleaned_data.get('name', None) or self.cleaned_data.get('title', '')

class BranchForm( BaseModelForm ):
    address = forms.CharField( 
            required=False, 
            widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'rows': 3}),
            initial=''
        )
    notes = forms.CharField( 
            required=False, 
            widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'rows': 7}), #, 'style': 'width:100%'
            initial=''
        )

    class Meta:
        model = Branch

class ContactForm( BaseModelForm ):
    phone = forms.CharField( 
            required=False, 
            widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'rows': 1}),
            label="Phones",
            initial=''
        )

    email = forms.CharField( 
            required=True, 
            widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'rows': 3}),
            label="Email addresses",
            initial=''
        )

    class Meta:
        model = Contact

    def clean_email( self ):
        emails = [x.strip() for x in re.sub(r'[\n,]+', r';', self.cleaned_data.get('email') or '').split(';')]
        return '; '.join([x for x in emails if x])

class JobForm( BaseModelForm ):
    #exclude = ('amendments', 'IsAmendment',)

    title = forms.CharField(
            required=True, 
            widget=forms.TextInput(attrs={'class': 'vLargeTextField'}), #, 'style': 'width:100%'
            label="Property Address",
            initial=''
        )
    type = forms.IntegerField( 
            required=True, 
            widget=forms.RadioSelect( choices=PRICE_CHOICES ),
            label="Type of Price",
            initial=0
        )

    runtime = forms.IntegerField( required=True, initial=0, label="Estimated run-time",
        widget=CountDownTimer( days=1, extra_attrs={'style':'text-align:center;', 'maxlength':2} ),
    )

    property = forms.DecimalField( required=False, max_digits=8, decimal_places=0, label="Property Value", initial='0' )
    default = forms.DecimalField( required=False, label="Plan Default", initial='0.00' )
    price = forms.DecimalField( required=False, label="Plan Price", initial='0.00' )
    calculated = forms.DecimalField( required=False, label="Calculated Price", initial='0.00' )
    received = forms.SplitDateTimeField( required=True, widget=AdminSplitDateTime(), initial='now' )
    finished = forms.SplitDateTimeField( required=False, widget=AdminSplitDateTime() )

    #IsAmendment = forms.BooleanField( required=False, widget=forms.HiddenInput() )
    amend_total = forms.DecimalField( required=False, initial='0.00', label="AmendTotal",
        widget=forms.TextInput(attrs={'disabled': 1}),
    )
    amendments = forms.IntegerField( required=False, initial=0, label="Amendments Count",
        widget=forms.TextInput(attrs={'size': 5}),
    )

    class Meta:
        model = Job

    def clean_received( self ):
        received = self.cleaned_data.get('received', None)
        if not received:
            received = datetime.datetime.now()
        return received

    def clean_default( self ):
        x = self.cleaned_data.get('default', None)
        if x:
            return x
        # Set 'Default Plan' for Fixed Fee equal to Client's Main record
        # --------------------------------------------------------------
        data = self.cleaned_data
        type_of_price = data['type']
        branch = data.get('branch', None)
        fixed_fee = 0
        if type_of_price == 0 and branch is not None:
            pay = branch.pay
            if pay is not None:
                fixed_fee = pay.fixed_fee
        if fixed_fee:
            return fixed_fee
        return 0

    def clean_IsAmendment( self ):
        #print 'IsAmendment'
        amendments = int(self.cleaned_data.get('amendments') or 0)
        if IsDebug:
            x = self.cleaned_data.get('IsAmendment', None)
            print 'clean_IsAmendment:%s, count:%s' % (x, amendments)
        # Set IsAmendment boolean, only if amendments > 0
        # -----------------------------------------------
        if amendments > 0:
            return True
        return False

    def clean_IsArchive( self ):
        x = self.cleaned_data.get('IsArchive', None)
        if IsDebug:
            print 'clean_IsArchive:%s' % x
        if x and str(x).lower() not in ('0', 'false', 'none',):
            return True
        return False

    def clean_amendments( self ):
        #print 'amendments'
        x = int(self.cleaned_data.get('amendments', None) or '0')
        if not x:
            return 0
        return x

    def clean_amend_total( self ):
        print 'amend_total'
        # Make AmendTotal equal: price * (amendments - 1)
        # -----------------------------------------------
        x = int(self.cleaned_data.get('amendments', None) or '0')
        price = decimal.Decimal(self.cleaned_data.get('price', None) or 0)
        calculated = decimal.Decimal(self.cleaned_data.get('calculated', None) or 0)
        if x > 0:
            return (x-1) * (calculated or price or 0)
        return 0

    def clean_square( self ):
        x = self.cleaned_data.get('square', None)
        v = str(x or '').strip()
        IsValid = 1
        if len(v) > 5 or not v.isdigit():
            digits = tuple([int(i) for i in v if i.isdigit()])
            if '.' in v:
                exp = -(len(v) - v.find('.') - 1)
            else:
                exp = 0
            sign = v.startswith('-') and 1 or 0
            try:
                v = decimal.Decimal((sign, digits, exp))
                if not (v >= 0 and v <= decimal.Decimal('99999.99')):
                    IsValid = 0
            except:
                IsValid = 0
        if not IsValid:
            raise forms.ValidationError("'Property Area' value should be valid positive number in range: 0-99999.99!")
        return x or decimal.Decimal('0.00')
