"""Automated tests for Gate Records Reporting and CSV Export."""

import csv
import io
import pytest
import database


def test_csv_export_contains_correct_records(auth_admin, db_conn):
    """CSV export returns a valid CSV with correct headers and committed passage data."""
    v = database.create_or_update_vehicle(
        db_conn, "PB10TEST11", "Export Tester", "Student", "EXP-01", "9876599999", "Scooter"
    )
    ev, blk = database.log_gate_event_with_block(
        db_conn, v["id"], "Export Tester", "Student", "EXP-01", "ENTRY", "Main Gate", 1, difficulty=2
    )

    resp = auth_admin.get("/events/export/csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "attachment; filename=" in resp.headers["Content-Disposition"]

    content = resp.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    # Check header
    header = rows[0]
    assert "Event ID" in header
    assert "Registration Number" in header
    assert "Rider Name" in header
    assert "Blockchain Block Hash" in header

    # Check data row
    data_rows = rows[1:]
    assert len(data_rows) >= 1
    found = any(r[1] == "PB10TEST11" and r[2] == "Export Tester" and r[5] == "ENTRY" for r in data_rows)
    assert found is True


def test_csv_export_filters(auth_admin, db_conn):
    """CSV export properly respects event type and search filters."""
    v1 = database.create_or_update_vehicle(db_conn, "PB10FLT1", "Alpha Rider", "Student", "A-1")
    v2 = database.create_or_update_vehicle(db_conn, "PB10FLT2", "Beta Rider", "Staff", "B-2")

    database.log_gate_event_with_block(
        db_conn, v1["id"], "Alpha Rider", "Student", "A-1", "ENTRY", "Main Gate", 1, difficulty=2
    )
    database.log_gate_event_with_block(
        db_conn, v2["id"], "Beta Rider", "Staff", "B-2", "ENTRY", "North Gate", 1, difficulty=2
    )
    database.log_gate_event_with_block(
        db_conn, v1["id"], "Alpha Rider", "Student", "A-1", "EXIT", "Main Gate", 1, difficulty=2
    )

    # Filter by EXIT only
    resp = auth_admin.get("/events/export/csv?type=EXIT")
    assert resp.status_code == 200
    rows = list(csv.reader(io.StringIO(resp.data.decode("utf-8"))))[1:]
    assert len(rows) == 1
    assert rows[0][1] == "PB10FLT1"
    assert rows[0][5] == "EXIT"

    # Filter by search "Beta"
    resp_beta = auth_admin.get("/events/export/csv?search=Beta")
    assert resp_beta.status_code == 200
    rows_beta = list(csv.reader(io.StringIO(resp_beta.data.decode("utf-8"))))[1:]
    assert len(rows_beta) == 1
    assert rows_beta[0][2] == "Beta Rider"


def test_empty_csv_export(auth_admin):
    """Filtering with zero matches returns CSV headers with no data rows without error."""
    resp = auth_admin.get("/events/export/csv?search=NonExistentRegistration999999")
    assert resp.status_code == 200
    reader = csv.reader(io.StringIO(resp.data.decode("utf-8")))
    rows = list(reader)
    assert len(rows) == 1  # Only header
    assert rows[0][0] == "Event ID"
