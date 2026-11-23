# DealerOS – Design Decisions

This document explains the key technical and business decisions made while implementing the DealerOS reconciliation application.

## 1. Organization-Based Data Isolation

Organization ownership is determined using the `locations.csv` dataset.

Each location is associated with an organization. Reconciliation results are filtered using the selected organization to prevent records belonging to another organization from being exposed.

## 2. Independent Storage of System B Entries

System B entries are stored independently instead of enforcing a direct foreign-key relationship with System A records.

**Reason:**
- Preserve orphan records.
- Retain duplicate entries.
- Avoid losing source data during import.
- Support accurate reconciliation.

## 3. System A Total Value as the Comparison Reference

System B values are compared against System A's `total_value`, not `base_value`.

**Reason:** The reconciliation must compare the final total amount rather than the base amount.

## 4. Handling Split Entries

A System A record may have multiple corresponding System B entries.

When the combined System B value equals the System A `total_value`, the entries are treated as a valid split.

**Reason:** Multiple entries do not automatically indicate a discrepancy.

## 5. Duplicate Entry Detection

Multiple System B entries for the same normalized record reference are identified as duplicates when they do not reconcile with the System A total.

**Reason:** Duplicate records must remain visible for investigation rather than being silently discarded.

## 6. Handling Blank Values

Blank System B values are treated as `NULL` or unknown values instead of being converted to zero.

**Reason:** A missing value and a genuine zero value have different meanings in financial reconciliation.

## 7. Record Reference Normalization

Record references are normalized to handle differences in:
- Uppercase and lowercase characters.
- Spaces.
- Hyphens.

Examples:

- `rec1034`
- `REC - 1070`
- `1112`

**Reason:** Formatting differences should not prevent matching records.

## 8. Preservation of Dirty Data

Imported source records are retained even when they contain incomplete or inconsistent information.

Examples include:
- Blank values.
- Missing actor IDs.
- Orphan references.
- Duplicate entries.

**Reason:** The reconciliation process should identify data-quality problems rather than hide them by deleting source records.

## 9. Voided Records

Voided System A records are excluded from the disagreement results.

**Reason:** Voided records should not be treated as active reconciliation obligations.

## 10. Disagreement Categories

The application identifies the following disagreement types:

| Category | Description |
|---|---|
| `MISSING_IN_B` | System A record is missing in System B. |
| `ORPHAN_IN_B` | System B entry has no matching System A record. |
| `DUPLICATE_IN_B` | Multiple System B entries exist for a record. |
| `VALUE_MISMATCH` | System A and System B values differ. |
| `DATE_MISMATCH` | Record dates do not match. |
| `LOCATION_MISMATCH` | Record locations do not match. |

## 11. Database Choice

SQLite is used as the database for this implementation.

**Reason:** SQLite provides a lightweight database suitable for local development and assessment execution without requiring a separate database server.

## 12. Frontend Implementation

The user interface is implemented using Django templates, HTML, CSS, and JavaScript.

**Reason:** A single Django application keeps the setup simple and avoids the additional configuration required for a separate React frontend.

## 13. Testing Approach

Automated tests are implemented using Django's testing framework.

The test suite covers:
- Missing records.
- Orphan records.
- Value mismatches.
- Duplicate entries.
- Valid split entries.
- Date mismatches.
- Blank System B values.
- Voided records.
- Organization-level data isolation.

**Current test result:** 10 tests passed.

---

**Project:** DealerOS – System A & System B Reconciliation Dashboard  
**Assignment:** AdosX DealerOS Assessment