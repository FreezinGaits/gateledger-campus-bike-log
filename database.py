"""GateLedger Database Module
==============================
SQLite database management, schema creation, atomic event-and-block transactions,
vehicle state tracking, and query interfaces.
"""

from __future__ import annotations
from datetime import datetime, timezone
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from werkzeug.security import generate_password_hash

from config import Config
import blockchain


def get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a SQLite database connection with row factory
    and enforced foreign key constraints.
    """
    path = db_path or Config.DATABASE_PATH
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None, difficulty: Optional[int] = None) -> None:
    """Initialize database tables, indexes, default accounts, and genesis block."""
    conn = get_db(db_path)
    cur = conn.cursor()

    # Table A: users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'guard')),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
            created_at TEXT NOT NULL
        );
        """
    )

    # Table B: vehicles
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_number TEXT UNIQUE NOT NULL,
            display_registration TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            owner_type TEXT NOT NULL CHECK(owner_type IN ('Student', 'Staff', 'Visitor')),
            campus_id TEXT,
            phone TEXT,
            make_model TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    # Table C: gate_events
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS gate_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
            registration_number_snapshot TEXT NOT NULL,
            rider_name_snapshot TEXT NOT NULL,
            owner_type_snapshot TEXT NOT NULL,
            campus_id_snapshot TEXT,
            event_type TEXT NOT NULL CHECK(event_type IN ('ENTRY', 'EXIT')),
            gate_name TEXT NOT NULL,
            event_timestamp_utc TEXT NOT NULL,
            operator_id INTEGER NOT NULL REFERENCES users(id),
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    # Table D: blockchain_blocks
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS blockchain_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER UNIQUE NOT NULL,
            timestamp_utc TEXT NOT NULL,
            event_id INTEGER REFERENCES gate_events(id) ON DELETE RESTRICT,
            data_json TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            nonce INTEGER NOT NULL,
            block_hash TEXT UNIQUE NOT NULL
        );
        """
    )

    # Performance and query indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_reg ON vehicles(registration_number);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gate_events_vehicle ON gate_events(vehicle_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gate_events_time ON gate_events(event_timestamp_utc);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gate_events_type ON gate_events(event_type);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_blockchain_index ON blockchain_blocks(block_index);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_blockchain_hash ON blockchain_blocks(block_hash);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_blockchain_event ON blockchain_blocks(event_id);")

    conn.commit()

    # Seed initial demo accounts if not already present
    seed_default_users(conn)

    # Initialize Genesis block
    pow_diff = difficulty if difficulty is not None else Config.POW_DIFFICULTY
    blockchain.init_genesis_block(conn, difficulty=pow_diff)

    conn.close()


def seed_default_users(conn: sqlite3.Connection) -> None:
    """Seed initial demo administrator and security guard accounts idempotently."""
    cur = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()

    # Admin check
    cur.execute("SELECT id FROM users WHERE username = ?", (Config.DEFAULT_ADMIN_USER,))
    if not cur.fetchone():
        admin_hash = generate_password_hash(Config.DEFAULT_ADMIN_PASSWORD)
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active, created_at)
            VALUES (?, ?, 'admin', 1, ?)
            """,
            (Config.DEFAULT_ADMIN_USER, admin_hash, now_utc),
        )

    # Guard check
    cur.execute("SELECT id FROM users WHERE username = ?", (Config.DEFAULT_GUARD_USER,))
    if not cur.fetchone():
        guard_hash = generate_password_hash(Config.DEFAULT_GUARD_PASSWORD)
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active, created_at)
            VALUES (?, ?, 'guard', 1, ?)
            """,
            (Config.DEFAULT_GUARD_USER, guard_hash, now_utc),
        )

    conn.commit()


def normalize_reg_number(raw_reg: str) -> str:
    """Normalize vehicle registration numbers for unambiguous matching.
    
    Converts to uppercase and removes spaces, hyphens, and other punctuation.
    Example: 'DL-01-AB-1234' -> 'DL01AB1234'
    """
    if not raw_reg:
        raise ValueError("Vehicle registration number cannot be empty.")
    normalized = re.sub(r"[^A-Za-z0-9]", "", raw_reg).upper()
    if len(normalized) < 4 or len(normalized) > 15:
        raise ValueError("Registration number must be between 4 and 15 alphanumeric characters.")
    return normalized


def get_vehicle_current_status(conn: sqlite3.Connection, vehicle_id: int) -> str:
    """Derive vehicle current status ('INSIDE' or 'OUTSIDE') strictly from its latest gate event.
    
    If the vehicle has no recorded events or its latest event is EXIT, it is OUTSIDE.
    If its latest event is ENTRY, it is INSIDE.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT event_type FROM gate_events
        WHERE vehicle_id = ?
        ORDER BY id DESC LIMIT 1
        """,
        (vehicle_id,),
    )
    row = cur.fetchone()
    if row and row["event_type"] == "ENTRY":
        return "INSIDE"
    return "OUTSIDE"


def get_vehicle_by_reg(conn: sqlite3.Connection, reg_no: str) -> Optional[Dict[str, Any]]:
    """Look up a vehicle by normalized registration number."""
    normalized = normalize_reg_number(reg_no)
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicles WHERE registration_number = ?", (normalized,))
    row = cur.fetchone()
    if row:
        v = dict(row)
        v["current_status"] = get_vehicle_current_status(conn, v["id"])
        return v
    return None


def get_vehicle_by_id(conn: sqlite3.Connection, vehicle_id: int) -> Optional[Dict[str, Any]]:
    """Look up a vehicle by its primary key ID."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cur.fetchone()
    if row:
        v = dict(row)
        v["current_status"] = get_vehicle_current_status(conn, v["id"])
        return v
    return None


