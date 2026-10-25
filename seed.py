"""GateLedger Demonstration Data Seeder
========================================
Populates realistic fictional vehicles, valid ENTRY/EXIT event sequences,
and mined SHA-256 blockchain blocks for testing and viva demonstration.
"""

import sys
from config import Config
import database


def seed_demo_data(db_path: str = None) -> None:
    """Seed sample campus vehicles, sequential gate events, and Maker-Checker change requests."""
    database.init_db(db_path)
    conn = database.get_db(db_path)
    cur = conn.cursor()

    # Check guard user
    cur.execute("SELECT id FROM users WHERE username = ?", (Config.DEFAULT_GUARD_USER,))
    guard = cur.fetchone()
    guard_id = guard["id"] if guard else 1

    cur.execute("SELECT id FROM users WHERE username = ?", (Config.DEFAULT_ADMIN_USER,))
    admin = cur.fetchone()
    admin_id = admin["id"] if admin else 1

    # Check if events already exist
    cur.execute("SELECT COUNT(*) AS count FROM gate_events")
    events_exist = cur.fetchone()["count"] > 0

    if not events_exist:
        print("[+] Seeding demo campus vehicles and gate events...")

        # Vehicle 1: Student (Honda Activa 6G)
        v1 = database.create_or_update_vehicle(
            conn=conn,
            registration_number="PB10AB1234",
            owner_name="Rohan Sharma",
            owner_type="Student",
            campus_id="CS2023-441",
            phone="9876543210",
            make_model="Honda Activa 6G (Grey)",
        )

        # Vehicle 2: Staff (Royal Enfield)
        v2 = database.create_or_update_vehicle(
            conn=conn,
            registration_number="DL03XY8899",
            owner_name="Dr. Priya Verma",
            owner_type="Staff",
            campus_id="FAC-109",
            phone="9811223344",
            make_model="Royal Enfield Classic 350 (Black)",
        )

        # Vehicle 3: Visitor (TVS Jupiter)
        v3 = database.create_or_update_vehicle(
            conn=conn,
            registration_number="HR26DQ4321",
            owner_name="Suresh Kumar",
            owner_type="Visitor",
            campus_id=None,
            phone="9988776655",
            make_model="TVS Jupiter 125 (Blue)",
        )

        # Vehicle 4: Student (Yamaha FZ-S)
        v4 = database.create_or_update_vehicle(
            conn=conn,
            registration_number="CH01BK9001",
            owner_name="Ananya Singh",
            owner_type="Student",
            campus_id="ME2022-118",
            phone="9765432109",
            make_model="Yamaha FZ-S V4 (Red)",
        )

        # Vehicle 5: Staff (Bajaj Pulsar)
        v5 = database.create_or_update_vehicle(
            conn=conn,
            registration_number="PB65AZ5520",
            owner_name="Arvind Patel",
            owner_type="Staff",
            campus_id="ADM-045",
            phone="9855512345",
            make_model="Bajaj Pulsar 150 (Silver)",
        )

        # Log Events:
        # 1. v1 (Rohan) enters Main Gate -> Block 1
        ev1, b1 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v1["id"],
            rider_name="Rohan Sharma",
            owner_type="Student",
            campus_id="CS2023-441",
            event_type="ENTRY",
            gate_name="Main Gate (Gate 1)",
            operator_id=guard_id,
            notes="Morning class entry. Helmet verified.",
        )
        print(f"  [+] Logged ENTRY for {v1['display_registration']} -> Block #{b1['block_index']} ({b1['block_hash'][:12]}...)")

        # 2. v2 (Dr. Priya) enters North Gate -> Block 2
        ev2, b2 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v2["id"],
            rider_name="Dr. Priya Verma",
            owner_type="Staff",
            campus_id="FAC-109",
            event_type="ENTRY",
            gate_name="North Gate (Gate 2)",
            operator_id=admin_id,
            notes="Faculty entry for Department Meeting.",
        )
        print(f"  [+] Logged ENTRY for {v2['display_registration']} -> Block #{b2['block_index']} ({b2['block_hash'][:12]}...)")

        # 3. v2 exits Main Gate -> Block 3 (Valid Exit after Entry)
        ev3, b3 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v2["id"],
            rider_name="Dr. Priya Verma",
            owner_type="Staff",
            campus_id="FAC-109",
            event_type="EXIT",
            gate_name="Main Gate (Gate 1)",
            operator_id=guard_id,
            notes="Faculty left for lunch off-campus.",
        )
        print(f"  [+] Logged EXIT for {v2['display_registration']} -> Block #{b3['block_index']} ({b3['block_hash'][:12]}...)")

        # 4. v3 (Suresh Kumar - Visitor) enters Main Gate -> Block 4
        ev4, b4 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v3["id"],
            rider_name="Suresh Kumar",
            owner_type="Visitor",
            campus_id=None,
            event_type="ENTRY",
            gate_name="Main Gate (Gate 1)",
            operator_id=guard_id,
            notes="Guest lecture delivery at Auditorium.",
        )
        print(f"  [+] Logged ENTRY for {v3['display_registration']} -> Block #{b4['block_index']} ({b4['block_hash'][:12]}...)")

        # 5. v3 exits Main Gate -> Block 5
        ev5, b5 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v3["id"],
            rider_name="Suresh Kumar",
            owner_type="Visitor",
            campus_id=None,
            event_type="EXIT",
            gate_name="Main Gate (Gate 1)",
            operator_id=guard_id,
            notes="Guest lecture completed.",
        )
        print(f"  [+] Logged EXIT for {v3['display_registration']} -> Block #{b5['block_index']} ({b5['block_hash'][:12]}...)")

        # 6. v4 (Ananya Singh) enters South Gate -> Block 6
        ev6, b6 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v4["id"],
            rider_name="Ananya Singh",
            owner_type="Student",
            campus_id="ME2022-118",
            event_type="ENTRY",
            gate_name="South Gate (Gate 3)",
            operator_id=guard_id,
            notes="Library study session entry.",
        )
        print(f"  [+] Logged ENTRY for {v4['display_registration']} -> Block #{b6['block_index']} ({b6['block_hash'][:12]}...)")

        # 7. v5 (Arvind Patel) enters Main Gate -> Block 7
        ev7, b7 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v5["id"],
            rider_name="Arvind Patel",
            owner_type="Staff",
            campus_id="ADM-045",
            event_type="ENTRY",
            gate_name="Main Gate (Gate 1)",
            operator_id=admin_id,
            notes="Administrative office morning arrival.",
        )
        print(f"  [+] Logged ENTRY for {v5['display_registration']} -> Block #{b7['block_index']} ({b7['block_hash'][:12]}...)")

        # Vehicle 6: Rahul Sharma (Computer Science Student)
        v6 = database.create_or_update_vehicle(
            conn=conn,
            registration_number="KA05XY1234",
            owner_name="Rahul Sharma",
            owner_type="Student",
            campus_id="CS2024-501",
            phone="9876543210",
            make_model="TVS Apache RTR 160 (Black)",
        )

        # 8. v6 (Rahul Sharma) enters Main Gate -> Block 8
        ev8, b8 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v6["id"],
            rider_name="Rahul Sharma",
            owner_type="Student",
            campus_id="CS2024-501",
            event_type="ENTRY",
            gate_name="Main Gate (Gate 1)",
            operator_id=guard_id,
            notes="Morning lecture attendance.",
        )
        print(f"  [+] Logged ENTRY for {v6['display_registration']} -> Block #{b8['block_index']} ({b8['block_hash'][:12]}...)")

        # 9. v6 (Rahul Sharma) exits Main Gate -> Block 9
        ev9, b9 = database.log_gate_event_with_block(
            conn=conn,
            vehicle_id=v6["id"],
            rider_name="Rahul Sharma",
            owner_type="Student",
            campus_id="CS2024-501",
            event_type="EXIT",
            gate_name="Main Gate (Gate 1)",
            operator_id=guard_id,
            notes="Departed campus for evening.",
        )
        print(f"  [+] Logged EXIT for {v6['display_registration']} -> Block #{b9['block_index']} ({b9['block_hash'][:12]}...)")
        print("[SUCCESS] Demo data successfully seeded! Initialized 6 vehicles and 9 verified blocks.")
    else:
        print("[*] Gate events already exist. Skipping gate events seeding.")

    # Check if change requests already exist
    cur.execute("SELECT COUNT(*) AS count FROM vehicle_change_requests")
    requests_exist = cur.fetchone()["count"] > 0

    if not requests_exist:
        print("[+] Seeding Maker-Checker demo change requests...")
        cur.execute("SELECT id FROM vehicles WHERE registration_number = 'KA05XY1234'")
        v6_row = cur.fetchone()
        cur.execute("SELECT id FROM vehicles WHERE registration_number = 'PB65AZ5520'")
        v5_row = cur.fetchone()

        if v6_row:
            # 1. PENDING Change Request for KA05XY1234 (Ready for Admin to review & approve in demo)
            database.create_change_request(
                conn=conn,
                vehicle_id=v6_row["id"],
                requester_id=guard_id,
                proposed_owner_name="Rahul S. Sharma",
                proposed_owner_type="Student",
                proposed_campus_id="CS2024-501",
                proposed_phone="9876543210",
                proposed_make_model="TVS Apache RTR 160 4V (Matte Black)",
                reason="Student presented updated official college ID showing middle initial 'S.' Requested profile sync.",
            )
            print("  [+] Seeded PENDING change request for KA05XY1234 (Rahul Sharma)")

        if v5_row:
            # 2. APPROVED Historical Change Request for PB65AZ5520 (Demonstrates audit trail)
            req2 = database.create_change_request(
                conn=conn,
                vehicle_id=v5_row["id"],
                requester_id=guard_id,
                proposed_owner_name="Arvind Patel",
                proposed_owner_type="Staff",
                proposed_campus_id="ADM-045",
                proposed_phone="9855512345",
                proposed_make_model="Bajaj Pulsar 150 Dtsi (Silver)",
                reason="Staff annual parking permit renewal; updated motorcycle variant details.",
            )
            database.approve_change_request(conn, req2["id"], reviewer_id=admin_id)
            print("  [+] Seeded APPROVED historical change request for PB65AZ5520 (Arvind Patel)")

    conn.close()


if __name__ == "__main__":
    db_target = sys.argv[1] if len(sys.argv) > 1 else None
    seed_demo_data(db_target)
