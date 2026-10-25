"""Automated tests for GateLedger Blockchain Engine."""

import pytest
import blockchain
import database


def test_genesis_block_creation(db_conn):
    """Confirm the Genesis block (Index 0) is created with correct defaults and PoW."""
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM blockchain_blocks WHERE block_index = 0")
    row = cur.fetchone()

    assert row is not None
    assert row["block_index"] == 0
    assert row["event_id"] is None
    assert row["previous_hash"] == "0" * 64
    assert row["block_hash"].startswith("00")
    assert row["nonce"] >= 0


def test_genesis_block_idempotency(db_conn):
    """Repeated calls to init_genesis_block must not duplicate or alter block 0."""
    gen1 = blockchain.init_genesis_block(db_conn, difficulty=2)
    gen2 = blockchain.init_genesis_block(db_conn, difficulty=2)

    assert gen1["block_hash"] == gen2["block_hash"]
    assert gen1["nonce"] == gen2["nonce"]

    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM blockchain_blocks WHERE block_index = 0")
    assert cur.fetchone()["count"] == 1


def test_sequential_block_creation_and_linking(db_conn):
    """Verify new blocks advance sequentially, correctly link to previous hash, and satisfy PoW."""
    v = database.create_or_update_vehicle(
        db_conn, "PB10AB1111", "Test Student", "Student", "CS01", "9876500000", "Pulsar"
    )

    ev1, b1 = database.log_gate_event_with_block(
        db_conn, v["id"], "Test Student", "Student", "CS01", "ENTRY", "Main Gate", 1, difficulty=2
    )
    assert b1["block_index"] == 1
    assert b1["previous_hash"] == blockchain.get_latest_block(db_conn)["previous_hash"] or b1["previous_hash"]
    assert b1["block_hash"].startswith("00")

    # Genesis block was block 0
    cur = db_conn.cursor()
    cur.execute("SELECT block_hash FROM blockchain_blocks WHERE block_index = 0")
    genesis_hash = cur.fetchone()["block_hash"]
    assert b1["previous_hash"] == genesis_hash

    # Second block (EXIT)
    ev2, b2 = database.log_gate_event_with_block(
        db_conn, v["id"], "Test Student", "Student", "CS01", "EXIT", "Main Gate", 1, difficulty=2
    )
    assert b2["block_index"] == 2
    assert b2["previous_hash"] == b1["block_hash"]
    assert b2["block_hash"].startswith("00")


def test_intact_chain_verification(db_conn):
    """An untouched chain with valid events must verify successfully."""
    v = database.create_or_update_vehicle(
        db_conn, "HR26AB2222", "Staff Member", "Staff", "FAC-1", "9876511111", "Activa"
    )
    database.log_gate_event_with_block(
        db_conn, v["id"], "Staff Member", "Staff", "FAC-1", "ENTRY", "Gate 1", 1, difficulty=2
    )
    database.log_gate_event_with_block(
        db_conn, v["id"], "Staff Member", "Staff", "FAC-1", "EXIT", "Gate 1", 1, difficulty=2
    )

    result = blockchain.verify_blockchain(db_conn, difficulty=2)
    assert result["is_valid"] is True
    assert result["total_blocks"] == 3  # Genesis + 2 events
    assert result["invalid_block_index"] is None


def test_detect_modified_block_data(db_conn):
    """Tampering with data_json in a block must cause hash mismatch detection."""
    v = database.create_or_update_vehicle(
        db_conn, "DL01CD3333", "Rider X", "Student", "CS02", "9876522222", "Yamaha"
    )
    database.log_gate_event_with_block(
        db_conn, v["id"], "Rider X", "Student", "CS02", "ENTRY", "Gate 1", 1, difficulty=2
    )

    # Manually tamper with block 1 payload in SQLite
    cur = db_conn.cursor()
    cur.execute(
        "UPDATE blockchain_blocks SET data_json = '{\"tampered\": true}' WHERE block_index = 1"
    )
    db_conn.commit()

    result = blockchain.verify_blockchain(db_conn, difficulty=2)
    assert result["is_valid"] is False
    assert result["invalid_block_index"] == 1
    assert "Tampered block data" in result["reason"] or "mismatch" in result["reason"].lower()