def create_or_update_vehicle(
    conn: sqlite3.Connection,
    registration_number: str,
    owner_name: str,
    owner_type: str,
    campus_id: Optional[str] = None,
    phone: Optional[str] = None,
    make_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a new vehicle or update an existing vehicle profile.
    
    Note: Updating a vehicle profile does NOT alter any historical gate event snapshots.
    """
    normalized = normalize_reg_number(registration_number)
    display_reg = registration_number.strip().upper()
    now_utc = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()

    cur.execute("SELECT * FROM vehicles WHERE registration_number = ?", (normalized,))
    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE vehicles
            SET display_registration = ?, owner_name = ?, owner_type = ?, campus_id = ?,
                phone = ?, make_model = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                display_reg,
                owner_name.strip(),
                owner_type,
                campus_id.strip() if campus_id else None,
                phone.strip() if phone else None,
                make_model.strip() if make_model else None,
                now_utc,
                existing["id"],
            ),
        )
        conn.commit()
        return get_vehicle_by_id(conn, existing["id"])  # type: ignore
    else:
        cur.execute(
            """
            INSERT INTO vehicles (
                registration_number, display_registration, owner_name, owner_type,
                campus_id, phone, make_model, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized,
                display_reg,
                owner_name.strip(),
                owner_type,
                campus_id.strip() if campus_id else None,
                phone.strip() if phone else None,
                make_model.strip() if make_model else None,
                now_utc,
                now_utc,
            ),
        )
        conn.commit()
        return get_vehicle_by_id(conn, cur.lastrowid)  # type: ignore


