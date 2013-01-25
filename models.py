# -*- coding: utf-8 -*-

'''
Common usage
=============

    from models import XID
    x = XID( isbn=u'1234', settings={u'OCLC_AFFILIATE_ID': u'the_id'} )
    x.getFilteredAlternates()
    assert type( x.filtered_alternates ) == list
    assert sorted( x.filtered_alternates[0].keys() ) == [
      u'author', u'city', u'ed',
      u'form', u'isbn', u'lang',
      u'oclcnum', u'publisher', u'title',
      u'url', u'year'] )
    ## filtered_alternate_entries match original isbn on language, and contain a self.blessed_formats entry'

Notes
=====

see [project README] for additional info

[project README]: https://github.com/Brown-University-Library/borrowdirect_tunneler#readme

'''


import datetime, imp, json, pprint, urllib2



## non-django model ##

class XID(object):

  def __init__( self, OCLC=None,ISBN=None, settings=None  ):
    '''
    - Allows a settings module to be passed in,
        or a settings path to be passed in,
        or a dictionary to be passed in.
    - Sets other attributes.
    '''
    ## normalize settings module
    if not settings:
      raise Exception, u'requires settings dict, or module or module path.'
    elif unicode( settings.__class__ ) == u"<type 'module'>":
      pass
    elif unicode( settings.__class__ ) == u"<type 'str'>":  # path
      settings = imp.load_source( u'*', settings )
    elif unicode( settings.__class__ ) == u"<type 'unicode'>":  # path
      settings = imp.load_source( u'*', settings )
    elif unicode( settings.__class__ ) == u"<type 'dict'>":
      s = imp.new_module(u'settings')
      for key, value in settings.items():
        setattr( s, key, value )
      settings = s
    else:
      raise Exception, u'if passing in settings, settings must be settings module or settings module path.'
    ## attributes
    assert settings.OCLC_AFFILIATE_ID
    self.OCLC_AFFILIATE_ID = settings.OCLC_AFFILIATE_ID
    self.SLEEP_SECONDS = .1 if not u'SLEEP_SECONDS' in dir(settings) else settings.SLEEP_SECONDS
    self.URLLIB2_TIMEOUT = 3 if not u'URLLIB2_TIMEOUT' in dir(settings) else settings.URLLIB2_TIMEOUT
    self.alternates = None  # will be the list result from the xid lookup
    self.filtered_alternates = None  # will be a list of alternates with matching format & language; # set in getFilteredAlternates()
    self.format_codes = None  # set in getAlternates()
    self.language_code = None  # set in getAlternates()
    self.log = [ u'START: %s' % datetime.datetime.now() ]
    self.requested_isbn = ISBN
    self.requested_oclcnum = OCLC
    self.oclc_status_code = None
    self.oclcnum_isbns = None  # will be a sorted list of unique xid-isbns if an oclcnum is submitted; set by getFilteredAlternates() is called
    self.xid_url = self.makeBaseUrl( self.requested_oclcnum, self.requested_isbn )  # the initial called url
    BLESSED_FORMATS = {
      u'BA': u'Book',
      u'BB': u'Hardcover',
      u'BC': u'Paperback',
      u'DA': u'Digital'
      }  # TODO: move to settings
    self.blessed_formats = BLESSED_FORMATS.keys()

  def getAlternates(self):
    '''
    - Hits the oclc xid getVersions service; populates self.alternates
    - Attempts to populate self.format_codes & self.language_code
    '''
    assert self.OCLC_AFFILIATE_ID
    ## get straight data
    data = urllib2.urlopen( self.xid_url, timeout=self.URLLIB2_TIMEOUT ).read()  # xid_url created by __init__
    assert type(data) == str
    data = data.decode( u'utf-8' )
    assert type(data) == unicode
    json_dict = json.loads(data)
    ## validity_check
    self.oclc_status_code = ( json_dict[u'stat'] )
    if not self.oclc_status_code == u'ok':
      return { u'stat': self.oclc_status_code }
    ## go to work
    self.alternates = json_dict[u'list']
    ## ascertain format&language - isbn
    if u'form' in self.alternates[0]:
      self.format_codes = self.alternates[0]['form']
    if u'lang' in self.alternates[0]:
      self.language_code = self.alternates[0]['lang']
    ## ascertain format&language - oclc w/corresponding isbn
    if self.requested_oclcnum:
      if u'isbn' in self.alternates[0]:
        self.log.append( u'- in getAlternates; oclcnum has an isbn' )
        self.oclcnum_isbns = self.alternates[0][u'isbn']
        ## get data for this isbn
        url = u'http://xisbn.worldcat.org/webservices/xid/isbn/%s?method=getMetadata&format=json&fl=*&ai=%s' % ( self.alternates[0][u'isbn'][0], self.OCLC_AFFILIATE_ID )  # the isbn value is a list, so just take the first entry
        self.log.append( u'- in getAlternates; hitting url: %s' % url )
        data = urllib2.urlopen( url, timeout=self.URLLIB2_TIMEOUT ).read()
        assert type(data) == str
        data = data.decode( 'utf-8' )
        assert type(data) == unicode
        json_dict = json.loads(data)
        self.log.append( u'- in getAlternates; isbn metadata: %s' % json_dict )
        ## see if it contains format & language info
        if u'form' in json_dict[u'list'][0]:
          self.format_codes = json_dict[u'list'][0]['form']
        if u'lang' in json_dict[u'list'][0]:
          self.language_code = json_dict[u'list'][0]['lang']
      else:
        ## oclc w/no corresponding isbn -- leave form&language attributes initialized to None
        self.log.append( u'- in getAlternates; no isbn for this oclcnum' )
    return self.alternates

  def getFilteredAlternates( self ):
    '''
    - Runs getAlternates() if needed.
    - Attempts to populate self.filtered_alternates with a subset of self.alternates
      where language is same as original and format is in self.blessed_formats.
    '''
    if self.alternates == None:
      self.getAlternates()  # attempts to determine format and language
      self.log.append( u'- in getFilteredAlternates(); raw alternates is: %s' % self.alternates )
    if not self.oclc_status_code == u'ok':
      return { u'stat': self.oclc_status_code }
    if not self.format_codes or not self.language_code:  # can't filter if we don't have these
      self.log.append( u'- in getFilteredAlternates(); format or language not available; returning' )
      self.filtered_alternates = []
      return self.filtered_alternates
    if self.requested_isbn:
      self.filtered_alternates = self.getFilteredAlternatesFromIsbn()
    else:  # oclcnum
      self.filtered_alternates = self.getFilteredAlternatesFromOclcnum()
    return self.filtered_alternates

  def getFilteredAlternatesFromIsbn( self ):
    '''
    - Called by self.getFilteredAlternates()
    '''
    assert type(self.alternates) == list, type(self.alternates)
    filtered_list = []
    alternates = self.alternates[1:]  # removing the request-isbn
    for alt_entry in alternates:
      assert type(alt_entry) == dict
      if not u'form' in alt_entry and not u'lang' in alt_entry:
        # print u'- no format_code or language for alt_entry: %s' % alt_entry
        continue
      if not alt_entry[u'lang'] == self.language_code:
        # print u'- no language match for alt_entry: %s' % alt_entry
        continue
      for format_code in alt_entry[u'form']:
        if not format_code in self.blessed_formats and not format_code in self.format_codes:
          # print u'- no match due to invalid format code for alt_entry: %s' % alt_entry
          break
        if format_code in self.blessed_formats:
          filtered_list.append( alt_entry )
          break
    self.filtered_alternates = filtered_list
    return self.filtered_alternates

  def getFilteredAlternatesFromOclcnum(self):
    '''
    - Called by: self.getFilteredAlternates()
    - Note: we only get here if the oclcnumber has a corresponding isbn, _and_
            if language and format info are obtained from that isbn's xisbn-getMetadata call.
    - Initial logic:
      - go through every alternate entry to compile a list of unique isbns.
      - for each of those isbns, hit oclc's xisbn service to look for matches on format & language.
    - Newer logic:
      - (reason for switch: previous method took too much time)
      - just take the isbn corresponding to the request-oclc number & do the normal xisbn lookup.
      - (given this new simpler logic, the filtered-alternate isbn & oclcnum functions could be combined)
    '''
    assert self.oclcnum_isbns
    assert type(self.oclcnum_isbns) == list
    assert self.format_codes
    assert self.language_code
    ## look for matches via isbn
    filtered_list = []
    for isbn in self.oclcnum_isbns:  # probably just one
      url = u'http://xisbn.worldcat.org/webservices/xid/isbn/%s?method=getEditions&format=json&fl=*&ai=%s' % ( isbn, self.OCLC_AFFILIATE_ID )
      self.log.append( u'- in getFilteredAlternatesFromOclcnum(); hitting url: %s' % url )
      try:
        data = urllib2.urlopen( url, timeout=self.URLLIB2_TIMEOUT ).read()
      except urllib2.URLError, e:
        self.log.append( u'- in getFilteredAlternatesFromOclcnum(); URLError is: %s' % e )
        pass
      assert type(data) == str
      data = data.decode( 'utf-8' )
      assert type(data) == unicode
      json_dict = json.loads(data)
      self.log.append( u'- in getFilteredAlternatesFromOclcnum(); json_dict is: %s' % json_dict )
      possibility_list = json_dict[u'list'][1:]  # remove the known-isbn
      for possibility in possibility_list:
        if u'form' in possibility and u'lang' in possibility:
          if possibility[u'form'] == self.format_codes and possibility[u'lang'] == self.language_code:
            filtered_list.append( possibility )
    self.filtered_alternates = filtered_list
    return self.filtered_alternates

  def makeBaseUrl( self, requested_oclcnum, requested_isbn ):
    '''
    - Called by XID.__init__
    '''
    if self.requested_oclcnum:
      url = u'http://xisbn.worldcat.org/webservices/xid/oclcnum/%s?method=getEditions&format=json&fl=*&ai=%s' % ( requested_oclcnum, self.OCLC_AFFILIATE_ID )
    else:
      url = u'http://xisbn.worldcat.org/webservices/xid/isbn/%s?method=getEditions&format=json&fl=*&ai=%s' % ( requested_isbn, self.OCLC_AFFILIATE_ID )
    return url

  # end class XID
