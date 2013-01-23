# -*- coding: utf-8 -*-

import json, os, pprint, urllib2, unittest
import settings_app
from django.test import TestCase
from xisbn_app.models import XID
# from xisbn_app.classes.utility_code import UtilityCode


class Interface_Test(TestCase):
  
  def test_badIsbn(self):
    output = urllib2.urlopen( u'http://127.0.0.1/easyborrow/xisbn/isbn/123/', timeout=settings_app.URLLIB2_TIMEOUT ).read()
    json_dict = json.loads( output )
    assert sorted(json_dict.keys()) == [u'documentation', u'request', u'response' ]
    assert sorted(json_dict[u'request'].keys()) == [u'number', u'number_type' ]
    assert sorted(json_dict[u'response'].keys()) == [u'alternates', u'filtered_alternates', u'status' ]
    assert json_dict[u'request'][u'number'] == u'123'
    assert json_dict[u'response'][u'status'] == u'invalidId', json_dict[u'response'][u'status']
    assert len(json_dict[u'response'][u'alternates']) == 0
    assert len(json_dict[u'response'][u'filtered_alternates']) == 0
  
  def test_goodIsbnWithFilteredAlternates(self):
    output = urllib2.urlopen( u'http://127.0.0.1/easyborrow/xisbn/isbn/9780688002305/', timeout=settings_app.URLLIB2_TIMEOUT ).read()
    json_dict = json.loads( output )
    assert json_dict[u'request'][u'number'] == u'9780688002305'
    assert json_dict[u'response'][u'status'] == u'request_ok'
    assert len(json_dict[u'response'][u'filtered_alternates']) > 0
    assert sorted(json_dict.keys()) == [u'documentation', u'request', u'response' ]
    assert sorted(json_dict[u'request'].keys()) == [u'number', u'number_type' ]
    assert sorted(json_dict[u'response'].keys()) == [u'alternates', u'filtered_alternates', u'status' ]
    
  def test_goodIsbnWithNoFilteredAlternates(self):
    output = urllib2.urlopen( u'http://127.0.0.1/easyborrow/xisbn/isbn/9780295987316/', timeout=settings_app.URLLIB2_TIMEOUT ).read()
    json_dict = json.loads( output )
    assert json_dict[u'request'][u'number'] == u'9780295987316'
    assert json_dict[u'response'][u'status'] == u'request_ok'
    assert len(json_dict[u'response'][u'filtered_alternates']) == 0
    assert sorted(json_dict.keys()) == [u'documentation', u'request', u'response' ]
    assert sorted(json_dict[u'request'].keys()) == [u'number', u'number_type' ]
    assert sorted(json_dict[u'response'].keys()) == [u'alternates', u'filtered_alternates', u'status' ]
    
  def test_oclcnumWithNoFilteredAlternates(self):
    output = urllib2.urlopen( u'http://127.0.0.1/easyborrow/xisbn/oclcnum/123/', timeout=settings_app.URLLIB2_TIMEOUT ).read()
    json_dict = json.loads( output )
    assert json_dict[u'request'][u'number'] == u'123'
    assert json_dict[u'request'][u'number_type'] == u'oclcnum'
    assert json_dict[u'response'][u'status'] == u'request_ok'
    assert len(json_dict[u'response'][u'filtered_alternates']) == 0
    assert sorted(json_dict.keys()) == [u'documentation', u'request', u'response' ]
    assert sorted(json_dict[u'request'].keys()) == [u'number', u'number_type' ]
    assert sorted(json_dict[u'response'].keys()) == [u'alternates', u'filtered_alternates', u'status' ]
				
	# end class Interface_Test()


