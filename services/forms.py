#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# Services. Admin model forms
#
# Checked: 2010/03/31
# ichar@g2.ru
#
import datetime

from django import forms
from django.forms import models

from services.models import DebugLog

TOPIC_CHOICES = (
    ( 'general',    'General enquiry' ),
    ( 'bug',        'Bug report'      ),
    ( 'suggestion', 'Suggestion'      ),
    ( 'other',      'Other'           ),
)

#
# ========================================================================================================
#

class BaseModelForm( models.ModelForm ):
    def clean_RD( self ):
        RD = self.cleaned_data.get('RD', None)
        if RD is None:
            RD = datetime.datetime.now()
        return RD

    def __init__( self, *args, **kwargs ):
        super(BaseModelForm, self).__init__(*args, **kwargs)
        self.label_suffix = ''


class DebugLogForm( BaseModelForm ):
    description = forms.CharField(
                    widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'cols':100, 'rows':15, 'style': 'width:100%'}),
                    initial="Replace with your feedback"
        )

    class Meta:
        model = DebugLog
