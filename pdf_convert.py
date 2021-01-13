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
import pathlib

# We will use official zim tools to convert the wiki to a markdown file
from zim.formats.wiki import WikiParser
from zim.formats.markdown import Dumper
from zim.formats import ParseTreeBuilder, StubLinker


LOGNAME = "/tmp/pdf_convert.log"
LOGLEVEL = logging.DEBUG
DIRNAME = "/tmp/zim_pdf_convert"
MARKDOWN_PATH = os.path.join(DIRNAME, 'markdown.md')

logging.basicConfig(filename=LOGNAME,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=LOGLEVEL)


def main(source_file, tool):
  # Open wiki file and transform it to markdown
  try:
    with open(source_file, 'r') as f:
      text = f.read()
    builder = ParseTreeBuilder()
    WikiParser()(builder, text)
    md = Dumper(linker=StubLinker()).dump(builder.get_parsetree())
  except Exception as e:
    logging.error(f"A critical error occurs when converting the wiki to markdown: {e}")
    return
  logging.info("conversion to markdown done")  

  # write markdown to tmp file
  os.makedirs(DIRNAME, exist_ok=True)
  with open(MARKDOWN_PATH, 'w') as f:
    # the first line of the markdown define the name
    firstline = f.readline()
    name = firstline.replace(' ', '_').replace('\n', '')
    f.write(firstline)
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
  f = sys.argv[1]  # %f in vim notation, path of the source file we need to work on
  tool = sys.argv[3]  # name of the plugin that called this file. Can be pdf_convert, remarkable, remarkableS
  logging.info(f"new convert called with, f: {f}, tool: {tool}")
  main(f, tool)