class XID_Tests(TestCase):
  '''
  - TODO: BA/english - should also return the BC/english?
  '''
  
  def test_settings_instantiation(self):
    '''
    Tests that module instantiation handles settings not-defined, or defined as dict, module, or path.
    '''
    ## no settings passed on instantiation
    try:
      x = XID( OCLC=u'673595' )  # http://www.worldcat.org/title/zen-and-the-art-of-motorcycle-maintenance-an-inquiry-into-values/oclc/673595
    except Exception, e:
      assert e.message == u'requires settings dict, or module or module path.', e.message
    ## dict method    
    settings_dict = { 'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID }
    x = XID( OCLC=u'673595', settings=settings_dict )
    assert x.requested_oclcnum == u'673595'
    assert x.xid_url[0:96] == u'http://xisbn.worldcat.org/webservices/xid/oclcnum/673595?method=getEditions&format=json&fl=*&ai=', x.xid_url[0:96]
    ## settings module
    x = XID( OCLC=u'673595', settings=settings_app )
    assert x.requested_oclcnum == u'673595'
    assert x.xid_url[0:96] == u'http://xisbn.worldcat.org/webservices/xid/oclcnum/673595?method=getEditions&format=json&fl=*&ai=', x.xid_url[0:96]
    ## settings path
    real_path = os.path.realpath( u'./xisbn_app/settings_app.py' )
    x = XID( OCLC=u'673595', settings=real_path )
    assert x.requested_oclcnum == u'673595'
    assert x.xid_url[0:96] == u'http://xisbn.worldcat.org/webservices/xid/oclcnum/673595?method=getEditions&format=json&fl=*&ai=', x.xid_url[0:96]

  ## getAlternates()
  
  def test_getAlternates_isbnBad(self):
    x = XID( 
      ISBN=u'123',
      settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    assert x.xid_url == u'http://xisbn.worldcat.org/webservices/xid/isbn/123?method=getEditions&format=json&fl=*&ai=%s' % settings_app.OCLC_AFFILIATE_ID, x.xid_url
    assert x.oclc_status_code == None
    x.getAlternates()
    assert x.oclc_status_code == u'invalidId', x.oclc_status_code

  def test_getAlternates_isbnWithAlternates(self):
    x = XID( 
      ISBN=u'9780688002305',  # ZMM
      settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    data = x.getAlternates()
    assert type(data) == list
    assert data[0]['isbn'] == [u'9780688002305']
    assert x.oclc_status_code == u'ok'
    assert type(x.alternates) == list
    assert type(x.format_codes[0]) == unicode
    assert x.format_codes == [u'BA'], x.format_codes
    assert type(x.language_code) == unicode, type(x.language_code)
    assert x.language_code == u'eng', x.language_code
    assert x.oclcnum_isbns == None  
    
  def test_getAlternates_oclcnumBad(self):
    x = XID( 
      OCLC=u'abc',
      settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    assert x.xid_url == u'http://xisbn.worldcat.org/webservices/xid/oclcnum/abc?method=getEditions&format=json&fl=*&ai=%s' % settings_app.OCLC_AFFILIATE_ID, x.xid_url
    assert x.oclc_status_code == None
    x.getAlternates()
    assert x.oclc_status_code == u'invalidId', x.oclc_status_code
    
  def test_getAlternates_oclcnumWithAnIsbnWithAlternates(self):
    ## oclcnum (which has a corresponding isbn)
    x = XID( OCLC=u'673595', settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    data = x.getAlternates()
    assert type(data) == list
    assert data[0]['oclcnum'] == [u'673595']
    assert x.oclc_status_code == u'ok'
    assert type(x.alternates) == list    
    assert type(x.format_codes[0]) == unicode
    assert x.format_codes == [u'BA'], x.format_codes
    assert type(x.language_code) == unicode, type(x.language_code)
    assert x.language_code == u'eng', x.language_code
    assert x.oclcnum_isbns == [u'9780688002305']
    
  def test_getAlternates_oclcnumNoIsbnAlternates(self):
    x = XID( OCLC=u'123', settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    x.getAlternates()
    assert x.oclc_status_code == u'ok', x.oclc_status_code
    assert len(x.alternates) > 0, x.alternates
    assert x.oclcnum_isbns == None, x.oclcnum_isbns
      
  ## getFilteredAlternates()
  
  def test_getFilteredAlternates_isbnNoFilteredAlternates(self):
    x = XID( 
      ISBN=u'9780802130198',  # 'Zen poems...'
      settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    x.getFilteredAlternates()
    assert x.oclc_status_code == u'ok'
    assert type(x.alternates) == list
    assert type(x.filtered_alternates) == list
    assert len(x.filtered_alternates) == 0
      
  def test_getFilteredAlternates_isbnWithAlternates(self):
    x = XID( ISBN=u'9780688002305', settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    x.getFilteredAlternates()
    assert x.oclc_status_code == u'ok'
    assert type(x.alternates) == list
    assert type(x.filtered_alternates) == list
    assert len(x.filtered_alternates) > 0
    assert not x.requested_isbn in x.filtered_alternates[0][u'isbn'], x.filtered_alternates[0][u'isbn']  # tests that request-isbn has been removed
    alternate_format_found = False
    self.assertEqual( sorted(x.filtered_alternates[0].keys()), [u'author', u'city', u'ed', u'form', u'isbn', u'lang', u'oclcnum', u'publisher', u'title', u'url', u'year'] )
    for entry in x.filtered_alternates:
      assert entry[u'lang'] == x.language_code
      # print u'- entry format: %s -- x.format_codes: %s' % (entry[u'form'], x.format_codes)
      self.assertFalse( u'AA' in entry[u'form'] )
      if not entry[u'form'] == x.format_codes:
        alternate_format_found = True
    self.assertEqual( alternate_format_found, True )
          
  def test_getFilteredAlternates_oclcnumWithAnIsbnWithAlternates(self):
    x = XID( OCLC=u'673595', settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    x.getFilteredAlternates()
    # pprint.pprint( x.log )
    assert x.oclc_status_code == u'ok'
    assert type(x.alternates) == list
    assert type(x.filtered_alternates) == list, type(x.filtered_alternates)
    assert len(x.filtered_alternates) > 0, len(x.filtered_alternates)
    assert x.oclcnum_isbns == [u'9780688002305']
    assert not x.requested_oclcnum in x.filtered_alternates[0][u'oclcnum'], x.filtered_alternates[0][u'oclcnum']  # tests that request-oclc has been removed
    for entry in x.filtered_alternates:
      assert entry[u'form'] == x.format_codes
      assert entry[u'lang'] == x.language_code

  def test_getFilteredAlternates_oclcnumNoIsbnAlternates(self):
    x = XID( OCLC=u'123', settings={ u'OCLC_AFFILIATE_ID': settings_app.OCLC_AFFILIATE_ID } )
    assert x.alternates == None
    x.getFilteredAlternates()
    assert x.oclc_status_code == u'ok', x.oclc_status_code
    assert len(x.alternates) > 0, x.alternates
    assert x.oclcnum_isbns == None, x.oclcnum_isbns
  
  # end class XID_Tests()
    
