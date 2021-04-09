"""
This script should be called by Zim as a plugin.
it can be used in several tools :
- pdf_convert: convert a page to a pdf. This use Zim libraries to convert from wiki to markdown,
  then Pandoc to convert to pdf.
- remarkable: convert a page to a pdf, then do a request to send the file to a connected remarkable
- remarkableS: convert a page to a pdf with spacing before every subsections to have space to write on the remarkable,
  then do a request to send the file to a connected remarkable
"""
import re
import os
from pathlib import Path
import sys
import logging
import subprocess
import traceback
import pathlib
from datetime import date, datetime
from xml.etree.ElementTree import parse

# We will use official zim tools to convert the wiki to a markdown file
from zim.formats.wiki import WikiParser
from zim.formats.markdown import Dumper
from zim.formats import ParseTreeBuilder, StubLinker


LOGNAME = "/tmp/zim_pdf_convert/pdf_convert.log"
LOGLEVEL = logging.DEBUG
DIRNAME = "/tmp/zim_pdf_convert"
MARKDOWN_PATH = os.path.join(DIRNAME, 'markdown.md')
os.makedirs(DIRNAME, exist_ok=True)

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[logging.FileHandler(LOGNAME), logging.StreamHandler()],
                    level=LOGLEVEL)

# This custom dumper is needed to correctly parse code blocks from Zim


class CustomDumper(Dumper):
  def dump_object_fallback(self, tag, attrib, strings=None):

    # dump code as... code
    if attrib['type'] == 'code':
      lang = attrib['lang']
      out = [f"```{lang}\n"] \
          + self.prefix_lines('', strings) \
          + [f"```\n"]
      return out

    # dump object as verbatim block
    return self.prefix_lines('\t', strings)


def parse_zim(source_file):
  with open(source_file, 'r') as f:
    text = f.read()
  builder = ParseTreeBuilder()
  WikiParser()(builder, text)
  md = CustomDumper(linker=StubLinker()).dump(builder.get_parsetree())
  logging.info("conversion to markdown done")
  return md


def get_filename(md):
  return md[0].replace(' ', '_').replace('\n', '')


def add_markdown_header(md):
  # Put a nice title in the markdown file
  # syntax is :
  # ---
  # title: My super document
  # date: 19 mars 2021
  # ---
  new_md = ["---\n",
            f"title: {md[0]}",
            f"date: {date.today().strftime('%B %d, %Y')}\n",
            "---\n"]

  for i in range(2, len(md)):
    if md[i] == '\n':
      return new_md+md[i:]


def save_markdown(md):
  # write markdown to tmp file
  home = str(Path.home())
  with open(MARKDOWN_PATH, 'w') as f:
    for line in md:
      line = line.replace('~', home)
      f.write(line)


def get_variables(md):
  regex_to_function = {
      "^s( |\t)*$": {'var': " --variable splitsection=1"},
      "^toc( |\t)*$": {'var': " --variable toc"},
      "^remarkable( |\t)*$": {'var': " --variable endemptypage=1", 'remarkable': True},
      "^dvs( |\t)*$": {'var': " --variable mainfont:DejaVuSans.ttf"},
  }
  v = "--variable fontsize=12pt"
  remarkable = False
  for l in md[2:]:
    if l == '\n':
      return v, remarkable
    for k in regex_to_function.keys():
      if bool(re.match(k, l.replace('\n', ''))):
        v += regex_to_function[k]['var']
        print(regex_to_function[k]['var'])
        if 'remarkable' in regex_to_function[k]:
          remarkable = True
  return v, remarkable


def main(source_file):
  md = parse_zim(source_file)
  filename = get_filename(md)
  variables, is_remarkable = get_variables(md)
  md = add_markdown_header(md)
  save_markdown(md)

  if is_remarkable:
    pdf_path = os.path.join(DIRNAME, f'{filename}_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.pdf')
  else:
    pdf_path = os.path.join(DIRNAME, f'{filename}.pdf')

  # Call pandoc to convert this file to pdf
  cmd = f'pandoc -N --template={pathlib.Path(__file__).parent.absolute()}/template.tex --variable geometry=a4paper,left=2cm,right=2cm,top=2cm,bottom=2cm {variables} {MARKDOWN_PATH} --pdf-engine=xelatex -o {pdf_path}'
  logging.info(f"execute command: {cmd}")
  e = subprocess.run(cmd.split(' '))
  logging.info(e)
  subprocess.run(['nautilus', DIRNAME])


if __name__ == "__main__":
  # the command line is "python3 /path/pdf_convert.py %f"
  try:
    f = sys.argv[1]  # %f in vim notation, path of the source file we need to work on
    logging.info(f"pdf_convert called with, f: {f}")
    main(f)
  except Exception as e:
    tb = traceback.format_exc()
    logging.error(f"{tb}")
