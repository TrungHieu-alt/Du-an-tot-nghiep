LATEXMK=latexmk
MAIN=main

.PHONY: pdf clean clean-all page-count

pdf:
	$(LATEXMK) -xelatex -interaction=nonstopmode -synctex=1 $(MAIN).tex

page-count:
	pdfinfo $(MAIN).pdf | grep '^Pages:'

clean:
	$(LATEXMK) -c $(MAIN).tex

clean-all:
	$(LATEXMK) -C $(MAIN).tex
