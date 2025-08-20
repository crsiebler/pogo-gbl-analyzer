# Simple Makefile to run PvP ranking comparisons for multiple leagues
# Default goal runs all leagues (respects LEAGUE / PROCESSOR overrides)
.DEFAULT_GOAL := all
# Updated for unified CLI flags (analyze vs output) — deprecated vars like TOP, OLD_TOP_N, EMERGING removed.
# Usage examples:
#   make great                                # Winners/losers full dataset, default output size
#   make ultra OUTPUT_TOP_N=40 MIN_DELTA=0.2   # Show 40 winners/losers, filter small deltas
#   make master PROCESSOR=movesets ANALYZE_TOP_N=60 OUTPUT_TOP_N=30

PYTHON ?= python3
PKG    ?= pogo_gbl_analyzer
MODULE ?= $(PKG).main
DATA_DIR = data

# Tunable args (override on command line)
OUTPUT_TOP_N ?= 25          # maps to --output-top-n
MIN_DELTA ?= 0.1            # maps to --min-delta (used by winners & types)
PROCESSOR ?= all            # winners | movesets | types | ranks | all
LEAGUE ?= all               # optional single league override (great|ultra|master|all)
ANALYZE_TOP_N ?= 100        # --analyze-top-n (applies to: winners NEW subset, movesets NEW subset, types BOTH snapshots)

# Build analyze flag (movesets will fallback internally to 50 if unset)
ifdef ANALYZE_TOP_N
	ANALYZE_FLAG=--analyze-top-n $(ANALYZE_TOP_N)
endif

# File conventions (adjust here if your filenames differ)
GREAT_OLD ?= $(DATA_DIR)/cp1500_all_overall_rankings_old.csv
GREAT_NEW ?= $(DATA_DIR)/cp1500_all_overall_rankings_new.csv
ULTRA_OLD ?= $(DATA_DIR)/cp2500_all_overall_rankings_old.csv
ULTRA_NEW ?= $(DATA_DIR)/cp2500_all_overall_rankings_new.csv
MASTER_OLD ?= $(DATA_DIR)/cp10000_all_overall_rankings_old.csv
MASTER_NEW ?= $(DATA_DIR)/cp10000_all_overall_rankings_new.csv

# Helper macro
define run_one
	$(PYTHON) -m $(MODULE) $(1) $(2) $(3) --output-top-n $(OUTPUT_TOP_N) --min-delta $(MIN_DELTA) --processor $(4) $(ANALYZE_FLAG)
endef

define run_all_processors_for_league
	@for proc in winners movesets types ranks; do \
		 echo "==> League $(1) / $$proc"; \
		 $(PYTHON) -m $(MODULE) $(2) $(3) $(1) --output-top-n $(OUTPUT_TOP_N) --min-delta $(MIN_DELTA) --processor $$proc $(ANALYZE_FLAG); \
	done
endef

.PHONY: help great ultra master all

help:
	@echo "Targets: great ultra master all"
	@echo "Default: 'make' => all (respects LEAGUE=all|great|ultra|master and PROCESSOR=...|all)"
	@echo "Variables: OUTPUT_TOP_N MIN_DELTA PROCESSOR (winners|movesets|types|ranks|all) ANALYZE_TOP_N LEAGUE"
	@echo "Examples:"
	@echo "  make LEAGUE=all PROCESSOR=all"
	@echo "  make PROCESSOR=types OUTPUT_TOP_N=15"
	@echo "  make ultra OUTPUT_TOP_N=40 MIN_DELTA=0.2"
	@echo "  make master PROCESSOR=movesets ANALYZE_TOP_N=60 OUTPUT_TOP_N=30"
	@echo "  make great ANALYZE_TOP_N=50"

# Individual league runs
great:
ifeq ($(PROCESSOR),all)
	$(call run_all_processors_for_league,great,$(GREAT_OLD),$(GREAT_NEW))
else
	$(call run_one,$(GREAT_OLD),$(GREAT_NEW),great,$(PROCESSOR))
endif

ultra:
ifeq ($(PROCESSOR),all)
	$(call run_all_processors_for_league,ultra,$(ULTRA_OLD),$(ULTRA_NEW))
else
	$(call run_one,$(ULTRA_OLD),$(ULTRA_NEW),ultra,$(PROCESSOR))
endif

master:
ifeq ($(PROCESSOR),all)
	$(call run_all_processors_for_league,master,$(MASTER_OLD),$(MASTER_NEW))
else
	$(call run_one,$(MASTER_OLD),$(MASTER_NEW),master,$(PROCESSOR))
endif

# Run all sequentially
all:
ifeq ($(LEAGUE),all)
	@$(MAKE) great PROCESSOR=$(PROCESSOR)
	@$(MAKE) ultra PROCESSOR=$(PROCESSOR)
	@$(MAKE) master PROCESSOR=$(PROCESSOR)
else ifneq ($(LEAGUE),)
	@$(MAKE) $(LEAGUE) PROCESSOR=$(PROCESSOR)
else
	@$(MAKE) great PROCESSOR=$(PROCESSOR)
	@$(MAKE) ultra PROCESSOR=$(PROCESSOR)
	@$(MAKE) master PROCESSOR=$(PROCESSOR)
endif
