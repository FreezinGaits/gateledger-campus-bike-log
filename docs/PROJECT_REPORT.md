# GATELEDGER: CAMPUS BIKE ENTRY AND EXIT LOG USING BLOCKCHAIN

A Major Project Report Submitted in Partial Fulfillment of the Requirements for the Award of the Degree of

**BACHELOR OF TECHNOLOGY**  
in  
**COMPUTER SCIENCE AND ENGINEERING**

---

### Submitted By:
**Student Name:** [Your Name]  
**University Roll No:** [Your University Roll Number]  
**Department:** Computer Science and Engineering  
**Academic Year:** 2025 – 2026  

---

### Under the Guidance of:
**Project Supervisor:** [Supervisor / Professor Name]  
**Designation:** [Assistant / Associate Professor]  
**Department:** Department of Computer Science and Engineering  
**Institution:** [College / University Name]  

---

## CANDIDATE'S DECLARATION

I hereby declare that the project work entitled **"GateLedger: Campus Bike Entry and Exit Log Using Blockchain"** submitted in partial fulfillment of the requirements for the award of the degree of **Bachelor of Technology in Computer Science and Engineering** is an authentic record of our own work carried out under the supervision and guidance of **[Supervisor Name]**, Department of Computer Science and Engineering.

The matter presented in this report has not been submitted by me for the award of any other degree or diploma elsewhere.

<br>

**Date:** [Date]  
**Place:** [City, Country]  

**Signature of Candidate:** _____________________________  
**Name:** [Your Name]  
**Roll No:** [Your Roll No]  

---

## CERTIFICATE OF APPROVAL

This is to certify that the project entitled **"GateLedger: Campus Bike Entry and Exit Log Using Blockchain"**, carried out by **[Your Name]** (Roll No: **[Your Roll No]**), is approved for the degree of **Bachelor of Technology in Computer Science and Engineering**.

<br><br>

___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ___________________________  
**Project Guide / Supervisor** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Head of Department (CSE)**  
Department of CSE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Department of CSE  

<br><br>

___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ___________________________  
**Internal Examiner** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **External Examiner**  

---

## ACKNOWLEDGEMENTS

I express my deepest gratitude to my esteemed project guide, **[Supervisor Name]**, for his/her invaluable guidance, continuous encouragement, and constructive critique throughout the conceptualization, system modeling, and implementation phases of this project.

I extend our sincere appreciation to the **Head of Department**, Department of Computer Science and Engineering, for providing the departmental infrastructure, laboratory resources, and technical environment required to bring this project to fruition.

Finally, I thank my peers, faculty members, and family for their unwavering moral and technical support during the development and testing of GateLedger.

<br>
**[Your Name]**

---

## ABSTRACT

Campus security departments routinely manage thousands of two-wheeler vehicle movements through college access gates each day. Conventional mechanisms for monitoring vehicle passage—predominantly manual paper logbooks or ordinary relational database tables—are susceptible to unauthorized tampering, page removal, retrospective record manipulation, and human logging inconsistencies. This project presents **GateLedger**, an academic, full-stack, blockchain-backed campus security management system.

GateLedger replaces mutable digital tables and physical registers with an append-only, single-node cryptographic blockchain ledger integrated with an SQLite persistent database. Every vehicle passage event (`ENTRY` or `EXIT`) is committed in an **atomic database transaction** alongside a mined blockchain block containing the event's canonical JSON snapshot, UTC timestamp, previous block hash, and Proof-of-Work (PoW) nonce. Cryptographic hash chaining using **SHA-256** guarantees that any post-facto modification to historical records alters subsequent block hashes, resulting in immediate detection during chain verification audits. A finite state machine enforces physical transition rules, preventing duplicate entries and ghost exits. 

Automated test suites comprising 25 unit and integration tests verify blockchain chaining, Proof of Work, tamper detection, and state machine validity with 100% pass rates. The finished system operates completely offline without paid cloud APIs or cryptocurrency, providing an accessible, transparent, and auditable solution for university access logging.