def log_gate_event_with_block(
    conn: sqlite3.Connection,
    vehicle_id: int,
    rider_name: str,
    owner_type: str,
    campus_id: Optional[str],
    event_type: str,
    gate_name: str,
    operator_id: int,
    notes: Optional[str] = None,
    difficulty: Optional[int] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Record a gate ENTRY or EXIT and atomically mine & commit its blockchain block.
    
    If event creation, block mining, or database insertion fails at any point,
    the entire transaction is rolled back.
    
    State transition rules:
    - ENTRY is rejected if current status is already INSIDE.
    - EXIT is rejected if current status is OUTSIDE (no active entry).
    """
    event_type = event_type.upper()
    if event_type not in ("ENTRY", "EXIT"):
        raise ValueError(f"Invalid event_type '{event_type}'. Must be ENTRY or EXIT.")

    cur = conn.cursor()

    # Retrieve vehicle
    cur.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    vehicle = cur.fetchone()
    if not vehicle:
        raise ValueError(f"Vehicle #{vehicle_id} does not exist.")

    # Check state transition against derived status
    current_status = get_vehicle_current_status(conn, vehicle_id)
    if event_type == "ENTRY" and current_status == "INSIDE":
        raise ValueError(
            f"Vehicle '{vehicle['display_registration']}' is already INSIDE campus. "
            "An EXIT event must be recorded before another entry."
        )
    if event_type == "EXIT" and current_status == "OUTSIDE":
        raise ValueError(
            f"Vehicle '{vehicle['display_registration']}' is currently OUTSIDE campus. "
            "An active ENTRY event is required before an exit can be logged."
        )

    now_utc = datetime.now(timezone.utc).isoformat()
    reg_snapshot = vehicle["registration_number"]
    rider_snapshot = rider_name.strip()
    category_snapshot = owner_type
    campus_id_snap = campus_id.strip() if campus_id else None

    # Payload for the blockchain block (deterministic canonical snapshot)
    block_payload = {
        "campus_id": campus_id_snap,
        "event_timestamp_utc": now_utc,
        "event_type": event_type,
        "gate_name": gate_name.strip(),
        "operator_id": operator_id,
        "owner_type": category_snapshot,
        "registration_number": reg_snapshot,
        "rider_name": rider_snapshot,
    }

    pow_diff = difficulty if difficulty is not None else Config.POW_DIFFICULTY

    try:
        # 1. Insert gate_events record
        cur.execute(
            """
            INSERT INTO gate_events (
                vehicle_id, registration_number_snapshot, rider_name_snapshot,
                owner_type_snapshot, campus_id_snapshot, event_type, gate_name,
                event_timestamp_utc, operator_id, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                reg_snapshot,
                rider_snapshot,
                category_snapshot,
                campus_id_snap,
                event_type,
                gate_name.strip(),
                now_utc,
                operator_id,
                notes.strip() if notes else None,
                now_utc,
            ),
        )
        event_id = cur.lastrowid

        # 2. Mine the corresponding blockchain block
        block_data = blockchain.build_next_block(
            conn=conn,
            event_id=event_id,
            event_payload=block_payload,
            difficulty=pow_diff,
        )

        # 3. Insert block into blockchain_blocks table
        blockchain.insert_block(conn, block_data)

        # 4. Commit transaction atomically
        conn.commit()

        # Fetch committed records to return
        cur.execute("SELECT * FROM gate_events WHERE id = ?", (event_id,))
        event_record = dict(cur.fetchone())

        cur.execute("SELECT * FROM blockchain_blocks WHERE event_id = ?", (event_id,))
        block_record = dict(cur.fetchone())

        return event_record, block_record

    except Exception:
        conn.rollback()
        raise


