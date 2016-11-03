from django.conf.urls.defaults import *
from mp.views import thanks

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from jobs.forms import JobForm
from jobs.wizard import ClientWizard, CompanyWizardForm, BranchWizardForm, ContactWizardForm
from jobs.wizard import PayStructureWizardForm, MYOBWizardForm, JobWizardForm

from jobs.exporter import ExcelReport
from jobs.flowlogic import JobFlowLogic

urlpatterns = patterns('',
    # Example:
    # (r'^mp/', include('mp.foo.urls')),

    (r'^.*flow_client_loader$', 'mp.jobs.views.flow_client_loader'),
    (r'^.*flow_paystructure_loader$', 'mp.jobs.views.flow_paystructure_loader'),
    (r'^.*flow_job_loader$', 'mp.jobs.views.flow_job_loader'),
    (r'^.*tracker$', 'mp.jobs.views.tracker'),
    (r'^.*loader$', 'mp.jobs.views.loader'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/jsi18n/$', 'django.views.i18n.javascript_catalog'),
    #(r'^admin/(.*)', admin.site.root),

    #(r'^admin$', include('django.contrib.admin.urls')),
    (r'^manage/doc/', include('django.contrib.admindocs.urls')),
    (r'^manage/jsi18n/$', 'django.views.i18n.javascript_catalog'),
    #(r'^manage/(.*)', admin.site.root),

    (r'^feedback/$', 'mp.jobs.views.feedback'),
    (r'^.*wizard/(.*)$', ClientWizard([ CompanyWizardForm, BranchWizardForm, ContactWizardForm, PayStructureWizardForm, MYOBWizardForm, JobWizardForm ])),
    (r'^.*reporting/$', ExcelReport()),
    (r'^.*jobflow/$', JobFlowLogic(admin.site)),
    (r'^.*thanks/$', thanks),

    (r'^(.*)', admin.site.root),
)