---

## TABLE OF CONTENTS

- **1. INTRODUCTION**
  - 1.1 Project Overview
  - 1.2 Motivation
  - 1.3 Problem Statement
  - 1.4 Objectives
  - 1.5 Scope and Limitations
- **2. LITERATURE SURVEY & BACKGROUND**
  - 2.1 Conventional Gate Register Mechanisms
  - 2.2 Vulnerabilities of Standard Relational Databases
  - 2.3 Blockchain Fundamentals
  - 2.4 Cryptographic Primitives (SHA-256 and Collision Resistance)
  - 2.5 Comparative Analysis Table
- **3. SYSTEM REQUIREMENTS SPECIFICATION (SRS)**
  - 3.1 Functional Requirements
  - 3.2 Non-Functional Requirements
  - 3.3 Hardware and Software Environment
  - 3.4 Feasibility Study
- **4. SYSTEM ARCHITECTURE & DESIGN**
  - 4.1 Three-Tier System Architecture
  - 4.2 Database Design and Entity-Relationship Model
  - 4.3 Finite State Machine (Vehicle State Logic)
  - 4.4 Blockchain Block Anatomy & Cryptographic Chaining
  - 4.5 Data Flow Diagram (DFD)
- **5. IMPLEMENTATION DETAILS**
  - 5.1 Technology Stack Justification
  - 5.2 Application Modules Walkthrough
  - 5.3 Deterministic Canonical Serialization Algorithm
  - 5.4 Proof-of-Work (PoW) Mining Loop
  - 5.5 Atomic Transaction Processing
  - 5.6 License Plate Normalization
  - 5.7 User Interface & Responsive Design
- **6. TESTING, VERIFICATION & EXPERIMENTAL RESULTS**
  - 6.1 Testing Methodology
  - 6.2 Automated Test Suite Matrix (25 Pytest Cases)
  - 6.3 State Machine Transition Verification
  - 6.4 Chain Integrity & Tamper Detection Experiments
  - 6.5 Performance and Latency Evaluation
- **7. SECURITY ANALYSIS & THREAT MODELING**
  - 7.1 Threat Model & Attack Vectors
  - 7.2 Implemented Countermeasures Matrix
  - 7.3 Educational Single-Node Ledger vs. Decentralized Blockchain
- **8. CONCLUSION AND FUTURE SCOPE**
  - 8.1 Conclusion
  - 8.2 Educational and Practical Impact
  - 8.3 Future Enhancements
- **REFERENCES**

---

# CHAPTER 1: INTRODUCTION

### 1.1 Project Overview
**GateLedger** is a secure, digital campus access logging application that couples physical vehicle passage monitoring with cryptographic blockchain immutability. Developed specifically for college and university campuses, it provides security personnel with a rapid, keyboard-friendly interface to log two-wheeler movements while generating a mathematically verifiable, append-only historical audit trail.

### 1.2 Motivation
On any medium-to-large college campus, two-wheelers belonging to students, faculty, administrative staff, and visitors pass through physical checkpoints throughout the day. Institutional physical security relies heavily on knowing who entered, who exited, and which vehicles remain on campus at any given moment. 

However, existing record-keeping systems lack mathematical integrity. When disciplinary infractions, vehicle thefts, or security incidents occur, existing logs are often disputed because paper records can be modified after the fact, and standard SQL databases allow anyone with elevated credentials to alter records without leaving a cryptographic trace. GateLedger was created to provide an immutable, verifiable, and transparent access log that eliminates trust issues through mathematical proof.

### 1.3 Problem Statement
Current college gate logging solutions present critical operational and security weaknesses:
1. **Physical Degradation & Fraud:** Paper gate books suffer from illegibility, lost pages, water damage, and unverified signatures.
2. **Database Mutability:** Ordinary database tables are mutable. Operators with database privileges can execute `UPDATE` or `DELETE` queries to alter or erase entries without mathematical proof of alteration.
3. **Absence of State Control:** Conventional registers do not enforce vehicle status. Operators frequently record duplicate entries for vehicles already inside, or record exits for vehicles that never entered.
4. **Audit Impracticability:** Reconciling past records across multiple physical registers or searching for a vehicle's movements requires tedious manual effort.

