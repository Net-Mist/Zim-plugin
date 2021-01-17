"""
This script should be called by Zim as a plugin.
it can be used in several tools :
- pdf_convert: convert a page to a pdf. This use Zim libraries to convert from wiki to markdown,
  then Pandoc to convert to pdf.
- remarkable: convert a page to a pdf, then do a request to send the file to a connected remarkable
- remarkableS: convert a page to a pdf with spacing before every subsections to have space to write on the remarkable,
  then do a request to send the file to a connected remarkable
"""
import os
import sys
import logging
import subprocess
import traceback
import pathlib

# We will use official zim tools to convert the wiki to a markdown file
from zim.formats.wiki import WikiParser
from zim.formats.markdown import Dumper
from zim.formats import ParseTreeBuilder, StubLinker


LOGNAME = "/tmp/pdf_convert.log"
LOGLEVEL = logging.DEBUG
DIRNAME = "/tmp/zim_pdf_convert"
MARKDOWN_PATH = os.path.join(DIRNAME, 'markdown.md')

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[logging.FileHandler(LOGNAME), logging.StreamHandler()],
                    level=LOGLEVEL)


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


def main(source_file, tool):
  # Open wiki file and transform it to markdown
  try:
    with open(source_file, 'r') as f:
      text = f.read()
    builder = ParseTreeBuilder()
    WikiParser()(builder, text)
    md = CustomDumper(linker=StubLinker()).dump(builder.get_parsetree())
  except Exception as e:
    tb = traceback.format_exc()
    logging.error(f"A critical error occurs when converting the wiki to markdown: {e}")
    logging.error(f"{tb}")
    return
  logging.info("conversion to markdown done")

  # get name
  name = md[0].replace(' ', '_').replace('\n', '')

  # write markdown to tmp file
  os.makedirs(DIRNAME, exist_ok=True)
  with open(MARKDOWN_PATH, 'w') as f:
    for line in md:
      f.write(line)

  variables = "--variable fontsize=12pt"
  if tool[-1] == 'S':
    variables += " --variable splitsection=1"

  # Call pandoc to convert this file to pdf
  pdf_path = os.path.join(DIRNAME, f'{name}.pdf')
  cmd = f'pandoc -N --template={pathlib.Path(__file__).parent.absolute()}/template.tex --variable geometry=a4paper,left=2cm,right=2cm,top=2cm,bottom=2cm {variables} {MARKDOWN_PATH} --pdf-engine=xelatex -o {pdf_path}'
  logging.info(f"execure command: {cmd}")
  e = subprocess.run(cmd.split(' '))
  logging.info(e)
  subprocess.run(['nautilus', DIRNAME])


if __name__ == "__main__":
  try:
    f = sys.argv[1]  # %f in vim notation, path of the source file we need to work on
    tool = sys.argv[2]  # name of the plugin that called this file. Can be pdf_convert, remarkable, remarkableS
    logging.info(f"new convert called with, f: {f}, tool: {tool}")
    main(f, tool)
  except Exception as e:
    tb = traceback.format_exc()
    logging.error(f"{tb}")
