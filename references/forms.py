#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# References. Admin model classes
#
# Checked: 2010/04/30
# ichar@g2.ru
#
import datetime

from django import forms
from django.forms import models

from references.models import Country, Department, Status, PayStructure, MYOB, PAY_CHOICES

TOPIC_CHOICES = (
    ( 'general',    'General enquiry' ),
    ( 'bug',        'Bug report'      ),
    ( 'suggestion', 'Suggestion'      ),
    ( 'other',      'Other'           ),
)

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
# ========================================================================================================
#

class FeedbackForm( forms.Form ):
    #
    # Contact HTML-form model
    #
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

    def clean_message( self ):
        message = self.cleaned_data.get('message', '')
        num_words = len(message.split())
        if num_words < 4:
            raise forms.ValidationError("Not enough words!")
        return message


class BaseModelForm( models.ModelForm ):
    def clean_RD( self ):
        #RD = self.cleaned_data.get('RD', None)
        #if RD is None:
        RD = datetime.datetime.now()
        return RD

    def __init__( self, *args, **kwargs ):
        super(BaseModelForm, self).__init__(*args, **kwargs)
        self.label_suffix = ''


class CountryForm( BaseModelForm ):
    class Meta:
        model = Country

class DepartmentForm( BaseModelForm ):
    class Meta:
        model = Department

class StatusForm( BaseModelForm ):
    class Meta:
        model = Status

class PayStructureForm( BaseModelForm ):
    type = forms.IntegerField( 
            required=True, 
            widget=forms.RadioSelect( choices=PAY_CHOICES ),
            label="Pay Type",
            initial=0
        )

    fixed_fee = forms.DecimalField( required=True, label="Fixed Fee", initial='0.00' )
    #amendments = forms.IntegerField( required=False, label="Amendments Limit", initial=0,
    #    help_text="For Amendments job's limitation enter this value!",
    #)

    class Meta:
        model = PayStructure

    def clean_fixed_fee( self ):
        pay_type = int(self.cleaned_data.get('type', None) or 0)
        x = self.cleaned_data.get('fixed_fee', None)
        if not x and pay_type == 0:
            raise forms.ValidationError("You have selected 'Fixed Fee' Pay Type. So this value is required!")
        return x

class MYOBForm( BaseModelForm ):
    myobcompany = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'vLargeTextField'}), #, 'style': 'width:100%'
            label="MYOB Company Name",
            initial=''
        )

    class Meta:
        model = MYOB