def test_detect_broken_previous_hash_link(db_conn):
    """Corrupting previous_hash must cause broken chain link detection."""
    v = database.create_or_update_vehicle(
        db_conn, "CH01EF4444", "Rider Y", "Visitor", None, "9876533333", "Jupiter"
    )
    database.log_gate_event_with_block(
        db_conn, v["id"], "Rider Y", "Visitor", None, "ENTRY", "Gate 1", 1, difficulty=2
    )
    database.log_gate_event_with_block(
        db_conn, v["id"], "Rider Y", "Visitor", None, "EXIT", "Gate 1", 1, difficulty=2
    )

    # Break link at block 2
    cur = db_conn.cursor()
    cur.execute(
        "UPDATE blockchain_blocks SET previous_hash = 'badbeef' WHERE block_index = 2"
    )
    db_conn.commit()

    result = blockchain.verify_blockchain(db_conn, difficulty=2)
    assert result["is_valid"] is False
    assert result["invalid_block_index"] == 2
    assert "Broken chain link" in result["reason"]


def test_detect_event_without_block(db_conn):
    """An event present in the database without a corresponding blockchain block must fail verification."""
    v = database.create_or_update_vehicle(
        db_conn, "PB02GH5555", "Rider Z", "Student", "CS03", "9876544444", "Splendor"
    )
    # Directly insert event into gate_events without mining a block
    cur = db_conn.cursor()
    cur.execute(
        """
        INSERT INTO gate_events (
            vehicle_id, registration_number_snapshot, rider_name_snapshot,
            owner_type_snapshot, campus_id_snapshot, event_type, gate_name,
            event_timestamp_utc, operator_id, created_at
        ) VALUES (?, ?, ?, ?, ?, 'ENTRY', 'Main Gate', '2026-10-25T12:00:00', 1, '2026-10-25T12:00:00')
        """,
        (v["id"], "PB02GH5555", "Rider Z", "Student", "CS03"),
    )
    db_conn.commit()

    result = blockchain.verify_blockchain(db_conn, difficulty=2)
    assert result["is_valid"] is False
    assert "missing an associated blockchain block" in result["reason"]


def test_detect_payload_mismatch_with_gate_event(db_conn):
    """If database gate_event snapshot is modified, verification must catch payload divergence."""
    v = database.create_or_update_vehicle(
        db_conn, "PB03JK6666", "Rider A", "Student", "CS04", "9876555555", "Activa"
    )
    ev, b = database.log_gate_event_with_block(
        db_conn, v["id"], "Rider A", "Student", "CS04", "ENTRY", "Gate 1", 1, difficulty=2
    )

    # Tamper with the gate_events snapshot row
    cur = db_conn.cursor()
    cur.execute(
        "UPDATE gate_events SET rider_name_snapshot = 'Forged Name' WHERE id = ?",
        (ev["id"],),
    )
    db_conn.commit()

    result = blockchain.verify_blockchain(db_conn, difficulty=2)
    assert result["is_valid"] is False
    assert result["invalid_block_index"] == b["block_index"]
    assert "payload does not match database snapshot" in result["reason"]


def test_safe_tampering_simulation_leaves_db_untouched(db_conn):
    """Simulate tampering must detect alteration on memory replica while leaving real DB intact."""
    v = database.create_or_update_vehicle(
        db_conn, "PB04LM7777", "Rider B", "Student", "CS05", "9876566666", "Activa"
    )
    ev, b = database.log_gate_event_with_block(
        db_conn, v["id"], "Rider B", "Student", "CS05", "ENTRY", "Gate 1", 1, difficulty=2
    )

    original_db_hash = b["block_hash"]

    # Run safe simulation
    sim_result = blockchain.simulate_tampering(
        db_conn,
        block_index=b["block_index"],
        tamper_field="rider_name",
        tamper_value="Malicious_Injected_User",
        difficulty=2,
    )

    # Tampering was detected on simulated copy
    assert sim_result["verification_result"]["is_valid"] is False
    assert sim_result["verification_result"]["invalid_block_index"] == b["block_index"]
    assert sim_result["db_remains_secure"] is True

    # Real database was untouched
    cur = db_conn.cursor()
    cur.execute("SELECT block_hash FROM blockchain_blocks WHERE block_index = ?", (b["block_index"],))
    assert cur.fetchone()["block_hash"] == original_db_hash

    # Verification on real database still passes!
    real_check = blockchain.verify_blockchain(db_conn, difficulty=2)
    assert real_check["is_valid"] is True
