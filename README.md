# GateLedger: Campus Bike Entry & Exit Log Using Blockchain

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-emerald.svg)](https://palletsprojects.com/p/flask/)
[![Blockchain](https://img.shields.io/badge/Blockchain-SHA--256%20PoW-teal.svg)](blockchain.py)
[![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](database.py)
[![Tests](https://img.shields.io/badge/Tests-25%20Passed-brightgreen.svg)](tests/)

> **A B.Tech Computer Science Capstone Project** demonstrating a tamper-evident, SHA-256 hash-chained, Proof-of-Work blockchain ledger for tracking college campus vehicle entry and exit events.

---

## 1. Project Introduction

**GateLedger** is an academic, full-stack campus security management system. It replaces traditional manual paper registers and vulnerable centralized database logs with a digital gate register backed by a persistent, single-node cryptographic blockchain ledger.

Every vehicle entry and exit event creates an immutable, timestamped snapshot that is cryptographically linked to preceding events using SHA-256 hashing and mined with a Proof-of-Work (PoW) consensus algorithm. Any unauthorized modification to historical records breaks the hash chain and is immediately flagged by the system's audit verification engine.

---

## 2. Problem Statement

Colleges and university campuses experience thousands of two-wheeler movements daily. Existing gate log mechanisms present significant operational and security vulnerabilities:
- **Paper Gate Registers:** Vulnerable to page tearing, ink fading, physical loss, forged signatures, and difficult historical searching.
- **Traditional Database Systems:** Vulnerable to internal tampering or silent modification by privileged operators without leaving an immutable audit trail.
- **Lack of State Enforcement:** Inability to prevent duplicate entries (logging an entry for a bike already inside) or ghost exits (logging an exit for a bike that never entered).

GateLedger solves these challenges by combining strict vehicle state enforcement with an append-only, SHA-256 hash-linked blockchain ledger.

---

## 3. Key Objectives

1. **Digital Gate Log:** Fast, keyboard-friendly recording of vehicle passages at campus gates.
2. **State Machine Validation:** Strictly enforces valid passage transitions (`ENTRY` &rarr; `EXIT` &rarr; `ENTRY`). Rejects duplicate entries and invalid exits.
3. **Cryptographic Immutability:** Mines an immutable SHA-256 block for every gate event, chaining each block's header to the previous block's hash.
4. **Proof of Work (PoW):** Requires finding a nonce such that the block hash satisfies a configurable difficulty prefix (default: `00`).
5. **Real-Time Auditing & Verification:** One-click chain integrity verification checking all hashes, sequence indices, previous hash links, and database snapshot consistency.
6. **Safe Tampering Simulation:** Educational demonstration tool allowing evaluators to safely simulate database tampering on an in-memory replica to observe instant detection without corrupting the real database.
7. **Role-Based Access Control (RBAC):** Distinct roles for **Security Guards** (gate operations, vehicle lookup) and **Administrators** (user management, system configuration).
8. **Data Export:** Filterable, timezone-aware CSV reporting.

---

## 4. Technology Stack

- **Backend:** Python 3.11+ / 3.12, Flask 3.1
- **Database:** SQLite3 with foreign-key enforcement (`PRAGMA foreign_keys = ON;`)
- **Cryptography:** Python standard library `hashlib` (SHA-256), `secrets`, `hmac`
- **Security:** Werkzeug password hashing (PBKDF2/SHA-256), session management, CSRF tokens
- **Time Handling:** Python standard library `datetime` and `zoneinfo` (stored in UTC, rendered in `Asia/Kolkata`)
- **Frontend:** HTML5, CSS3 (Custom Campus Security Theme), Vanilla JavaScript (No React, no external CDNs, 100% offline-ready)
- **Automated Testing:** `pytest` (25 automated test cases)

---

## 5. Prerequisites

- Python 3.11, 3.12, or later
- Pip (Python Package Manager)
- Any modern web browser (Edge, Chrome, Firefox, Safari)

---

## 6. Installation & Setup

### Windows (PowerShell or Command Prompt)

```powershell
# 1. Clone or navigate to the project directory
cd c:\blockchain_project\gateledger-campus-bike-log

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install required dependencies
pip install -r requirements.txt

# 4. (Optional) Seed realistic demonstration data
python seed.py

# 5. Start the GateLedger application
python app.py
```

### macOS / Linux

```bash
# 1. Navigate to the project directory
cd gateledger-campus-bike-log

# 2. (Optional) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Seed demonstration data
python3 seed.py

# 5. Start the application
python3 app.py
```

---

## 7. Application URL & Demo Credentials

Once started, open your browser and navigate to:
**`http://127.0.0.1:5000`**

### Pre-configured Demo Accounts:

| Role | Username | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@campus.local` | `Admin@123` | Full access: Dashboard, Gate Events, Vehicles, Blockchain Explorer, CSV Export, User Management |
| **Security Guard** | `guard@campus.local` | `Guard@123` | Operational access: Dashboard, Log Entry/Exit, Vehicles, Gate Records, Blockchain Explorer |

*Note: On the login page, click the quick-fill buttons (`Guard` or `Admin`) to automatically populate demo credentials.*

---

## 8. Application Architecture & Folder Structure

```
gateledger-campus-bike-log/
├── app.py                  # Main Flask application, routes, error handlers, and lifecycle hooks
├── blockchain.py           # Core blockchain engine: SHA-256 hashing, PoW mining, integrity verification
├── database.py             # SQLite database layer, schema, atomic transactions, state derivation
├── auth.py                 # Authentication helpers, session management, RBAC decorators, CSRF
├── config.py               # Environment variables, timezone, and difficulty settings
├── seed.py                 # Demonstration data seeder with 5 vehicles and 6 mined blocks
├── requirements.txt        # Minimal production and testing dependencies
├── .env.example            # Sample environment variables configuration
├── .gitignore              # Git ignore rules for virtual environments and databases
├── static/
│   ├── css/style.css       # Custom responsive stylesheet (Navy/Teal campus security design)
│   └── js/main.js          # Dynamic vehicle lookup, debounce autofill, and block inspection modal
├── templates/
│   ├── base.html           # Master responsive layout with navigation and security headers
│   ├── login.html          # Login card with quick-fill demo buttons
│   ├── dashboard.html      # Real-time metrics, live stats, and recent activity table
│   ├── new_event.html      # Interactive entry/exit passage recording form with live lookup
│   ├── records.html        # Filterable historical passage records with search & pagination
│   ├── event_detail.html   # Detailed event audit snapshot and linked blockchain block
│   ├── vehicles.html       # Vehicle catalog with status pills and search filters
│   ├── vehicle_detail.html # Vehicle profile, edit interface, and full passage timeline
│   ├── blockchain.html     # Blockchain explorer, verify tool, and safe tamper simulator
│   ├── admin_users.html    # Administrator user account management
│   └── errors/             # Custom 400, 403, 404, and 500 error templates
├── tests/
│   ├── conftest.py         # Pytest fixtures and isolated temporary databases
│   ├── test_blockchain.py  # Tests for genesis, PoW, sequential linking, and tamper detection
│   ├── test_gate_events.py # Tests for entry/exit cycles, state rules, and atomic rollbacks
│   ├── test_auth.py        # Tests for passwords, sessions, RBAC, and CSRF protection
│   └── test_reports.py     # Tests for CSV export, filtering, and empty data handling
└── docs/
    ├── PROJECT_REPORT.md   # Comprehensive B.Tech project documentation report
    └── DEMO_SCRIPT.md      # Step-by-step viva presentation script and 11 viva Q&As
```

---

## 9. Blockchain Implementation Details

### Block Data Structure

Each block in GateLedger is represented by a dictionary and stored persistently in SQLite:

```json
{
  "block_index": 1,
  "timestamp_utc": "2026-10-25T08:15:30.123456+00:00",
  "event_id": 1,
  "data_json": "{\"campus_id\":\"CS2023-441\",\"event_timestamp_utc\":\"2026-10-25T08:15:30.123456+00:00\",\"event_type\":\"ENTRY\",\"gate_name\":\"Main Gate (Gate 1)\",\"operator_id\":2,\"owner_type\":\"Student\",\"registration_number\":\"PB10AB1234\",\"rider_name\":\"Rohan Sharma\"}",
  "previous_hash": "00a12e89f4...",
  "nonce": 384,
  "block_hash": "00f14116b4e8c1d..."
}
```

### Deterministic Hashing Equation

GateLedger computes the SHA-256 hash across all core block headers and canonical JSON payload:

$$\text{Block Hash} = \text{SHA-256}(\text{block\_index} \parallel \text{timestamp\_utc} \parallel \text{event\_id} \parallel \text{canonical\_data\_json} \parallel \text{previous\_hash} \parallel \text{nonce})$$

- Canonical JSON is generated using `json.dumps(payload, sort_keys=True, separators=(',', ':'))` ensuring that key order variations do not alter the calculated hash.

### Proof-of-Work (PoW) Mining

Mining implements a verifiable proof-of-work puzzle:
- **Target Rule:** The block hash must begin with `difficulty` leading hexadecimal zeros (default `difficulty = 2`, requiring prefix `"00"`).
- **Mining Loop:** The miner initializes `nonce = 0` and increments `nonce` sequentially until `calculate_block_hash(...)` produces a hash starting with `"00"`.
- This ensures computational commitment while remaining fast (under 50 milliseconds) on ordinary laptops during live college demonstrations.

### Verification Algorithm

The verification routine (`blockchain.verify_blockchain`) audits:
1. **Genesis Authenticity:** Block 0 has index 0, previous hash `000...000`, valid PoW, and matching SHA-256.
2. **Sequential Indices:** Blocks are numbered strictly $0, 1, 2, \dots, N-1$ with no missing or duplicate indices.
3. **Linkage Invariance:** Each block's `previous_hash` exactly equals the `block_hash` of the preceding block.
4. **Hash Integrity:** Recomputed SHA-256 from current stored fields matches `block_hash`.
5. **Difficulty Satisfaction:** Every hash satisfies the required leading zero prefix.
6. **Cross-Check with Database:** Block `event_id` exists in `gate_events`, the block payload strictly matches the database event snapshot, and no committed event is missing a block.

---

## 10. Automated Testing

GateLedger includes a comprehensive test suite executed against isolated, temporary SQLite databases.

To run the automated tests:

```bash
pytest -q
```

### Actual Test Execution Output:

```text
.........................                                                [100%]
25 passed in 15.71s
```

All 25 test cases cover:
- Genesis block creation & idempotency
- Sequential block indexing & previous-hash linking
- Proof-of-Work prefix verification
- Detection of modified block data, broken links, and altered stored hashes
- Detection of gate events missing blocks or payload mismatches
- Safe tampering simulation with zero persistent side effects
- Valid ENTRY &rarr; EXIT &rarr; ENTRY state cycles
- Rejection of duplicate entries and ghost exits
- Registration number normalization and invalid format rejection
- Atomic transaction rollback on failure
- Authentication, RBAC route protection, and CSRF token validation
- Filtered and empty CSV reporting

---

## 11. Known Limitations & Security Model

This system is an **educational, persistent, single-node blockchain application**:
- **Single-Node Model:** It is hosted on a central server and SQLite database, not a distributed P2P network like Bitcoin or Ethereum.
- **Threat Model:** Cryptographic hash chaining protects against silent records tampering, undetected accidental corruption, and rogue unauthorized database edits. However, an attacker with full root access to the server operating system could hypothetically alter records and recompute all subsequent blocks.
- **Production Recommendation:** In a real-world enterprise deployment, blocks should be replicated across multiple campus gate nodes using Byzantine fault-tolerant (BFT) consensus or anchored periodically to a public distributed ledger.

---

## 12. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