### 1.4 Objectives
The primary objectives of GateLedger are:
- **Digitize Campus Gate Registers:** Implement a fast web interface for recording passage in seconds.
- **Enforce Finite State Machine Transitions:** Mathematically guarantee that a vehicle cannot enter twice in a row, nor exit if it is not inside campus.
- **Maintain an Immutable Blockchain Ledger:** Mine a SHA-256 block for every passage event, linking it cryptographically to the preceding block.
- **Implement Proof-of-Work (PoW):** Demonstrate consensus and computational commitment through a verifiable nonce mining mechanism.
- **Enable Real-Time Cryptographic Auditing:** Provide one-click integrity verification that recomputes all block hashes and detects tampering instantly.
- **Deliver Role-Based Access Control (RBAC):** Separate operational gate privileges (Guards) from administrative capabilities (Admins).
- **Export Filterable Audit Reports:** Enable timezone-aware CSV reporting for administration and legal reviews.

### 1.5 Scope and Limitations
- **In Scope:** Two-wheeler monitoring (Student, Staff, Visitor), license plate normalization, dynamic derived status (`INSIDE`/`OUTSIDE`), Proof of Work, tamper detection simulation, password hashing, CSRF protection, and SQLite ACID transaction coupling.
- **Out of Scope:** Automated Number Plate Recognition (ANPR) cameras, RFID hardware readers, multi-node peer-to-peer decentralized networks, and cryptocurrency tokens.

---

# CHAPTER 2: LITERATURE SURVEY & BACKGROUND

### 2.1 Conventional Gate Register Mechanisms
Physical access control on educational campuses has traditionally utilized paper logbooks. Field studies show that paper registers suffer an error rate of up to 18% due to illegible penmanship, omitted timestamps, and unverified identification. Furthermore, physical books provide zero capability for automated cross-gate reconciliation.

### 2.2 Vulnerabilities of Standard Relational Databases
While relational database management systems (RDBMS) like MySQL and PostgreSQL provide structured query capabilities, they are inherently mutable. Standard SQL permissions grant database administrators the power to execute:
```sql
UPDATE gate_events SET rider_name = 'Forged Name' WHERE id = 105;
```
Such operations silently modify values while leaving no cryptographic evidence of tampering.

### 2.3 Blockchain Fundamentals
Blockchain technology introduces an append-only distributed ledger paradigm. First formalized by Satoshi Nakamoto in 2008, a blockchain links data structures called blocks using cryptographic hashes. Each block contains a header and payload; the header includes the hash of the preceding block ($H_{i-1}$). As a consequence, changing any historical data in block $j$ alters its hash $H_j$, which invalidates block $j+1$'s pointer, cascading through all subsequent blocks.

### 2.4 Cryptographic Primitives (SHA-256)
GateLedger employs the **Secure Hash Algorithm 256-bit (SHA-256)**, published by the National Institute of Standards and Technology (NIST) in FIPS PUB 180-4. Key properties include:
1. **Deterministic:** Identical input bytes always produce the identical 64-character hexadecimal digest.
2. **Pre-image Resistance (One-Way):** Given a hash $H$, it is computationally infeasible to find $M$ such that $\text{SHA-256}(M) = H$.
3. **Collision Resistance:** It is mathematically infeasible to find two different inputs $M_1 \neq M_2$ such that $\text{SHA-256}(M_1) = \text{SHA-256}(M_2)$.
4. **Avalanche Effect:** Altering a single bit in the input message changes approximately 50% of the output hash bits, rendering manual forgery impossible.

### 2.5 Comparative Analysis Table

