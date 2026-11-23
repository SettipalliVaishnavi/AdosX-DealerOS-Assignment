# DealerOS – Reconciliation Dashboard

## 1. Project Overview

DealerOS is a Django-based reconciliation application designed to compare records from System A and System B across multiple organizations.

The application identifies discrepancies between the two systems, helping users detect missing records, duplicate entries, orphan records, and mismatched values, dates, and locations.

## 2. Technology Stack

- **Backend:** Python, Django
- **API:** Django REST Framework
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Data Import:** CSV

## 3. Features

- Import CSV datasets from System A, System B, and Locations.
- Organization-based data isolation.
- Identify records missing from System B.
- Detect orphan records in System B.
- Identify duplicate System B entries.
- Detect value mismatches.
- Detect date and location mismatches.
- Support valid split entries.
- Preserve incomplete and dirty source records.
- Filter disagreements by reason.
- Sort disagreement records by value.
- Display reconciliation results in a dashboard.

## 4. Dataset Information

The application processes the following datasets:

| Dataset | Records |
|---|---:|
| Locations | 5 |
| System A | 120 |
| System B | 121 |

All 121 System B entries are retained during import.

## 5. Reconciliation Rules

- System B values are compared against System A `total_value`.
- Multiple System B entries are considered valid split entries when their combined value matches the System A total.
- Duplicate entries are identified separately.
- Blank System B values are treated as unknown (`NULL`), not zero.
- Record references are normalized to handle differences in casing, spaces, and hyphens.
- Orphan System B entries are preserved.
- Voided System A records are excluded from disagreement results.
- Organization ownership is determined using the Locations dataset.

## 6. Disagreement Categories

| Reason | Description |
|---|---|
| `MISSING_IN_B` | A System A record has no matching System B entry. |
| `ORPHAN_IN_B` | A System B entry has no matching System A record. |
| `DUPLICATE_IN_B` | Multiple System B entries exist for a record. |
| `VALUE_MISMATCH` | System A and System B values do not match. |
| `DATE_MISMATCH` | Record dates differ between systems. |
| `LOCATION_MISMATCH` | Record locations differ between systems. |

## 7. Project Structure

```text
AdosX_DealerOS_Assignment/
│
├── backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── reconcile/
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── import_data.py
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── page_views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   ├── data/
│   │   ├── locations.csv
│   │   ├── system_a.csv
│   │   └── system_b.csv
│   │
│   ├── templates/
│   │   └── reconcile/
│   │       └── dashboard.html
│   │
│   └── manage.py
│
├── .gitignore
├── README.md
├── DECISIONS.md
└── requirements.txt
```

## 8. Installation and Setup

### Step 1: Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd AdosX_DealerOS_Assignment
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Navigate to the backend

```bash
cd backend
```

### Step 6: Apply database migrations

```bash
python manage.py migrate
```

### Step 7: Import the datasets

```bash
python manage.py import_data
```

### Step 8: Start the development server

```bash
python manage.py runserver
```

Open the dashboard:

http://127.0.0.1:8000/

## 9. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/organizations/` | Get available organizations |
| GET | `/api/disagreements/?org=ORG-A` | Get organization disagreements |
| GET | `/api/disagreements/?org=ORG-A&reason=VALUE_MISMATCH` | Filter by disagreement reason |
| GET | `/api/disagreements/?org=ORG-A&sort=value` | Sort by lowest value first |
| GET | `/api/disagreements/?org=ORG-A&sort=-value` | Sort by highest value first |

## 10. Running Automated Tests

From the backend directory, execute:

```bash
python manage.py test reconcile
```

The current test suite contains 10 automated tests covering:

- Missing records
- Orphan records
- Value mismatches
- Duplicate entries
- Valid split entries
- Date mismatches
- Blank System B values
- Voided records
- Organization-level data isolation

**Current result:** 10 tests passed.

## 11. Dashboard

The DealerOS dashboard provides:

- Organization selection
- Disagreement reason filtering
- Value-based sorting
- Total disagreement count
- Reconciliation records table
- System A and System B value comparison
- Difference display

## 12. Implementation Note

The frontend is implemented using Django templates, HTML, CSS, and JavaScript rather than a separate React application. This keeps the application within a single Django project and simplifies local setup.

## 13. Future Improvements

- Add CSV upload functionality through the dashboard.
- Add downloadable reconciliation reports.
- Improve dashboard visualizations.
- Add pagination for large datasets.
- Add production database support.

---

**Project:** DealerOS – System A & System B Reconciliation Dashboard  
**Assignment:** AdosX DealerOS Assessment