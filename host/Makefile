.PHONY: install bench bench-python bench-lsl bench-brainflow bench-mne bench-eegexpy clean

VENV      ?= $(HOME)/freeeeg
PY        := $(VENV)/bin/python
STAMP     := $(shell date +%Y%m%d-%H%M%S)
HOST      := $(shell hostname -s)
RESULTS   := results/bench-$(HOST)-$(STAMP).csv

install:
	scripts/install_pi.sh

bench: | results
	@echo "metric,value,unit,timestamp,host" > $(RESULTS)
	@$(PY) -m bench.bench_python     | tee -a $(RESULTS)
	@$(PY) -m bench.bench_lsl        | tee -a $(RESULTS)
	@$(PY) -m bench.bench_brainflow  | tee -a $(RESULTS)
	@$(PY) -m bench.bench_mne        | tee -a $(RESULTS)
	@$(PY) -m bench.bench_eegexpy    | tee -a $(RESULTS) || echo "# eeg-expy skipped (not installed)"
	@echo "Results saved to $(RESULTS)"

bench-python:     ; $(PY) -m bench.bench_python
bench-lsl:        ; $(PY) -m bench.bench_lsl
bench-brainflow:  ; $(PY) -m bench.bench_brainflow
bench-mne:        ; $(PY) -m bench.bench_mne
bench-eegexpy:    ; $(PY) -m bench.bench_eegexpy

results:
	@mkdir -p results

clean:
	rm -rf __pycache__ bench/__pycache__