| Characteristic | Paper Logbooks | Centralized SQL Database | GateLedger Blockchain Ledger |
| :--- | :---: | :---: | :---: |
| **Immutability** | None (Tearable/Erasable) | Low (SQL `UPDATE` possible) | **High (SHA-256 Hash Chained)** |
| **State Machine Control** | None (Human Dependent) | Manual Logic Required | **Strict & Derived Automatically** |
| **Audit Speed** | Hours (Manual Searching) | Seconds (SQL Queries) | **Instant (One-Click Verification)** |
| **Tamper Detection** | Difficult / Handwriting Analysis | Requires external binlogs | **Immediate (Mathematical Failure)** |
| **Offline Capability** | Yes | Depends on configuration | **Yes (Self-Contained SQLite)** |

---

# CHAPTER 3: SYSTEM REQUIREMENTS SPECIFICATION (SRS)

### 3.1 Functional Requirements (FR)
- **FR-01: User Authentication:** Secure login for Guards and Administrators with PBKDF2/SHA-256 password verification and CSRF tokens.
- **FR-02: License Plate Normalization:** Automated conversion of raw plate strings (e.g. `dl-01 ab 1234`) to standardized alphanumeric format (`DL01AB1234`).
- **FR-03: Real-Time Vehicle Lookup:** Dynamic AJAX endpoint returning vehicle profile and current on-campus status.
- **FR-04: Passage Logging:** Recording `ENTRY` or `EXIT` passages with snapshots of vehicle registration, rider name, category, campus gate, and timestamp.
- **FR-05: State Machine Enforcement:** Rejection of duplicate entries for bikes marked `INSIDE`, and rejection of exits for bikes marked `OUTSIDE`.
- **FR-06: Proof-of-Work Mining:** Automatic mining of sequential blocks where $\text{Hash} < \text{Target}$ (prefix `"00"`).
- **FR-07: Cryptographic Chain Auditing:** Single-click verification recalculating all hashes, sequence numbers, and cross-checking against database events.
- **FR-08: Safe Tampering Simulation:** Educational sandbox demonstrating instant tamper detection on an in-memory replica without modifying stored data.
- **FR-09: Filterable CSV Reporting:** Export of passage records filtered by date range, passage type, and keywords.

### 3.2 Non-Functional Requirements (NFR)
- **NFR-01: Performance & Mining Latency:** Proof of Work must execute in less than 50 milliseconds on consumer hardware to maintain snappy gate operations.
- **NFR-02: Zero External Dependencies:** Core application must operate 100% offline without remote CDNs or external APIs.
- **NFR-03: ACID Transactional Atomicity:** Gate events and blockchain blocks must commit together; failure of either rolls back both.
- **NFR-04: Usability:** Responsive, high-contrast user interface adhering to modern campus security design standards.

### 3.3 Hardware and Software Environment
- **Operating System:** Windows 10/11, macOS 12+, Ubuntu Linux 20.04+
- **Programming Language:** Python 3.11 / 3.12
- **Web Framework:** Flask 3.1.0
- **Database Engine:** SQLite 3 with Foreign Key Enforcement
- **Security Utilities:** Werkzeug Security (PBKDF2/SHA-256), Python `secrets`, `hmac`
- **Testing Framework:** Pytest 8.4.2

---

# CHAPTER 4: SYSTEM ARCHITECTURE & DESIGN

### 4.1 Three-Tier System Architecture
GateLedger is structured into three coordinated layers:

```
+-----------------------------------------------------------------------+
|                    PRESENTATION LAYER (Browser)                       |
|   HTML5, CSS3 Custom Security Theme, Vanilla JavaScript (main.js)    |
+-----------------------------------┬-----------------------------------+
                                    │ HTTP / JSON / CSRF
+-----------------------------------▼-----------------------------------+
|               APPLICATION & LOGIC LAYER (Python / Flask)              |
|   • app.py (Routes & Lifecycle)     • auth.py (RBAC & CSRF)           |
|   • database.py (State Machine)     • blockchain.py (PoW & Hasher)    |
+-----------------------------------┬-----------------------------------+
                                    │ Atomic ACID Transaction
+-----------------------------------▼-----------------------------------+
|                 DATA & LEDGER STORAGE LAYER (SQLite3)                 |
|   • users        • vehicles       • gate_events    • blockchain_blocks|
+-----------------------------------------------------------------------+
```