def get_dashboard_metrics(conn: sqlite3.Connection, app_tz: Any) -> Dict[str, Any]:
    """Calculate real-time dashboard metrics from SQLite data."""
    cur = conn.cursor()

    # Total registered vehicles
    cur.execute("SELECT COUNT(*) AS total FROM vehicles")
    total_vehicles = cur.fetchone()["total"]

    # Total blockchain blocks
    cur.execute("SELECT COUNT(*) AS total FROM blockchain_blocks")
    total_blocks = cur.fetchone()["total"]

    # Calculate bikes currently INSIDE campus:
    # A bike is inside if its latest gate event is 'ENTRY'
    cur.execute(
        """
        WITH LatestEvents AS (
            SELECT vehicle_id, event_type,
                   ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY id DESC) as rn
            FROM gate_events
        )
        SELECT COUNT(*) AS inside_count
        FROM LatestEvents
        WHERE rn = 1 AND event_type = 'ENTRY';
        """
    )
    inside_count = cur.fetchone()["inside_count"]

    # Entries and exits recorded today (based on local application calendar date)
    now_local = datetime.now(app_tz)
    today_local_str = now_local.strftime("%Y-%m-%d")

    cur.execute("SELECT event_type, event_timestamp_utc FROM gate_events")
    all_events = cur.fetchall()

    entries_today = 0
    exits_today = 0
    for ev in all_events:
        try:
            utc_dt = datetime.fromisoformat(ev["event_timestamp_utc"])
            local_dt = utc_dt.astimezone(app_tz)
            if local_dt.strftime("%Y-%m-%d") == today_local_str:
                if ev["event_type"] == "ENTRY":
                    entries_today += 1
                elif ev["event_type"] == "EXIT":
                    exits_today += 1
        except Exception:
            continue

    # Blockchain integrity quick check
    verification = blockchain.verify_blockchain(conn, difficulty=Config.POW_DIFFICULTY)

    return {
        "inside_count": inside_count,
        "entries_today": entries_today,
        "exits_today": exits_today,
        "total_vehicles": total_vehicles,
        "total_blocks": total_blocks,
        "chain_valid": verification["is_valid"],
        "chain_head_hash": verification["chain_head_hash"],
        "verification_reason": verification["reason"],
    }


def get_recent_events(conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent gate events with joined operator and block hash info."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            ge.*,
            u.username as operator_username,
            v.display_registration,
            bb.block_index,
            bb.block_hash
        FROM gate_events ge
        JOIN users u ON ge.operator_id = u.id
        JOIN vehicles v ON ge.vehicle_id = v.id
        LEFT JOIN blockchain_blocks bb ON bb.event_id = ge.id
        ORDER BY ge.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(r) for r in cur.fetchall()]


