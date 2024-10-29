import argparse
import os
import re
import xml.etree.ElementTree as ET
import zipfile

from parser import BookParser


UMLAUTE = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss', ord(' '): '_'}

        

def parse_toc(toc, zip_dir):
    nav = []
    root = ET.fromstring(toc.decode('utf-8'))
    namespace = re.search(r'\{.*\}', root.tag).group(0)

    if namespace:
        print(f'namespace: {namespace}')
    else:
        namespace = ''

    namespaces = {'ns': namespace[1:-1]}
    navmap = root.find('ns:navMap', namespaces)

    for chapter in navmap:
        nav_label = chapter.find('ns:navLabel', namespaces)
        heading = nav_label.find('ns:text', namespaces).text
        heading = heading.replace('.', '') # formatting
        file = zip_dir + '/' + chapter.find('ns:content', namespaces).get('src')
        nav.append((heading, file))
    
    # return array of tuple: (heading, file)
    return nav


def write_toc(file, name, toc):
    with open(file, 'w') as f:
        f.write(f'# {name}\n\n\n')

        for book, filename in toc:
            f.write(f'[[{filename}|{book}]]\n\n')



def main():
    # PARSER
    parser = argparse.ArgumentParser(description='ELB-CSV EPUB to Markdown converter')
    parser.add_argument('-i', help="Path to ELB-CSV EPUB", required=True)
    parser.add_argument('-o', help="Path to output directory", required=True)
    args = parser.parse_args()


    epub = args.i
    export_dir = args.o
    name = 'ELB-CSV'

    os.mkdir(export_dir)
    

    with zipfile.ZipFile(epub) as zip:
        toc_list = [name for name in zip.namelist() if '/toc.ncx' in name]
        if len(toc_list) != 1:
            raise Exception('Found none or multiple table of content(s)')
        toc = zip.read(toc_list[0])
        # get root dir
        zip_dir = toc_list[0].replace('/toc.ncx', '')
        nav = parse_toc(toc, zip_dir)

        idx = 1
        toc = []
        for item in nav:
            heading = item[0]
            file = item[1]
            content = zip.read(file).decode("utf-8")

            path = f'{export_dir}/{idx:02d}-{heading.translate(UMLAUTE)}'
            os.mkdir(path)

            parser = BookParser(path, heading, name)
            parser.feed(content)

            if not parser.isWritten:
                os.rmdir(path)
            else:
                idx += 1
                toc.append((heading, parser.generate_filename(0)))

        # write global table of content
        path = f'{export_dir}/{name}.md'
        write_toc(path, name, toc)

        



if __name__ == '__main__':
    main()

