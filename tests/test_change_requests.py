"""Tests for Maker-Checker Dual-Control Change Request Workflow
=============================================================
Verifies that guards can submit profile change requests, master profiles
remain unaltered until reviewed, admins can approve or reject requests,
and RBAC prevents unauthorized modifications.
"""

import pytest
import database


def test_database_change_request_lifecycle(db_conn):
    """Direct database test of change request creation, query, and approval."""
    # Create test vehicle
    v = database.create_or_update_vehicle(
        db_conn, "PB10TEST01", "Original Owner", "Student", "STU-001", "9800000001", "Bike Model 1"
    )

    # 1. Guard (user_id=2) creates change request
    req = database.create_change_request(
        conn=db_conn,
        vehicle_id=v["id"],
        requester_id=2,
        proposed_owner_name="Corrected Owner",
        proposed_owner_type="Staff",
        proposed_campus_id="FAC-999",
        proposed_phone="9800000099",
        proposed_make_model="Bike Model 2",
        reason="Owner changed status from Student to Staff.",
    )
    assert req["status"] == "PENDING"
    assert req["proposed_owner_name"] == "Corrected Owner"

    # Verify vehicle record is still unchanged
    v_orig = database.get_vehicle_by_id(db_conn, v["id"])
    assert v_orig["owner_name"] == "Original Owner"

    # 2. Query change requests
    pending = database.list_change_requests(db_conn, status_filter="PENDING")
    assert any(r["id"] == req["id"] for r in pending)

    # 3. Admin approves request
    success, msg = database.approve_change_request(db_conn, req["id"], reviewer_id=1)
    assert success is True
    assert "approved and applied" in msg

    # Verify vehicle record is now updated
    v_updated = database.get_vehicle_by_id(db_conn, v["id"])
    assert v_updated["owner_name"] == "Corrected Owner"
    assert v_updated["owner_type"] == "Staff"
    assert v_updated["campus_id"] == "FAC-999"

    # Attempting to re-approve must fail
    success2, msg2 = database.approve_change_request(db_conn, req["id"], reviewer_id=1)
    assert success2 is False
    assert "already been processed" in msg2


def test_database_change_request_rejection(db_conn):
    """Test rejecting a change request keeps vehicle profile intact."""
    v = database.create_or_update_vehicle(
        db_conn, "PB10TEST02", "Legit Owner", "Student", "STU-002", "9800000002", "Bike Model A"
    )

    req = database.create_change_request(
        conn=db_conn,
        vehicle_id=v["id"],
        requester_id=2,
        proposed_owner_name="Impostor Name",
        proposed_owner_type="Visitor",
        proposed_campus_id=None,
        proposed_phone=None,
        proposed_make_model=None,
        reason="Suspicious request.",
    )

    success, msg = database.reject_change_request(
        db_conn, req["id"], reviewer_id=1, review_notes="ID does not match student database."
    )
    assert success is True
    assert "rejected" in msg

    # Verify vehicle is untouched
    v_curr = database.get_vehicle_by_id(db_conn, v["id"])
    assert v_curr["owner_name"] == "Legit Owner"

    # Check request status
    req_after = database.get_change_request_by_id(db_conn, req["id"])
    assert req_after["status"] == "REJECTED"
    assert req_after["review_notes"] == "ID does not match student database."


def test_guard_submit_and_admin_approve_flow(client, db_conn):
    """Full HTTP test: guard submits request, admin approves it via web interface."""
    # Seed a vehicle
    v = database.create_or_update_vehicle(
        db_conn, "KA05MC1111", "Student One", "Student", "CS101", "9811111111", "Pulsar 150"
    )

    # 1. Guard logs in
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["_csrf_token"]
    client.post("/login", data={"username": "guard@campus.local", "password": "Guard@123", "csrf_token": csrf})

    # Guard submits correction request
    with client.session_transaction() as sess:
        csrf = sess["_csrf_token"]
    submit_resp = client.post(
        f"/vehicles/{v['id']}/request-change",
        data={
            "csrf_token": csrf,
            "proposed_owner_name": "Student One Updated",
            "proposed_owner_type": "Student",
            "proposed_campus_id": "CS101",
            "proposed_phone": "9811111111",
            "proposed_make_model": "Pulsar 150 Black",
            "reason": "Corrected name spelling per college ID card.",
        },
        follow_redirects=True,
    )
    assert submit_resp.status_code == 200
    assert b"submitted to Administrator" in submit_resp.data

    # 2. Guard cannot access admin requests page (redirects with access denied)
    admin_page = client.get("/admin/requests", follow_redirects=True)
    assert admin_page.status_code == 200
    assert b"Administrator privileges are required" in admin_page.data

    # 3. Guard logs out and Admin logs in
    client.get("/logout")
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["_csrf_token"]
    client.post("/login", data={"username": "admin@campus.local", "password": "Admin@123", "csrf_token": csrf})

    # Admin visits admin requests page
    reqs_resp = client.get("/admin/requests")
    assert reqs_resp.status_code == 200
    assert b"Student One Updated" in reqs_resp.data

    # Admin approves request
    reqs = database.list_change_requests(db_conn, status_filter="PENDING")
    req_id = reqs[0]["id"]

    with client.session_transaction() as sess:
        csrf = sess["_csrf_token"]
    appr_resp = client.post(
        f"/admin/requests/{req_id}/approve",
        data={"csrf_token": csrf},
        follow_redirects=True,
    )
    assert appr_resp.status_code == 200
    assert b"approved and applied" in appr_resp.data

    # Check vehicle detail shows new name
    detail_resp = client.get(f"/vehicles/{v['id']}")
    assert b"Student One Updated" in detail_resp.data