def get_filtered_events(
    conn: sqlite3.Connection,
    search: Optional[str] = None,
    event_type: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: Optional[int] = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """Query gate events with flexible search and filtering criteria.
    
    Returns:
        (list_of_events, total_filtered_count)
    """
    cur = conn.cursor()
    conditions = []
    params: List[Any] = []

    if search:
        s = f"%{search.strip()}%"
        conditions.append(
            "(ge.registration_number_snapshot LIKE ? OR ge.rider_name_snapshot LIKE ? OR ge.campus_id_snapshot LIKE ?)"
        )
        params.extend([s, s, s])

    if event_type and event_type in ("ENTRY", "EXIT"):
        conditions.append("ge.event_type = ?")
        params.append(event_type)

    if category and category in ("Student", "Staff", "Visitor"):
        conditions.append("ge.owner_type_snapshot = ?")
        params.append(category)

    if date_from:
        conditions.append("ge.event_timestamp_utc >= ?")
        params.append(f"{date_from}T00:00:00")

    if date_to:
        conditions.append("ge.event_timestamp_utc <= ?")
        params.append(f"{date_to}T23:59:59")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count query
    count_sql = f"SELECT COUNT(*) AS total FROM gate_events ge {where_clause}"
    cur.execute(count_sql, params)
    total_count = cur.fetchone()["total"]

    # Data query
    data_sql = f"""
        SELECT 
            ge.*,
            u.username as operator_username,
            v.display_registration,
            bb.block_index,
            bb.block_hash
        FROM gate_events ge
        JOIN users u ON ge.operator_id = u.id
        JOIN vehicles v ON ge.vehicle_id = v.id
        LEFT JOIN blockchain_blocks bb ON bb.event_id = ge.id
        {where_clause}
        ORDER BY ge.id DESC
    """
    if limit is not None:
        data_sql += " LIMIT ? OFFSET ?"
        cur.execute(data_sql, params + [limit, offset])
    else:
        cur.execute(data_sql, params)

    return [dict(r) for r in cur.fetchall()], total_count


def get_event_detail(conn: sqlite3.Connection, event_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full event detail with related vehicle and blockchain block records."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            ge.*,
            u.username as operator_username,
            v.display_registration,
            v.phone as vehicle_phone,
            v.make_model as vehicle_make_model,
            bb.id as block_id,
            bb.block_index,
            bb.timestamp_utc as block_timestamp_utc,
            bb.previous_hash,
            bb.nonce,
            bb.block_hash,
            bb.data_json
        FROM gate_events ge
        JOIN users u ON ge.operator_id = u.id
        JOIN vehicles v ON ge.vehicle_id = v.id
        LEFT JOIN blockchain_blocks bb ON bb.event_id = ge.id
        WHERE ge.id = ?
        """,
        (event_id,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_all_vehicles(
    conn: sqlite3.Connection,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    owner_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all vehicles with their current computed status and event counts."""
    cur = conn.cursor()
    conditions = []
    params: List[Any] = []

    if search:
        s = f"%{search.strip()}%"
        conditions.append(
            "(v.registration_number LIKE ? OR v.owner_name LIKE ? OR v.campus_id LIKE ?)"
        )
        params.extend([s, s, s])

    if owner_type and owner_type in ("Student", "Staff", "Visitor"):
        conditions.append("v.owner_type = ?")
        params.append(owner_type)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT 
            v.*,
            (SELECT COUNT(*) FROM gate_events WHERE vehicle_id = v.id) as total_events
        FROM vehicles v
        {where_clause}
        ORDER BY v.id DESC
    """
    cur.execute(sql, params)
    vehicles = [dict(r) for r in cur.fetchall()]

    # Derive status for each vehicle
    filtered_vehicles = []
    for v in vehicles:
        v["current_status"] = get_vehicle_current_status(conn, v["id"])
        if status_filter and status_filter.upper() in ("INSIDE", "OUTSIDE"):
            if v["current_status"] != status_filter.upper():
                continue
        filtered_vehicles.append(v)

    return filtered_vehicles


def get_vehicle_event_history(conn: sqlite3.Connection, vehicle_id: int) -> List[Dict[str, Any]]:
    """Retrieve full chronological timeline of entries and exits for a given vehicle."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            ge.*,
            u.username as operator_username,
            bb.block_index,
            bb.block_hash
        FROM gate_events ge
        JOIN users u ON ge.operator_id = u.id
        LEFT JOIN blockchain_blocks bb ON bb.event_id = ge.id
        WHERE ge.vehicle_id = ?
        ORDER BY ge.id DESC
        """,
        (vehicle_id,),
    )
    return [dict(r) for r in cur.fetchall()]


# User Management
def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
    row = cur.fetchone()
    return dict(row) if row else None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def list_users(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, is_active, created_at FROM users ORDER BY id ASC")
    return [dict(r) for r in cur.fetchall()]


def create_user(
    conn: sqlite3.Connection, username: str, password_hash: str, role: str
) -> Dict[str, Any]:
    username_clean = username.strip().lower()
    if role not in ("admin", "guard"):
        raise ValueError("Role must be 'admin' or 'guard'.")

    cur = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, role, is_active, created_at)
        VALUES (?, ?, ?, 1, ?)
        """,
        (username_clean, password_hash, role, now_utc),
    )
    conn.commit()
    return get_user_by_id(conn, cur.lastrowid)  # type: ignore


def toggle_user_active_status(conn: sqlite3.Connection, user_id: int) -> Tuple[bool, str]:
    """Toggle user active state (1 -> 0 or 0 -> 1).
    
    Guards against deactivating the last active administrator.
    """
    cur = conn.cursor()
    user = get_user_by_id(conn, user_id)
    if not user:
        return False, "User not found."

    if user["is_active"] == 1 and user["role"] == "admin":
        cur.execute("SELECT COUNT(*) AS active_admins FROM users WHERE role = 'admin' AND is_active = 1")
        active_admins = cur.fetchone()["active_admins"]
        if active_admins <= 1:
            return False, "Cannot deactivate the only remaining active administrator."

    new_status = 0 if user["is_active"] == 1 else 1
    cur.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    state_str = "activated" if new_status == 1 else "deactivated"
    return True, f"User {user['username']} has been {state_str}."
