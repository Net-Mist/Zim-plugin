# Zim plugins

A set of custom tools to handle several useful actions (well, at least useful for me...)


## Notes
  - it seems the wiki parser of zim 0.72.0 is broken (this is the default version in Ubuntu 20.04). Please follow 2.0.2 of https://doc.ubuntu-fr.org/zim#installation
  to install it from the official PPA 
  

## Resources
see : 
  - https://zim-wiki.org/manual/Help/Custom_Tools.html for information about how to create new tools in Zim
  
## Tools
- pdf_convert
  - convert a page to a pdf document
  - python3 PATH_TO_THIS_PROJECT/pdf_convert.py %f pdf_convert


The beginning of the document is formatted as:

"""
Title of the document
==================
option1
option2
option3
"""

options can be:
- toc: add a table of content
- s: split between section
- remarkable: add timestamp in the filename and empty pages at the end of the document
- dvs: DejaVuSans font
