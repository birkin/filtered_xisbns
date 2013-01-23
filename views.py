# -*- coding: utf-8 -*-

import json, urllib2
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render_to_response
from xisbn_app import settings_app
from xisbn_app.models import XID


def showAlternates( request, num_type, num ):
  ## validate num_type
  if num_type not in [u'isbn', u'oclcnum']:
    return HttpResponseNotFound( u'404 / Not Found' )
  ## initialize return dict
  data = { 
    u'documentation': u'url_coming', 
    u'request': {
      u'number_type': num_type,
      u'number': num
      }, 
    u'response': {
      u'alternates': [],
      u'filtered_alternates': [],
      u'status': u'init'
      } 
    }  
  ## work
  if num_type == u'isbn':
    xid = XID( ISBN=num, settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
  else:
    xid = XID( OCLC=num, settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
  try:
    xid.getFilteredAlternates()
    ## build response
    data[u'response'][u'alternates'] = ( [] if xid.alternates == None else xid.alternates )
    data[u'response'][u'filtered_alternates'] = ( [] if xid.filtered_alternates == None else xid.filtered_alternates )
    data[u'response'][u'status'] = ( u'request_ok' if xid.oclc_status_code == u'ok' else xid.oclc_status_code )
  except urllib2.URLError, e:
    data[u'response'][u'status'] = u'URLError: %s' % e
  ## output
  output = json.dumps( data, sort_keys=True, indent=2 ).decode(u'utf-8')
  assert type(output) == unicode
  callback = request.GET.get( u'callback', None )
  if callback:
    assert type(callback) == unicode
    output = u'%s(%s)' % ( callback, output )
  return HttpResponse( output, content_type='application/json; charset=utf8' )
