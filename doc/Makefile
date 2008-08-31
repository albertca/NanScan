doc: docbook doxygen

docbook:
	cd src && docbook2html -o ../html nanscan.docbook && cp *.png ../html
	
doxygen:
	cd doxygen && doxygen nanscan.doxyfile

.PHONY: doxygen docbook