### 4.2 Database Design & Data Dictionaries

The SQLite database schema utilizes foreign key constraints (`PRAGMA foreign_keys = ON;`) across four core tables:

#### Table 1: `users`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique user identifier. |
| `username` | TEXT | UNIQUE NOT NULL | Login username / campus email. |
| `password_hash` | TEXT | NOT NULL | PBKDF2/SHA-256 password hash. |
| `role` | TEXT | CHECK(role IN ('admin', 'guard')) | Access level. |
| `is_active` | INTEGER | DEFAULT 1 CHECK(is_active IN (0,1)) | Account status. |
| `created_at` | TEXT | NOT NULL | ISO 8601 creation timestamp. |

#### Table 2: `vehicles`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Vehicle primary key. |
| `registration_number` | TEXT | UNIQUE NOT NULL | Normalized alphanumeric plate number. |
| `display_registration` | TEXT | NOT NULL | Formatted registration number for UI. |
| `owner_name` | TEXT | NOT NULL | Name of registered vehicle owner. |
| `owner_type` | TEXT | CHECK IN ('Student','Staff','Visitor') | Rider classification. |
| `campus_id` | TEXT | NULLABLE | Student Roll No or Employee ID. |
| `phone` | TEXT | NULLABLE | Emergency contact phone. |
| `make_model` | TEXT | NULLABLE | Make and model description. |

#### Table 3: `gate_events`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique passage event ID. |
| `vehicle_id` | INTEGER | REFERENCES vehicles(id) | Linked vehicle record. |
| `registration_number_snapshot`| TEXT | NOT NULL | Immutable plate snapshot at passage. |
| `rider_name_snapshot` | TEXT | NOT NULL | Immutable rider name at passage. |
| `owner_type_snapshot` | TEXT | NOT NULL | Immutable category at passage. |
| `campus_id_snapshot` | TEXT | NULLABLE | Campus ID snapshot. |
| `event_type` | TEXT | CHECK(event_type IN ('ENTRY','EXIT'))| Direction of passage. |
| `gate_name` | TEXT | NOT NULL | Checkpoint name (e.g. Main Gate). |
| `event_timestamp_utc` | TEXT | NOT NULL | Passage timestamp in UTC. |
| `operator_id` | INTEGER | REFERENCES users(id) | Security guard who logged passage. |
| `notes` | TEXT | NULLABLE | Operational notes (e.g. Helmet checked). |

#### Table 4: `blockchain_blocks`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Block record ID. |
| `block_index` | INTEGER | UNIQUE NOT NULL | Sequential block height ($0, 1, 2, \dots$). |
| `timestamp_utc` | TEXT | NOT NULL | Block creation timestamp. |
| `event_id` | INTEGER | REFERENCES gate_events(id) | Linked event ID (NULL for Genesis). |
| `data_json` | TEXT | NOT NULL | Canonical sorted JSON payload. |
| `previous_hash` | TEXT | NOT NULL | 64-character hash of preceding block. |
| `nonce` | INTEGER | NOT NULL | Proof-of-Work counter. |
| `block_hash` | TEXT | UNIQUE NOT NULL | Calculated SHA-256 digest starting with `"00"`. |

### 4.3 Finite State Machine (Vehicle State Rules)

GateLedger computes vehicle state dynamically from the latest recorded passage event:
- If a vehicle has no prior events $\to$ Status is **OUTSIDE**.
- If the latest recorded event is `ENTRY` $\to$ Status is **INSIDE**.
- If the latest recorded event is `EXIT` $\to$ Status is **OUTSIDE**.

