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
LEVEL = logging.DEBUG
DIRNAME = "/tmp/zim_pdf_convert"
MARKDOWN_PATH = os.path.join(DIRNAME, 'markdown.md')

logging.basicConfig(filename=LOGNAME,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=LEVEL)


def main(source_file, name, remarkable):
  # Quick sanity check
  name = name.split(':')[-1]
  name = name.replace(' ', '_')
  
  # Open wiki file and transform it to markdown
  try:
    with open(source_file, 'r') as f:
      text = f.read()
    builder = ParseTreeBuilder()
    WikiParser()(builder, text)
    md = Dumper(linker=StubLinker()).dump(builder.get_parsetree())
  except Exception as e:
    logging.error(e)
    return

  # write markdown to tmp file
  os.makedirs(DIRNAME, exist_ok=True)
  with open(MARKDOWN_PATH, 'w') as f:
    for line in md:
      f.write(line)

  with open(MARKDOWN_PATH, 'r') as f:
    name = f.readline()
    name = name.replace(' ', '_')
    name = name.replace('\n', '')
  
  variables = "--variable fontsize=12pt"
  if remarkable:  
    variables += " --variable splitsection=1"
    
  

  # Call pandoc to convert this file to pdf
  pdf_path = os.path.join(DIRNAME, f'{name}.pdf')
  cmd = f'pandoc -N --template={pathlib.Path(__file__).parent.absolute()}/template.tex --variable geometry=a4paper,left=2cm,right=2cm,top=2cm,bottom=2cm {variables} {MARKDOWN_PATH} --pdf-engine=xelatex -o {pdf_path}'
  logging.info(cmd)
  e = subprocess.run(cmd.split(' '))
  logging.info(e)
  subprocess.run(['nautilus', DIRNAME])

if __name__ == "__main__":
  f = sys.argv[1]  # %f in vim notation
  p = sys.argv[2]  # %p in vim notation
  remarkable = len(sys.argv) > 3
  logging.info("new convert")
  logging.info("called with")
  logging.info(f"f: {f}")
  logging.info(f"p: {p}")
  logging.info(f"remarkable: {remarkable}")
  logging.info(sys.argv)
  logging.info(len(sys.argv))
  main(f, p, remarkable)
