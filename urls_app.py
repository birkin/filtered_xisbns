from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to


urlpatterns = patterns('',

	( r'^(?P<num_type>[^/]+)/(?P<num>[^/]+)/$',  'xisbn_app.views.showAlternates' ),
	
  )