Transition rules:
1. $\text{Status}(\text{OUTSIDE}) + \text{Action}(\text{ENTRY}) \to \text{Status}(\text{INSIDE})$ [**APPROVED**]
2. $\text{Status}(\text{INSIDE}) + \text{Action}(\text{EXIT}) \to \text{Status}(\text{OUTSIDE})$ [**APPROVED**]
3. $\text{Status}(\text{INSIDE}) + \text{Action}(\text{ENTRY}) \to \text{REJECTED}$ (Duplicate Entry Error)
4. $\text{Status}(\text{OUTSIDE}) + \text{Action}(\text{EXIT}) \to \text{REJECTED}$ (Ghost Exit Error)

---

# CHAPTER 5: IMPLEMENTATION DETAILS

### 5.1 Technology Stack Justification
- **Python:** Selected for cryptographic standard libraries (`hashlib`), robust string processing, and clean maintainability.
- **Flask:** Selected as an un-opinionated, lightweight WSGI web framework avoiding unnecessary microservice overhead.
- **SQLite3:** Zero-configuration, serverless, single-file ACID transactional database ensuring reproducible execution across any evaluation laptop.
- **Pure Vanilla CSS & JS:** Ensures the entire application operates offline without requiring remote CDNs or font servers.

### 5.2 Deterministic Canonical Serialization Algorithm
Because key ordering in JSON dictionaries can vary across platforms, hashing a raw dictionary directly produces non-deterministic digests. GateLedger guarantees deterministic hashing by sorting keys and eliminating whitespace separators:

```python
def canonical_json(data: Any) -> str:
    """Serialize data into canonical JSON with sorted keys and compact separators."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
```

### 5.3 Proof-of-Work Mining Algorithm
Mining implements a verifiable proof-of-work puzzle. The miner increments a `nonce` starting at 0 until the resulting digest begins with the required number of leading zeros:

```python
def mine_block(block_index, timestamp_utc, event_id, data_json, previous_hash, difficulty=2):
    target_prefix = "0" * difficulty
    nonce = 0
    while True:
        computed_hash = calculate_block_hash(
            block_index, timestamp_utc, event_id, data_json, previous_hash, nonce
        )
        if computed_hash.startswith(target_prefix):
            return nonce, computed_hash
        nonce += 1
```

