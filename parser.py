import re
from html.parser import HTMLParser


class BookParser(HTMLParser):

    isChapter = False
    isParagraph = False
    isVerse = False
    isVerseNo = False
    isAnchor = False
    isWritten = False
    curChapterNo = -1
    chapters = []
    curVerseNo = -1
    curVerse = ''
    verses = []


    def __init__(self, path, bookName, bible):
        HTMLParser.__init__(self)
        self.path = path
        self.bookName = bookName
        self.bible = bible


    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            for attr in attrs:
                if attr[0] == 'class' and attr[1] == 'book-name':
                    self.isChapter = True
                    break

                if attr[0] == 'class' and attr[1] == 'verse-no':
                    self.isVerseNo = True
                    self.isVerse = True
                    break


        elif tag == 'p' and not attrs:
            self.isParagraph = True
           
        elif tag == 'a':
            self.isAnchor = True 
        
        elif 'h' in tag:
            self.isPragraph = False
        
        elif tag == 'small':
            self.curVerse += '<small>'
        
        elif tag == 'small':
            self.curVerse += '<small>'
        
        elif tag == 'i':
            self.curVerse += '*'


    def handle_endtag(self, tag):
        if tag == 'p':
            self.isParagraph = False

        elif tag == 'a':
            self.isAnchor = False

        elif tag == 'body':
            # handle last verse
            if self.curVerseNo > 0:
                self.verses.append((self.curVerseNo, self.curVerse.strip()))
                self.write_chapter(False)

                self.write_overview()
                self.isWritten = True

        elif tag == 'small':
            self.curVerse += '</small>'

        elif tag == 'i':
            self.curVerse += '*'


    def handle_data(self, data):
        if self.isChapter:
            chapter = 1
            try:
                chapter = re.search(r'[0-9]+$', data).group(0)
            except:
                pass

            self.isChapter = False

            # handle last verse from last chapter
            if self.curVerseNo > 0:
                self.verses.append((self.curVerseNo, self.curVerse.strip()))

            self.curVerseNo = -1
            self.curVerse = ''

            self.write_chapter(True)

            self.curChapterNo = int(chapter)
            self.chapters.append(int(chapter))

        if self.isVerseNo:
            if self.curVerseNo > 0:
                self.verses.append((self.curVerseNo, self.curVerse.strip()))
            
            self.curVerseNo = int(data)
            self.curVerse = ''
            self.isVerseNo = False
            return

        if self.isParagraph and self.isVerse and not self.isAnchor and not self.isVerseNo:
            self.curVerse += data


    def write_chapter(self, hasNextChapter):
        if not len(self.verses):
            return
        if self.curChapterNo <= 0:
            return

        print(f'{self.bookName} {self.curChapterNo:02d}')
        links = self.generate_links(hasNextChapter)

        filename = self.generate_filename(self.curChapterNo, md=True)
        with open(f'{self.path}/{filename}', 'w') as f:
            f.write(f'# {self.bookName} {self.curChapterNo}\n\n')
            f.write(links)
            f.write('\n***\n\n')

            for no, text in self.verses:
                f.write(f'###### v{no}\n')
                f.write(text)
                f.write('\n\n')

            f.write('***\n')
            f.write(links)
            f.write('\n')

        self.verses.clear()


    def write_overview(self):
        filename = self.generate_filename(0, md=True)
        with open(f'{self.path}/{filename}', 'w') as f:
            f.write(f'links: [[{self.bible}]]\n')
            f.write(f'# {self.bookName}\n\n')
            firstChapter = self.generate_filename(1)
            f.write(f'[[{firstChapter}|Start Reading →]]\n\n***\n\n')

            if len(self.chapters) <= 1:
                return
            
            f.write(f'## Kapitel\n\n')
            for chapter in self.chapters:
                link = self.generate_filename(chapter)
                title = self.generate_chapter_heading(chapter)
                f.write(f'[[{link}|{title}]]\n\n')
            
        self.chapters.clear()


    def generate_chapter_heading(self, chapter):
        return f'{self.bookName} {chapter:02d}'


    def generate_filename(self, chapter, md=False):
        filename = ''
        if chapter == 0:
            filename = f'{self.bookName}'
        else:
            filename = f'{self.bookName}-{chapter:02d}'
        if md:
            filename += '.md'
        return filename


    def generate_links(self, hasNextChapter):
        link = ''
        if self.curChapterNo == 1 and hasNextChapter:
            # [[Genesis]] | [[Gen-02|Genesis 02 →]]
            
            nextChapterFile = self.generate_filename(self.curChapterNo+1)
            nextChapter = self.generate_chapter_heading(self.curChapterNo+1)
            link = f'[[{self.bookName}]] | [[{nextChapterFile}|{nextChapter} →]]'
        
        elif self.curChapterNo == 1 and not hasNextChapter:
            # [[Genesis]]
            link = f'[[{self.bookName}]]'

        elif self.curChapterNo > 1 and not hasNextChapter:
            # [[Gen-49|← Genesis 49]] | [[Genesis]]
            prevChapterFile = self.generate_filename(self.curChapterNo-1)
            prevChapter = self.generate_chapter_heading(self.curChapterNo-1)
            link = f'[[{prevChapterFile}|← {prevChapter}]] | [[{self.bookName}]]'

        else:
            # [[Gen-01|← Genesis 01]] | [[Genesis]] | [[Gen-03|Genesis 03 →]]
            prevChapterFile = self.generate_filename(self.curChapterNo-1)
            prevChapter = self.generate_chapter_heading(self.curChapterNo-1)
            nextChapterFile = self.generate_filename(self.curChapterNo+1)
            nextChapter = self.generate_chapter_heading(self.curChapterNo+1)
            link = f'[[{prevChapterFile}|← {prevChapter}]] | [[{self.bookName}]] | [[{nextChapterFile}|{nextChapter} →]]'

        return link



