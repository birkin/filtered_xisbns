_( formatted in [markdown](http://daringfireball.net/projects/markdown/) )_

About
=====

This [django] [DJA] webapp provides a simple wrapper around a class that takes an [ISBN] [ISB], grabs a list of alternate ISBNs from [OCLC's xisbn service] [OXI], filters them on language and format, and returns the filtered list.

The filtering class matches the original's language exactly, and matches a list of specified formats.

Purpose: To offer user a list of relevant alternate books. Assumption: same language, and certain formats, are relevant (i.e. paperpack & hardcover are similar, paperback & audio less so).

[DJA]: https://www.djangoproject.com
[ISB]: http://en.wikipedia.org/wiki/ISBN
[OXI]: http://www.oclc.org/xisbn/default.htm

---


On this page...
===============

- Common usage
- Notes
- License

---
  
  
Common usage
============

Webapp
------

    >>> import json, urllib2
    >>> output = urllib2.urlopen( u'http://127.0.0.1/easyborrow/xisbn/isbn/9780688002305/' ).read()
    >>> json_dict = json.loads( output )
    >>> sorted( json_dict.keys() )
    [u'documentation', u'request', u'response']
    >>> 
    >>> sorted( json_dict[u'request'].keys() )
    [u'number', u'number_type']
    >>> json_dict[u'request']['number'] 
    u'9780688002305'
    >>> json_dict[u'request']['number_type']
    u'isbn'
    >>> 
    >>> sorted( json_dict[u'response'].keys() )
    [u'alternates', u'filtered_alternates', u'status']
    >>> len( json_dict[u'response']['alternates'] )
    70
    >>> len( json_dict[u'response']['filtered_alternates'] )
    27
    >>> json_dict[u'response']['status']
    u'request_ok'

    >>> ## 'callback' works, too
    >>> print urllib2.urlopen( u'http://127.0.0.1/easyborrow/xisbn/isbn/9780688002305/?callback=abc' ).read()
    abc({
      "documentation": "url_coming", 
      "request": {
        "number": "9780688002305", 
        ... [snip] ...


( for structure of 'alternates' and 'filtered_alternates' entries, see Class, below )

Class
-----

    >>> from models import XID
    >>> x = XID( isbn=u'1234', settings={u'OCLC_AFFILIATE_ID': u'the_id'} )
    >>> x.getFilteredAlternates()
    >>> assert type( x.filtered_alternates ) == list
    >>> assert sorted( x.filtered_alternates[0].keys() ) == [
          u'author', u'city', u'ed', 
          u'form', u'isbn', u'lang', 
          u'oclcnum', u'publisher', u'title', 
          u'url', u'year'] )

    ## other info...

    ## x.alternates
    >>> assert type( x.alternates ) == list  # x.alternates are oclc's results; the first is the requested isbn
    >>> assert sorted( x.alternates[0].keys() ) == [
          u'author', u'city', u'ed', 
          u'form', u'isbn', u'lang', 
          u'oclcnum', u'publisher', u'title', 
          u'url', u'year'] )
    >>> assert x.alternates[0][u'isbn'] == u'1234'  # again, the first entry is the requested isbn
    >>> assert x.language_code == x.alternates[0][u'lang']  # the first x.alternates entry's language is stored for filtered_alternates checks

    ## filtering formats
    >>> assert type( x.blessed_formats ) == list  # x.alternates entries won't make it into x.filtered_alternates unless they contain a blessed-format

    ## x.filtered_alternates
    >>> filtered_alternate_entry_format_check = u'init'
    >>> for format in filtered_alternate_entry[u'form']:
    ...   if format in x.blessed_formats:
    ...     filtered_alternate_entry_format_check = u'match_found'
    >>> assert filtered_alternate_entry_format_check == u'match_found'  # filtered_alternate_entries match original on language, and contain a 'blessed_format'
        

---


Notes
=====

- [OCLC's xisbn service] [OXI] has rules for different levels of usage. This code assumes an affiliate-ID has been registered.

- Experimental / under-construction -- filtered alternates on oclc number...

        >>> import json, requests
        >>> url = u'http://127.0.0.1/easyborrow/xisbn/oclcnum/23832012/'
        >>> r = requests.get( url )
        >>> json_dict = json.loads( r.text )
        >>> json_dict.keys()
        [u'documentation', u'request', u'response']
        >>> sorted( json_dict[u'request'].keys() )
        [u'number', u'number_type']
        >>> sorted( json_dict[u'response'].keys() )
        [u'alternates', u'filtered_alternates', u'status']
        >>> len( json_dict[u'response'][u'alternates'] )
        262
        >>> len( json_dict[u'response'][u'filtered_alternates'] )
        10


- code contact info: [birkin_diana@brown.edu] [BJD]

[BJD]: mailto://birkin_diana@brown.edu
[OXI]: http://www.oclc.org/xisbn/default.htm

---


License
=======

[xisbn_app] [APP] by [Brown University Library] [BUL]
is licensed under a [Creative Commons Attribution-ShareAlike 3.0 Unported License] [CC BY-SA 3.0]

[APP]: https://github.com/birkin/filtered_xisbns/
[BUL]: https://library.brown.edu
[CC BY-SA 3.0]: http://creativecommons.org/licenses/by-sa/3.0/

Human readable summary:

    You are free:
    - to Share — to copy, distribute and transmit the work
    - to Remix — to adapt the work
    - to make commercial use of the work

    Under the following conditions:
    - Attribution — You must attribute the work to:
      Brown University Library - http://library.brown.edu/its/software/
    - Share Alike — If you alter, transform, or build upon this work, 
      you may distribute the resulting work only under the same 
      or similar license to this one.  

---
