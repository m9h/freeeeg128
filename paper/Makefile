# FreeEEG128 synthesis paper — Sweave + tectonic build
#
#   make          → paper.pdf
#   make clean    → remove build artefacts
#
# Requires: R (for Sweave), tectonic

PAPER = paper

.PHONY: all clean tidy

all: $(PAPER).pdf

$(PAPER).tex: $(PAPER).Rnw
	R CMD Sweave $(PAPER).Rnw

R_TEXMF := $(shell Rscript -e 'cat(R.home("share"))')/texmf

$(PAPER).pdf: $(PAPER).tex refs.bib
	TEXINPUTS=".:$(R_TEXMF)/tex/latex//:" tectonic --keep-logs $(PAPER).tex

tidy:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log $(PAPER).out \
	      $(PAPER).toc Rplots.pdf

clean: tidy
	rm -f $(PAPER).tex $(PAPER).pdf $(PAPER)-*.pdf
