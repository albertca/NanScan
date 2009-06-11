import poppler
import sys

document = poppler.document_new_from_file(sys.argv[1], None)
#self.document = poppler.document_new_from_file (uri, None)
print "PAGES: ", document.get_n_pages()
print "SIZE: ", current_page.get_size()


# Font Info:
font_info = poppler.FontInfo(self.document)
iter = font_info.scan(self.n_pages)

print iter.get_full_name()

while iter.next():
    print iter.get_full_name()
