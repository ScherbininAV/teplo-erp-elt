# Automated ELT Pipeline for Unit Economics

## Architecture
Extract, Load, Transform (ELT) pattern.

## Stack
* **Language:** Python 3.11 (Pandas, SQLAlchemy, python-dotenv)
* **Database:** PostgreSQL 16
* **Orchestration:** Windows Task Scheduler / Batch scripting

## Workflow
1. **Extract:** Raw transactional data and SKU catalogs are extracted from local Excel files.
2. **Load:** Idempotent injection into PostgreSQL normalized tables (`sales_journal`, `sku_catalog`) using SQLAlchemy ORM engine.
3. **Transform:** Unit economics (revenue, cost, marketplace fees, net profit) are calculated in real-time via PostgreSQL Views (`v_unit_economics`) maintaining strict data granularity.
4. **Export:** Resulting analytical dashboard is flat-filed back to `.xlsx` for stakeholder review.