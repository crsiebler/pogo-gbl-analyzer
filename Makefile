# Simple Makefile to run PvP ranking comparisons for multiple leagues
# Usage examples:
#   make great
#   make ultra TOP=15 MIN_DELTA=0.2
#   make master OLD_TOP_N=50 EMERGING=1

PYTHON ?= python3
PKG    ?= pogo_gbl_analyzer
MODULE ?= $(PKG).main
DATA_DIR = data

# Tunable args (override on command line)
TOP ?= 25
MIN_DELTA ?= 0.1
OLD_TOP_N ?=
EMERGING ?= 0

# Build optional flags
ifdef OLD_TOP_N
  OLD_TOP_FLAG=--old-top-n $(OLD_TOP_N)
endif
ifeq ($(EMERGING),1)
  EMERGING_FLAG=--include-emerging
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
	$(PYTHON) -m $(MODULE) $(1) $(2) $(3) --top $(TOP) --min-delta $(MIN_DELTA) $(OLD_TOP_FLAG) $(EMERGING_FLAG)
endef

.PHONY: help great ultra master all

help:
	@echo "Available targets:"
	@echo "  make great   - Compare Great League (1500 CP) rankings"
	@echo "  make ultra   - Compare Ultra League (2500 CP) rankings"
	@echo "  make master  - Compare Master League (10000 CP) rankings"
	@echo ""
	@echo "Override variables: TOP MIN_DELTA OLD_TOP_N EMERGING=1"
	@echo "Examples:"
	@echo "  make ultra TOP=40 MIN_DELTA=0.2"
	@echo "  make master OLD_TOP_N=50 EMERGING=1"

# Individual league runs
great:
	$(call run_compare,$(GREAT_OLD),$(GREAT_NEW),great)

ultra:
	$(call run_compare,$(ULTRA_OLD),$(ULTRA_NEW),ultra)

master:
	$(call run_compare,$(MASTER_OLD),$(MASTER_NEW),master)

# Run all sequentially
all: great ultra master
