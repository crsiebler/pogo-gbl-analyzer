# Simple Makefile to run PvP ranking comparisons for multiple leagues
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
PROCESSOR ?= winners        # winners | movesets | types
ANALYZE_TOP_N ?=            # --analyze-top-n (applies to: winners NEW subset, movesets NEW subset, types BOTH snapshots)

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
define run_compare
	$(PYTHON) -m $(MODULE) $(1) $(2) $(3) --output-top-n $(OUTPUT_TOP_N) --min-delta $(MIN_DELTA) --processor $(PROCESSOR) $(ANALYZE_FLAG)
endef

.PHONY: help great ultra master all

help:
	@echo "Available targets:"
	@echo "  make great   - Compare Great League (1500 CP) rankings"
	@echo "  make ultra   - Compare Ultra League (2500 CP) rankings"
	@echo "  make master  - Compare Master League (10000 CP) rankings"
	@echo ""
	@echo "Override variables: OUTPUT_TOP_N MIN_DELTA PROCESSOR=winners|movesets|types ANALYZE_TOP_N"
	@echo "Examples:"
	@echo "  make ultra OUTPUT_TOP_N=40 MIN_DELTA=0.2"
	@echo "  make master PROCESSOR=types OUTPUT_TOP_N=15"
	@echo "  make master PROCESSOR=types ANALYZE_TOP_N=100 OUTPUT_TOP_N=15"
	@echo "  make master PROCESSOR=movesets ANALYZE_TOP_N=60 OUTPUT_TOP_N=30"
	@echo "  make great ANALYZE_TOP_N=50"

# Individual league runs
great:
	$(call run_compare,$(GREAT_OLD),$(GREAT_NEW),great)

ultra:
	$(call run_compare,$(ULTRA_OLD),$(ULTRA_NEW),ultra)

master:
	$(call run_compare,$(MASTER_OLD),$(MASTER_NEW),master)

# Run all sequentially
all: great ultra master
