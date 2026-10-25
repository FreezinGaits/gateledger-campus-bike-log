"""GateLedger Blockchain Module
=================================
Educational, persistent, single-node SHA-256 Proof-of-Work blockchain ledger
designed for campus vehicle entry and exit audit logging.
"""

from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


def canonical_json(data: Any) -> str:
    """Serialize data into a deterministic, canonical JSON string with sorted keys.
    
    This ensures that equivalent data dictionaries always yield identical byte representations
    for SHA-256 hashing regardless of key insertion order.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def calculate_block_hash(
    block_index: int,
    timestamp_utc: str,
    event_id: Optional[int],
    data_json: str,
    previous_hash: str,
    nonce: int,
) -> str:
    """Calculate the cryptographic SHA-256 hash of a block.
    
    The hash is computed over all essential header and payload fields:
    SHA-256(index | timestamp | event_id | canonical_payload | previous_hash | nonce)
    """
    event_str = str(event_id) if event_id is not None else ""
    raw_string = f"{block_index}|{timestamp_utc}|{event_str}|{data_json}|{previous_hash}|{nonce}"
    return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()


def mine_block(
    block_index: int,
    timestamp_utc: str,
    event_id: Optional[int],
    data_json: str,
    previous_hash: str,
    difficulty: int = 2,
) -> Tuple[int, str]:
    """Perform Proof-of-Work mining by finding a nonce such that the block hash
    begins with `difficulty` leading hexadecimal zeros (e.g. '00' for difficulty=2).
    
    Returns:
        (nonce, block_hash)
    """
    target_prefix = "0" * difficulty
    nonce = 0
    while True:
        computed_hash = calculate_block_hash(
            block_index=block_index,
            timestamp_utc=timestamp_utc,
            event_id=event_id,
            data_json=data_json,
            previous_hash=previous_hash,
            nonce=nonce,
        )
        if computed_hash.startswith(target_prefix):
            return nonce, computed_hash
        nonce += 1


def init_genesis_block(conn: sqlite3.Connection, difficulty: int = 2) -> Dict[str, Any]:
    """Ensure the immutable Genesis block (Index 0) exists.
    
    This operation is strictly idempotent: if Block 0 already exists in the
    database, it is loaded and returned without modifications.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM blockchain_blocks WHERE block_index = 0 LIMIT 1"
    )
    row = cursor.fetchone()
    if row is not None:
        return dict(row)

    # Genesis block definitions
    block_index = 0
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    event_id = None
    genesis_data = {
        "message": "GateLedger Genesis Block - Campus Security Ledger Initialized",
        "system": "GateLedger Academic Blockchain v1.0",
        "algorithm": "SHA-256 Proof-of-Work",
    }
    data_json = canonical_json(genesis_data)
    previous_hash = "0" * 64

    nonce, block_hash = mine_block(
        block_index=block_index,
        timestamp_utc=timestamp_utc,
        event_id=event_id,
        data_json=data_json,
        previous_hash=previous_hash,
        difficulty=difficulty,
    )

    cursor.execute(
        """
        INSERT INTO blockchain_blocks (
            block_index, timestamp_utc, event_id, data_json, previous_hash, nonce, block_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (block_index, timestamp_utc, event_id, data_json, previous_hash, nonce, block_hash),
    )
    conn.commit()

    cursor.execute("SELECT * FROM blockchain_blocks WHERE block_index = 0")
    return dict(cursor.fetchone())


def get_latest_block(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """Fetch the latest block on the active chain head."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM blockchain_blocks ORDER BY block_index DESC LIMIT 1"
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def build_next_block(
    conn: sqlite3.Connection,
    event_id: int,
    event_payload: Dict[str, Any],
    difficulty: int = 2,
) -> Dict[str, Any]:
    """Construct and mine the next sequential block for a newly created gate event.
    
    Does NOT commit the database transaction; the calling routine commits
    both the gate event and this block atomically.
    """
    latest = get_latest_block(conn)
    if latest is None:
        raise ValueError("Cannot append block: Genesis block does not exist.")

    next_index = latest["block_index"] + 1
    previous_hash = latest["block_hash"]
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    data_json = canonical_json(event_payload)

    nonce, block_hash = mine_block(
        block_index=next_index,
        timestamp_utc=timestamp_utc,
        event_id=event_id,
        data_json=data_json,
        previous_hash=previous_hash,
        difficulty=difficulty,
    )

    return {
        "block_index": next_index,
        "timestamp_utc": timestamp_utc,
        "event_id": event_id,
        "data_json": data_json,
        "previous_hash": previous_hash,
        "nonce": nonce,
        "block_hash": block_hash,
    }


def insert_block(conn: sqlite3.Connection, block: Dict[str, Any]) -> int:
    """Insert a mined block into the blockchain_blocks table.
    
    Must be called within an active transaction.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO blockchain_blocks (
            block_index, timestamp_utc, event_id, data_json, previous_hash, nonce, block_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            block["block_index"],
            block["timestamp_utc"],
            block["event_id"],
            block["data_json"],
            block["previous_hash"],
            block["nonce"],
            block["block_hash"],
        ),
    )
    return cursor.lastrowid


def verify_blockchain(
    conn: sqlite3.Connection,
    blocks_override: Optional[List[Dict[str, Any]]] = None,
    difficulty: int = 2,
) -> Dict[str, Any]:
    """Comprehensively verify the integrity of the blockchain.
    
    Checks:
    1. Chain is non-empty.
    2. Genesis block has index 0, valid initial previous_hash, valid PoW, and matching SHA-256.
    3. Block indices are sequential with no skips or duplicates.
    4. Each block's previous_hash exactly matches the preceding block's hash.
    5. Recomputed SHA-256 matches stored block_hash.
    6. Mined block hash satisfies Proof-of-Work difficulty prefix.
    7. Cross-check against gate_events table (when verifying database chain):
       - Every non-genesis block references an existing gate event.
       - The block payload matches the event snapshot in gate_events.
       - No gate event in the database is missing a block.
       - No duplicate events are logged across blocks.

    Returns a structured verification report.
    """
    checked_at = datetime.now(timezone.utc).isoformat()
    target_prefix = "0" * difficulty

    if blocks_override is not None:
        blocks = blocks_override
        is_simulation = True
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")
        blocks = [dict(r) for r in cursor.fetchall()]
        is_simulation = False

    total_blocks = len(blocks)
    if total_blocks == 0:
        return {
            "is_valid": False,
            "total_blocks": 0,
            "invalid_block_index": None,
            "reason": "Blockchain is empty. No Genesis block found.",
            "checked_at": checked_at,
            "difficulty": difficulty,
            "chain_head_hash": None,
        }

    # 1. Verify Genesis Block (Index 0)
    genesis = blocks[0]
    if genesis["block_index"] != 0:
        return {
            "is_valid": False,
            "total_blocks": total_blocks,
            "invalid_block_index": genesis["block_index"],
            "reason": f"First block has invalid index {genesis['block_index']} (must be 0).",
            "checked_at": checked_at,
            "difficulty": difficulty,
            "chain_head_hash": blocks[-1]["block_hash"],
        }

    expected_genesis_prev = "0" * 64
    if genesis["previous_hash"] != expected_genesis_prev:
        return {
            "is_valid": False,
            "total_blocks": total_blocks,
            "invalid_block_index": 0,
            "reason": f"Genesis block previous_hash '{genesis['previous_hash']}' does not match expected genesis hash '{expected_genesis_prev}'.",
            "checked_at": checked_at,
            "difficulty": difficulty,
            "chain_head_hash": blocks[-1]["block_hash"],
        }

    recomputed_genesis_hash = calculate_block_hash(
        block_index=genesis["block_index"],
        timestamp_utc=genesis["timestamp_utc"],
        event_id=genesis["event_id"],
        data_json=genesis["data_json"],
        previous_hash=genesis["previous_hash"],
        nonce=genesis["nonce"],
    )
    if recomputed_genesis_hash != genesis["block_hash"]:
        return {
            "is_valid": False,
            "total_blocks": total_blocks,
            "invalid_block_index": 0,
            "reason": f"Genesis block hash mismatch. Stored: {genesis['block_hash']}, Recomputed: {recomputed_genesis_hash}",
            "checked_at": checked_at,
            "difficulty": difficulty,
            "chain_head_hash": blocks[-1]["block_hash"],
        }

    if not genesis["block_hash"].startswith(target_prefix):
        return {
            "is_valid": False,
            "total_blocks": total_blocks,
            "invalid_block_index": 0,
            "reason": f"Genesis block hash does not satisfy Proof of Work difficulty ({difficulty} leading zeros).",
            "checked_at": checked_at,
            "difficulty": difficulty,
            "chain_head_hash": blocks[-1]["block_hash"],
        }

    seen_event_ids = set()

    # 2. Verify Subsequent Blocks
    for i in range(1, total_blocks):
        current = blocks[i]
        prev = blocks[i - 1]

        # Sequential index check
        if current["block_index"] != i:
            return {
                "is_valid": False,
                "total_blocks": total_blocks,
                "invalid_block_index": current["block_index"],
                "reason": f"Non-sequential block index detected. Expected {i}, found {current['block_index']}.",
                "checked_at": checked_at,
                "difficulty": difficulty,
                "chain_head_hash": blocks[-1]["block_hash"],
            }

        # Chain linkage check
        if current["previous_hash"] != prev["block_hash"]:
            return {
                "is_valid": False,
                "total_blocks": total_blocks,
                "invalid_block_index": current["block_index"],
                "reason": (
                    f"Broken chain link at Block #{current['block_index']}. "
                    f"Previous hash '{current['previous_hash']}' does not match "
                    f"preceding block hash '{prev['block_hash']}'."
                ),
                "checked_at": checked_at,
                "difficulty": difficulty,
                "chain_head_hash": blocks[-1]["block_hash"],
            }

        # SHA-256 hash recalculation check
        recomputed_hash = calculate_block_hash(
            block_index=current["block_index"],
            timestamp_utc=current["timestamp_utc"],
            event_id=current["event_id"],
            data_json=current["data_json"],
            previous_hash=current["previous_hash"],
            nonce=current["nonce"],
        )
        if recomputed_hash != current["block_hash"]:
            return {
                "is_valid": False,
                "total_blocks": total_blocks,
                "invalid_block_index": current["block_index"],
                "reason": (
                    f"Tampered block data at Block #{current['block_index']}. "
                    f"Stored hash '{current['block_hash']}' != Recomputed SHA-256 '{recomputed_hash}'."
                ),
                "checked_at": checked_at,
                "difficulty": difficulty,
                "chain_head_hash": blocks[-1]["block_hash"],
            }

        # Proof-of-Work check
        if not current["block_hash"].startswith(target_prefix):
            return {
                "is_valid": False,
                "total_blocks": total_blocks,
                "invalid_block_index": current["block_index"],
                "reason": (
                    f"Block #{current['block_index']} fails Proof of Work. "
                    f"Hash '{current['block_hash']}' does not start with '{target_prefix}'."
                ),
                "checked_at": checked_at,
                "difficulty": difficulty,
                "chain_head_hash": blocks[-1]["block_hash"],
            }

        # Duplicate event association check
        if current["event_id"] is not None:
            if current["event_id"] in seen_event_ids:
                return {
                    "is_valid": False,
                    "total_blocks": total_blocks,
                    "invalid_block_index": current["block_index"],
                    "reason": f"Duplicate event_id {current['event_id']} referenced in multiple blocks.",
                    "checked_at": checked_at,
                    "difficulty": difficulty,
                    "chain_head_hash": blocks[-1]["block_hash"],
                }
            seen_event_ids.add(current["event_id"])

    # 3. Database consistency cross-check (only for persisted verification)
    if not is_simulation:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gate_events ORDER BY id ASC")
        db_events = {row["id"]: dict(row) for row in cursor.fetchall()}

        # Verify every non-genesis block matches a database gate event
        for i in range(1, total_blocks):
            blk = blocks[i]
            event_id = blk["event_id"]
            if event_id not in db_events:
                return {
                    "is_valid": False,
                    "total_blocks": total_blocks,
                    "invalid_block_index": blk["block_index"],
                    "reason": f"Block #{blk['block_index']} references non-existent gate_event #{event_id}.",
                    "checked_at": checked_at,
                    "difficulty": difficulty,
                    "chain_head_hash": blocks[-1]["block_hash"],
                }
            
            ev = db_events[event_id]
            expected_payload = {
                "campus_id": ev["campus_id_snapshot"],
                "event_timestamp_utc": ev["event_timestamp_utc"],
                "event_type": ev["event_type"],
                "gate_name": ev["gate_name"],
                "operator_id": ev["operator_id"],
                "owner_type": ev["owner_type_snapshot"],
                "registration_number": ev["registration_number_snapshot"],
                "rider_name": ev["rider_name_snapshot"],
            }
            if blk["data_json"] != canonical_json(expected_payload):
                return {
                    "is_valid": False,
                    "total_blocks": total_blocks,
                    "invalid_block_index": blk["block_index"],
                    "reason": f"Block #{blk['block_index']} payload does not match database snapshot for event #{event_id}.",
                    "checked_at": checked_at,
                    "difficulty": difficulty,
                    "chain_head_hash": blocks[-1]["block_hash"],
                }

        # Check if any gate event is missing from the blockchain
        missing_events = set(db_events.keys()) - seen_event_ids
        if missing_events:
            first_missing = sorted(missing_events)[0]
            return {
                "is_valid": False,
                "total_blocks": total_blocks,
                "invalid_block_index": None,
                "reason": f"Database gate_event #{first_missing} is missing an associated blockchain block.",
                "checked_at": checked_at,
                "difficulty": difficulty,
                "chain_head_hash": blocks[-1]["block_hash"],
            }

    return {
        "is_valid": True,
        "total_blocks": total_blocks,
        "invalid_block_index": None,
        "reason": "All blocks sequentially linked and verified with SHA-256 and Proof of Work.",
        "checked_at": checked_at,
        "difficulty": difficulty,
        "chain_head_hash": blocks[-1]["block_hash"],
    }


def simulate_tampering(
    conn: sqlite3.Connection,
    block_index: Optional[int] = None,
    tamper_field: str = "rider_name",
    tamper_value: str = "Malicious Impersonator (Tampered)",
    difficulty: int = 2,
) -> Dict[str, Any]:
    """Demonstrate blockchain tamper detection SAFELY.
    
    Creates an IN-MEMORY copy of the blockchain blocks, alters data in the
    chosen block, and runs verification against the tampered copy.
    The real SQLite database is NEVER modified.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")
    rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        raise ValueError("Blockchain contains no blocks to tamper with.")

    # Target block: default to latest block or block 1 if available
    if block_index is None:
        target_idx = rows[-1]["block_index"]
    else:
        target_idx = block_index

    # Find the target block in our in-memory list
    found_pos = None
    for idx, b in enumerate(rows):
        if b["block_index"] == target_idx:
            found_pos = idx
            break

    if found_pos is None:
        raise ValueError(f"Block with index {target_idx} not found.")

    # Deep copy the block array so the database and original values remain 100% untouched
    simulated_blocks = copy.deepcopy(rows)
    target_block = simulated_blocks[found_pos]

    original_data_json = target_block["data_json"]
    original_block_hash = target_block["block_hash"]

    # Parse and tamper with the data payload
    try:
        payload = json.loads(original_data_json)
    except Exception:
        payload = {"data": original_data_json}

    payload[tamper_field] = tamper_value
    tampered_data_json = canonical_json(payload)

    # Assign tampered payload without re-mining nonce or changing hash
    target_block["data_json"] = tampered_data_json

    # Calculate what the hash WOULD BE if recomputed with tampered data
    expected_recomputed_hash = calculate_block_hash(
        block_index=target_block["block_index"],
        timestamp_utc=target_block["timestamp_utc"],
        event_id=target_block["event_id"],
        data_json=target_block["data_json"],
        previous_hash=target_block["previous_hash"],
        nonce=target_block["nonce"],
    )

    # Run full verification on the tampered in-memory chain
    verification_result = verify_blockchain(
        conn=conn,
        blocks_override=simulated_blocks,
        difficulty=difficulty,
    )

    # Double-check that original database was NOT touched
    cursor.execute("SELECT block_hash, data_json FROM blockchain_blocks WHERE block_index = ?", (target_idx,))
    db_row = cursor.fetchone()
    db_remains_unchanged = (
        db_row is not None
        and db_row["block_hash"] == original_block_hash
        and db_row["data_json"] == original_data_json
    )

    return {
        "tampered_block_index": target_idx,
        "original_payload": original_data_json,
        "tampered_payload": tampered_data_json,
        "original_hash": original_block_hash,
        "recomputed_hash": expected_recomputed_hash,
        "verification_result": verification_result,
        "db_remains_secure": db_remains_unchanged,
    }
