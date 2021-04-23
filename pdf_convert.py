"""
This script should be called by Zim as a plugin.
The command Zim need to run is :

python3 PATH_TO_THIS_FILE/pdf_convert.py %f %d
"""
import logging
import os
import pathlib
import re
import subprocess
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

# We will use official zim tools to convert the wiki to a markdown file
from zim.formats import ParseTreeBuilder, StubLinker
from zim.formats.markdown import Dumper
from zim.formats.wiki import WikiParser

DIRNAME = "/tmp/zim_pdf_convert"
LOGNAME = DIRNAME + "/pdf_convert.log"
LOGLEVEL = logging.DEBUG
MARKDOWN_PATH = os.path.join(DIRNAME, 'markdown.md')
os.makedirs(DIRNAME, exist_ok=True)

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[logging.FileHandler(LOGNAME), logging.StreamHandler()],
                    level=LOGLEVEL)


class CustomDumper(Dumper):
  # This custom dumper is needed to correctly parse code blocks and images from Zim
  def __init__(self, attachment_dir, linker=None, template_options=None):
    super().__init__(linker, template_options)
    self.attachment_dir = attachment_dir

  def dump_object_fallback(self, tag, attrib, strings=None):
    # dump code as markdown code block with language specification
    if attrib['type'] == 'code':
      lang = attrib['lang']
      out = [f"```{lang}\n"] \
          + self.prefix_lines('', strings) \
          + [f"```\n"]
      return out

    # dump object as verbatim block
    return self.prefix_lines('\t', strings)

  def dump_img(self, tag, attrib, strings=None):
    """
    Args:
      tag: always "img"
      attrib: dictionary with key 'src' and maybe 'width' or 'height'
    """
    src = self.linker.img(attrib['src'])
    # update src to remove '../' and '~'
    home = str(Path.home())
    src = src.replace('~', home)
    src = src.replace('../', '/'.join(self.attachment_dir.split('/')[:-1])+'/')
    src = src.replace('./', self.attachment_dir+'/')

    text = attrib.get('alt', '')

    param_keys = ['width', 'height']
    params = ""
    for key in param_keys:
      if key in attrib:
        params += f"{key}={attrib[key]}"

    if params:
      return ['![%s](%s){ %s }' % (text, src, params)]
    else:
      return ['![%s](%s)' % (text, src)]


def parse_zim(source_file, attachment_dir):
  with open(source_file, 'r') as f:
    text = f.read()
  builder = ParseTreeBuilder()
  WikiParser()(builder, text)
  md = CustomDumper(attachment_dir, linker=StubLinker()).dump(builder.get_parsetree())
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
  with open(MARKDOWN_PATH, 'w') as f:
    for line in md:
      f.write(line)


def get_variables(md):
  regex_to_function = {
      "^s( |\t)*$": {'var': " --variable splitsection=1"},
      "^toc( |\t)*$": {'var': " --variable toc"},
      "^remarkable( |\t)*$": {'var': " --variable endemptypage=1", 'remarkable': True},
      "^dvs( |\t)*$": {'var': " --variable mainfont:DejaVuSans.ttf"},
  }
  # TODO add date option
  v = "--variable fontsize=12pt"
  remarkable = False
  for l in md[2:]:
    if l == '\n':
      return v, remarkable
    for k in regex_to_function.keys():
      if bool(re.match(k, l.replace('\n', ''))):
        v += regex_to_function[k]['var']
        if 'remarkable' in regex_to_function[k]:
          remarkable = True
  return v, remarkable


def main(source_file, attachment_dir):
  md = parse_zim(source_file, attachment_dir)
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
  # the command line is "python3 /path/pdf_convert.py %f %d"
  logging.info(f"{sys.argv}")
  try:
    f = sys.argv[1]  # %f in vim notation, path of the source file we need to work on
    d = sys.argv[2]  # %d in vim notation, the attachment directory
    logging.info(f"pdf_convert called with, f: {f}, d: {d}")
    main(f, d)
  except Exception as e:
    tb = traceback.format_exc()
    logging.error(f"{tb}")
