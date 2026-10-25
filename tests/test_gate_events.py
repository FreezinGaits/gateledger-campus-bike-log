"""Automated tests for Campus Gate Entry and Exit Operations."""

import pytest
import database


def test_successful_entry_and_exit_cycle(db_conn):
    """Test full valid lifecycle: ENTRY -> EXIT -> subsequent ENTRY."""
    v = database.create_or_update_vehicle(
        db_conn, "PB10XY9999", "Aman Deep", "Student", "CS99", "9812345678", "Pulsar"
    )

    # 1. First ENTRY
    ev1, b1 = database.log_gate_event_with_block(
        db_conn, v["id"], "Aman Deep", "Student", "CS99", "ENTRY", "Main Gate", 1, difficulty=2
    )
    assert ev1["event_type"] == "ENTRY"
    assert b1["block_index"] == 1
    assert database.get_vehicle_current_status(db_conn, v["id"]) == "INSIDE"

    # 2. Valid EXIT
    ev2, b2 = database.log_gate_event_with_block(
        db_conn, v["id"], "Aman Deep", "Student", "CS99", "EXIT", "Main Gate", 1, difficulty=2
    )
    assert ev2["event_type"] == "EXIT"
    assert b2["block_index"] == 2
    assert database.get_vehicle_current_status(db_conn, v["id"]) == "OUTSIDE"

    # 3. Subsequent Re-ENTRY
    ev3, b3 = database.log_gate_event_with_block(
        db_conn, v["id"], "Aman Deep", "Student", "CS99", "ENTRY", "North Gate", 1, difficulty=2
    )
    assert ev3["event_type"] == "ENTRY"
    assert b3["block_index"] == 3
    assert database.get_vehicle_current_status(db_conn, v["id"]) == "INSIDE"


def test_rejection_of_duplicate_entry(db_conn):
    """Attempting an ENTRY when a bike is already INSIDE must be rejected."""
    v = database.create_or_update_vehicle(
        db_conn, "DL04CD1212", "Simran Kaur", "Staff", "EE-01", "9876543210", "Activa"
    )

    # First ENTRY succeeds
    database.log_gate_event_with_block(
        db_conn, v["id"], "Simran Kaur", "Staff", "EE-01", "ENTRY", "Main Gate", 1, difficulty=2
    )
    assert database.get_vehicle_current_status(db_conn, v["id"]) == "INSIDE"

    # Second ENTRY must raise ValueError
    with pytest.raises(ValueError) as exc:
        database.log_gate_event_with_block(
            db_conn, v["id"], "Simran Kaur", "Staff", "EE-01", "ENTRY", "North Gate", 1, difficulty=2
        )
    assert "already INSIDE campus" in str(exc.value)

    # Confirm no orphan event or block was committed
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM gate_events WHERE vehicle_id = ?", (v["id"],))
    assert cur.fetchone()["count"] == 1

    cur.execute("SELECT COUNT(*) AS count FROM blockchain_blocks WHERE block_index > 0")
    assert cur.fetchone()["count"] == 1


def test_rejection_of_exit_without_entry(db_conn):
    """Attempting an EXIT for a bike that is OUTSIDE (or has no entry) must be rejected."""
    v = database.create_or_update_vehicle(
        db_conn, "HR10ZZ4321", "Visitor One", "Visitor", None, "9999900000", "Jupiter"
    )
    assert database.get_vehicle_current_status(db_conn, v["id"]) == "OUTSIDE"

    with pytest.raises(ValueError) as exc:
        database.log_gate_event_with_block(
            db_conn, v["id"], "Visitor One", "Visitor", None, "EXIT", "Main Gate", 1, difficulty=2
        )
    assert "currently OUTSIDE campus" in str(exc.value)

    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM gate_events WHERE vehicle_id = ?", (v["id"],))
    assert cur.fetchone()["count"] == 0


def test_registration_number_normalization():
    """Verify registration normalization handles spaces, lowercase, hyphens, and dots."""
    assert database.normalize_reg_number("pb-10-ab-1234") == "PB10AB1234"
    assert database.normalize_reg_number(" DL 01 CD 5678 ") == "DL01CD5678"
    assert database.normalize_reg_number("hr.26.ef.9012") == "HR26EF9012"

    # Rejection of invalid / empty inputs
    with pytest.raises(ValueError):
        database.normalize_reg_number("")

    with pytest.raises(ValueError):
        database.normalize_reg_number("   ")

    with pytest.raises(ValueError):
        database.normalize_reg_number("A1")  # Too short (< 4 chars)


def test_atomic_transaction_rollback_on_failure(db_conn):
    """Ensure that if mining or block insertion fails, the gate_event is rolled back."""
    v = database.create_or_update_vehicle(
        db_conn, "PB01AT8888", "Rollback Tester", "Student", "CS88", "9870001111", "Bike"
    )

    # Count before
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM gate_events")
    events_before = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) AS count FROM blockchain_blocks")
    blocks_before = cur.fetchone()["count"]

    # Trigger failure with invalid operator_id violating foreign key constraint
    with pytest.raises(Exception):
        database.log_gate_event_with_block(
            db_conn,
            vehicle_id=v["id"],
            rider_name="Rollback Tester",
            owner_type="Student",
            campus_id="CS88",
            event_type="ENTRY",
            gate_name="Main Gate",
            operator_id=999999,  # Non-existent foreign key
            difficulty=2,
        )

    # Confirm neither event nor block was committed
    cur.execute("SELECT COUNT(*) AS count FROM gate_events")
    assert cur.fetchone()["count"] == events_before

    cur.execute("SELECT COUNT(*) AS count FROM blockchain_blocks")
    assert cur.fetchone()["count"] == blocks_before