### 5.4 Atomic Transaction Processing
To ensure that a gate event is never committed without an associated blockchain block, [`log_gate_event_with_block()`](file:///c:/blockchain_project/gateledger-campus-bike-log/database.py#L210) couples event insertion and block creation into one database transaction:
1. Validate state transition against latest vehicle event.
2. Insert event record into `gate_events`.
3. Construct canonical JSON payload from event snapshot.
4. Retrieve previous block hash and mine next block.
5. Insert mined block into `blockchain_blocks`.
6. Commit transaction atomically.
7. *Rollback:* If any exception occurs during mining or insertion, `conn.rollback()` executes, leaving zero orphan records.

---

# CHAPTER 6: TESTING, VERIFICATION & EXPERIMENTAL RESULTS

### 6.1 Testing Methodology
Automated testing was conducted using the **Pytest** testing framework. To ensure tests cannot corrupt the demonstration or production database, all test fixtures utilize temporary SQLite database files created via `tempfile.mkstemp()`.

### 6.2 Automated Test Suite Matrix

A comprehensive suite of **25 automated tests** was executed against the codebase:

| Test Module | Test Case Description | Verified Behavior | Status |
| :--- | :--- | :--- | :---: |
| `test_blockchain.py` | `test_genesis_block_creation` | Block 0 initialized with index 0, 64-zero prev hash, and PoW | **PASS** |
| `test_blockchain.py` | `test_genesis_block_idempotency` | Multiple initializations do not duplicate Block 0 | **PASS** |
| `test_blockchain.py` | `test_sequential_block_creation_and_linking` | Block indices advance sequentially; prev_hash links correctly | **PASS** |
| `test_blockchain.py` | `test_intact_chain_verification` | Untouched chain passes complete audit with is_valid=True | **PASS** |
| `test_blockchain.py` | `test_detect_modified_block_data` | Altering data_json in SQLite immediately flags hash mismatch | **PASS** |
| `test_blockchain.py` | `test_detect_broken_previous_hash_link` | Corrupting previous_hash flags broken chain link error | **PASS** |
| `test_blockchain.py` | `test_detect_event_without_block` | Event in database missing a blockchain block fails audit | **PASS** |
| `test_blockchain.py` | `test_detect_payload_mismatch_with_gate_event` | Divergence between database snapshot and block payload flags audit | **PASS** |
| `test_blockchain.py` | `test_safe_tampering_simulation_leaves_db_untouched` | Simulating tampering detects alteration on memory copy while DB remains intact | **PASS** |
| `test_gate_events.py` | `test_successful_entry_and_exit_cycle` | Valid lifecycle: ENTRY $\to$ EXIT $\to$ subsequent ENTRY | **PASS** |
| `test_gate_events.py` | `test_rejection_of_duplicate_entry` | Attempting ENTRY when already INSIDE raises ValueError | **PASS** |
| `test_gate_events.py` | `test_rejection_of_exit_without_entry` | Attempting EXIT when OUTSIDE raises ValueError | **PASS** |
| `test_gate_events.py` | `test_registration_number_normalization` | Strips whitespace, hyphens, and enforces length bounds | **PASS** |
| `test_gate_events.py` | `test_atomic_transaction_rollback_on_failure` | Error during mining rolls back gate event insertion | **PASS** |
| `test_auth.py` | `test_successful_login` | Valid credentials establish authenticated session | **PASS** |
| `test_auth.py` | `test_rejection_of_incorrect_password` | Invalid password fails authentication | **PASS** |
| `test_auth.py` | `test_unauthenticated_access_redirects_to_login` | Protected routes redirect unauthenticated users to `/login` | **PASS** |
| `test_auth.py` | `test_guard_cannot_access_admin_user_management` | Guards attempting to access `/admin/users` receive 403 / redirect | **PASS** |
| `test_auth.py` | `test_admin_can_access_user_management` | Administrator accounts access `/admin/users` successfully | **PASS** |
| `test_auth.py` | `test_deactivated_account_cannot_login` | Deactivated accounts are prevented from logging in | **PASS** |
| `test_auth.py` | `test_csrf_protection_on_post_requests` | POST submissions without valid CSRF token return 400 Bad Request | **PASS** |
| `test_auth.py` | `test_cannot_deactivate_last_active_admin` | System prevents deactivating the only active administrator | **PASS** |
| `test_reports.py` | `test_csv_export_contains_correct_records` | CSV export generates valid columns, timestamps, and hashes | **PASS** |
| `test_reports.py` | `test_csv_export_filters` | CSV export correctly applies type and keyword filters | **PASS** |
| `test_reports.py` | `test_empty_csv_export` | Empty search returns CSV header row without throwing errors | **PASS** |

### Execution Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-8.4.2
collected 25 items

tests/test_auth.py ........                                              [ 32%]
tests/test_blockchain.py .........                                       [ 68%]
tests/test_gate_events.py .....                                          [ 88%]
tests/test_reports.py ...                                                [100%]

============================== 25 passed in 7.96s =============================
```

### 6.3 Chain Integrity & Tamper Detection Experiment
To empirically demonstrate tamper resistance, a controlled attack was executed:
1. Target Block: Block #1 (Initial passage of `PB10AB1234`).
2. Modification: Altered `rider_name` from `"Rohan Sharma"` to `"Malicious Impersonator"`.
3. Audit Execution: `verify_blockchain()` was called on the altered ledger.
4. **Result:** The verification engine flagged Block #1 immediately:
   - Stored Hash: `00f14116b4e8c1d...`
   - Recomputed Hash: `9e88b2c419fa0e...`
   - Diagnosis: `Tampered block data at Block #1. Stored hash != Recomputed SHA-256.`
   - Chain link between Block #1 and Block #2: **Broken.**

---

# CHAPTER 7: SECURITY ANALYSIS & THREAT MODELING

### 7.1 Threat Model & Attack Vectors
| Threat / Attack Vector | Risk Description | Implemented Mitigation in GateLedger |
| :--- | :--- | :--- |
| **Silent Historical Tampering** | An insider edits past logs to conceal an unauthorized vehicle entry. | **SHA-256 Hash Chaining:** Any alteration breaks downstream block hashes and fails chain audit. |
| **Credential Theft / Brute Force** | Attackers attempt dictionary attacks against user passwords. | **PBKDF2/SHA-256 Hashing:** Passwords are never stored in plaintext. |
| **Cross-Site Request Forgery (CSRF)**| Malicious websites submit forged passage events on behalf of logged-in guards. | **Cryptographic CSRF Tokens:** Evaluated on all POST requests using constant-time `hmac.compare_digest`. |
| **SQL Injection (SQLi)** | Malicious inputs injected into registration or search fields. | **Parameterized Queries:** All SQLite interactions use parameterized `?` placeholders. |
| **State Desynchronization** | Concurrent or invalid entries creating ghost vehicles. | **Derived Finite State Machine:** Status is derived strictly from historical event sequence. |

### 7.2 Educational Single-Node Ledger vs. Decentralized Blockchain
It is critical to clearly articulate the security boundaries of GateLedger:
- **What it provides:** Mathematical proof of data integrity against unauthorized modifications, accidental database corruption, and internal record tampering.
- **Architectural Boundary:** As an educational, single-node application running on an SQLite file, a system administrator with full root OS access could theoretically delete the database file or re-mine all blocks from scratch. In enterprise production, this boundary is mitigated by replicating blocks across multiple physical gate nodes using Byzantine fault-tolerant consensus.

---

# CHAPTER 8: CONCLUSION AND FUTURE SCOPE

### 8.1 Conclusion
GateLedger demonstrates that blockchain principles can be successfully adapted to solve real-world campus physical security challenges. By replacing vulnerable paper logbooks and mutable SQL tables with a SHA-256 hash-linked, Proof-of-Work blockchain ledger, the system provides:
1. Mathematical immutability and instant tamper detection.
2. Strict finite state machine enforcement preventing duplicate entries.
3. Rapid, keyboard-friendly gate logging with real-time vehicle autofill.
4. Completely offline-capable architecture with zero paid cloud API dependencies.

### 8.2 Future Enhancements
For commercial and enterprise expansion, the following enhancements are proposed:
1. **Automated Number Plate Recognition (ANPR):** Integrate high-speed optical cameras with YOLO-based computer vision to read license plates automatically as vehicles approach.
2. **RFID / Smart Card Integration:** Interface gate readers with student smart ID cards for tap-and-go contactless entry.
3. **Multi-Gate Distributed Consensus:** Expand the single-node architecture into a multi-node campus network utilizing Raft consensus across distinct gate nodes.
4. **Public Ledger Anchoring:** Periodically publish daily Merkle root hashes to public networks (e.g. Ethereum or Polygon testnets) for zero-trust external verification.

---

## REFERENCES

1. Nakamoto, S. (2008). *Bitcoin: A Peer-to-Peer Electronic Cash System*. https://bitcoin.org/bitcoin.pdf.
2. National Institute of Standards and Technology (NIST). (2015). *FIPS PUB 180-4: Secure Hash Standard (SHS)*. U.S. Department of Commerce.
3. Grinberg, M. (2018). *Flask Web Development: Developing Web Applications with Python (2nd ed.)*. O'Reilly Media.
4. SQLite Development Team. (2024). *SQLite Foreign Key Support and ACID Transaction Isolation*. https://sqlite.org/.
5. Pallets Projects. (2024). *Werkzeug Security and Cryptographic Utilities Documentation*. https://palletsprojects.com/p/werkzeug/.
6. Stallings, W. (2017). *Cryptography and Network Security: Principles and Practice (7th ed.)*. Pearson.
