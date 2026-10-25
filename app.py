"""GateLedger — Campus Bike Entry & Exit Log Using Blockchain
==============================================================
Main Flask application containing routes, filters, error handling,
and lifecycle management.
"""

from __future__ import annotations
import csv
from datetime import datetime, timezone
import io
import os
import sqlite3
from typing import Any, Dict, Optional
from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import auth
import blockchain
from config import Config
import database


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Flask application factory."""
    app = Flask(__name__)

    # Default configuration
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["DATABASE_PATH"] = Config.DATABASE_PATH
    app.config["POW_DIFFICULTY"] = Config.POW_DIFFICULTY
    app.config["APP_TIMEZONE"] = Config.APP_TIMEZONE
    app.config["SESSION_COOKIE_HTTPONLY"] = Config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = Config.SESSION_COOKIE_SAMESITE

    if test_config:
        app.config.update(test_config)

    # Initialize database if needed
    with app.app_context():
        database.init_db(
            db_path=app.config["DATABASE_PATH"],
            difficulty=app.config["POW_DIFFICULTY"],
        )
        # On Vercel, auto-seed realistic demo records if database is fresh
        if Config.IS_VERCEL:
            try:
                import seed
                seed.seed_demo_data(app.config["DATABASE_PATH"])
            except Exception:
                pass

    # Database connection per request lifecycle
    def get_current_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = database.get_db(app.config["DATABASE_PATH"])
        return g.db

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Template filters
    @app.template_filter("format_dt")
    def format_dt(utc_iso_string: Optional[str]) -> str:
        """Format an ISO 8601 UTC timestamp into a human-readable local datetime."""
        if not utc_iso_string:
            return "N/A"
        try:
            tz = Config.get_tz()
            dt_utc = datetime.fromisoformat(utc_iso_string)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(tz)
            return dt_local.strftime("%d %b %Y, %I:%M %p")
        except Exception:
            return str(utc_iso_string)

    @app.template_filter("short_hash")
    def short_hash(hash_str: Optional[str], length: int = 12) -> str:
        """Truncate a cryptographic hash for clean table display."""
        if not hash_str:
            return ""
        if len(hash_str) <= length:
            return hash_str
        half = (length - 3) // 2
        return f"{hash_str[:half + 2]}...{hash_str[-half:]}"

    # Global context processor
    @app.context_processor
    def inject_globals():
        conn = get_current_db()
        current_user = auth.get_current_user(conn)
        pending_requests_count = (
            database.get_pending_requests_count(conn)
            if current_user and current_user["role"] == "admin"
            else 0
        )
        return {
            "current_user": current_user,
            "csrf_token": auth.get_or_create_csrf_token,
            "app_name": "GateLedger",
            "app_timezone": app.config["APP_TIMEZONE"],
            "pending_requests_count": pending_requests_count,
        }

    # CSRF Protection Hook
    @app.before_request
    def check_csrf():
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            # Exclude endpoints if needed (none are exempted for maximum security)
            token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            if not auth.validate_csrf(token):
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                    return jsonify({"error": "Invalid or missing CSRF token."}), 400
                abort(400, description="Invalid or missing CSRF security token.")

    # -------------------------------------------------------------
    # Authentication Routes
    # -------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        conn = get_current_db()
        if "user_id" in session:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = database.get_user_by_username(conn, username)
            if user and check_password_hash(user["password_hash"], password):
                if user["is_active"] != 1:
                    flash("Your account has been deactivated. Contact an administrator.", "danger")
                    return render_template("login.html", username=username)

                auth.login_user(user)
                flash(f"Welcome back, {user['username']}! ({user['role'].upper()})", "success")
                next_page = request.args.get("next")
                if next_page and next_page.startswith("/"):
                    return redirect(next_page)
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password. Please try again.", "danger")
                return render_template("login.html", username=username)

        return render_template("login.html")

    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        auth.logout_user()
        flash("You have been securely logged out.", "info")
        return redirect(url_for("login"))

    # -------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------
    @app.route("/")
    @auth.login_required
    def dashboard():
        conn = get_current_db()
        tz = Config.get_tz()
        stats = database.get_dashboard_metrics(conn, tz)
        recent_events = database.get_recent_events(conn, limit=8)
        return render_template("dashboard.html", stats=stats, recent_events=recent_events)

    # -------------------------------------------------------------
    # Vehicle Gate Entry & Exit Management
    # -------------------------------------------------------------
    @app.route("/events/new", methods=["GET", "POST"])
    @auth.login_required
    def new_event():
        conn = get_current_db()
        prefill_reg = request.args.get("reg", "").strip()
        prefill_type = request.args.get("type", "ENTRY").strip().upper()

        if request.method == "POST":
            event_type = request.form.get("event_type", "ENTRY").strip().upper()
            raw_reg = request.form.get("registration_number", "").strip()
            rider_name = request.form.get("rider_name", "").strip()
            owner_type = request.form.get("owner_type", "Student").strip()
            campus_id = request.form.get("campus_id", "").strip()
            phone = request.form.get("phone", "").strip()
            make_model = request.form.get("make_model", "").strip()
            gate_name = request.form.get("gate_name", "Main Gate (Gate 1)").strip()
            notes = request.form.get("notes", "").strip()

            # Server-side validation
            errors = []
            if not raw_reg:
                errors.append("Vehicle registration number is required.")
            if not rider_name:
                errors.append("Rider name is required.")
            if event_type not in ("ENTRY", "EXIT"):
                errors.append("Event type must be either ENTRY or EXIT.")
            if owner_type not in ("Student", "Staff", "Visitor"):
                errors.append("Rider category must be Student, Staff, or Visitor.")
            if not gate_name:
                errors.append("Gate name is required.")

            try:
                normalized_reg = database.normalize_reg_number(raw_reg)
            except ValueError as ve:
                errors.append(str(ve))
                normalized_reg = None

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "new_event.html",
                    form_data=request.form,
                    prefill_type=event_type,
                    prefill_reg=raw_reg,
                )

            try:
                # 1. Register or update vehicle profile
                vehicle = database.create_or_update_vehicle(
                    conn=conn,
                    registration_number=normalized_reg,
                    owner_name=rider_name,
                    owner_type=owner_type,
                    campus_id=campus_id if campus_id else None,
                    phone=phone if phone else None,
                    make_model=make_model if make_model else None,
                )

                # 2. Record gate event and atomically mine block
                ev, blk = database.log_gate_event_with_block(
                    conn=conn,
                    vehicle_id=vehicle["id"],
                    rider_name=rider_name,
                    owner_type=owner_type,
                    campus_id=campus_id if campus_id else None,
                    event_type=event_type,
                    gate_name=gate_name,
                    operator_id=session["user_id"],
                    notes=notes if notes else None,
                    difficulty=app.config["POW_DIFFICULTY"],
                )

                flash(
                    f"Successfully logged {event_type} for vehicle {vehicle['display_registration']}! "
                    f"Committed to Blockchain Block #{blk['block_index']} (Hash: {blk['block_hash'][:16]}...)",
                    "success",
                )
                return redirect(url_for("event_detail", event_id=ev["id"]))

            except ValueError as ve:
                flash(str(ve), "danger")
                return render_template(
                    "new_event.html",
                    form_data=request.form,
                    prefill_type=event_type,
                    prefill_reg=raw_reg,
                )
            except Exception as ex:
                flash(f"System error processing gate event: {str(ex)}", "danger")
                return render_template(
                    "new_event.html",
                    form_data=request.form,
                    prefill_type=event_type,
                    prefill_reg=raw_reg,
                )

        return render_template(
            "new_event.html",
            prefill_reg=prefill_reg,
            prefill_type=prefill_type,
            form_data={},
        )

    @app.route("/api/vehicle/lookup")
    @auth.login_required
    def api_vehicle_lookup():
        """Look up vehicle details and current status by registration number."""
        reg = request.args.get("reg", "").strip()
        if not reg:
            return jsonify({"found": False, "message": "No registration provided."})

        try:
            conn = get_current_db()
            vehicle = database.get_vehicle_by_reg(conn, reg)
            if vehicle:
                return jsonify({
                    "found": True,
                    "vehicle": {
                        "id": vehicle["id"],
                        "registration_number": vehicle["registration_number"],
                        "display_registration": vehicle["display_registration"],
                        "owner_name": vehicle["owner_name"],
                        "owner_type": vehicle["owner_type"],
                        "campus_id": vehicle["campus_id"] or "",
                        "phone": vehicle["phone"] or "",
                        "make_model": vehicle["make_model"] or "",
                        "current_status": vehicle["current_status"],
                    },
                })
            return jsonify({"found": False, "message": "Vehicle not yet registered."})
        except Exception as e:
            return jsonify({"found": False, "error": str(e)})

    # -------------------------------------------------------------
    # Gate Records & CSV Export
    # -------------------------------------------------------------
    @app.route("/events")
    @auth.login_required
    def event_records():
        conn = get_current_db()
        search = request.args.get("search", "").strip()
        event_type = request.args.get("type", "").strip().upper()
        category = request.args.get("category", "").strip()
        date_from = request.args.get("from", "").strip()
        date_to = request.args.get("to", "").strip()

        # Pagination
        try:
            page = max(1, int(request.args.get("page", 1)))
        except ValueError:
            page = 1
        per_page = 20
        offset = (page - 1) * per_page

        events, total_count = database.get_filtered_events(
            conn=conn,
            search=search,
            event_type=event_type,
            category=category,
            date_from=date_from,
            date_to=date_to,
            limit=per_page,
            offset=offset,
        )

        total_pages = max(1, (total_count + per_page - 1) // per_page)

        return render_template(
            "records.html",
            events=events,
            total_count=total_count,
            page=page,
            total_pages=total_pages,
            search=search,
            event_type=event_type,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )

    @app.route("/events/<int:event_id>")
    @auth.login_required
    def event_detail(event_id: int):
        conn = get_current_db()
        event = database.get_event_detail(conn, event_id)
        if not event:
            abort(404, description="Gate event record not found.")
        return render_template("event_detail.html", event=event)

    @app.route("/events/export/csv")
    @auth.login_required
    def export_csv():
        conn = get_current_db()
        search = request.args.get("search", "").strip()
        event_type = request.args.get("type", "").strip().upper()
        category = request.args.get("category", "").strip()
        date_from = request.args.get("from", "").strip()
        date_to = request.args.get("to", "").strip()

        # Fetch all matching events without pagination limit
        events, total = database.get_filtered_events(
            conn=conn,
            search=search,
            event_type=event_type,
            category=category,
            date_from=date_from,
            date_to=date_to,
            limit=None,
            offset=0,
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Event ID",
            "Registration Number",
            "Rider Name",
            "Rider Category",
            "Campus ID",
            "Event Type",
            "Gate Name",
            "Timestamp (UTC)",
            "Timestamp (Local)",
            "Operator",
            "Blockchain Block Index",
            "Blockchain Block Hash",
            "Notes",
        ])

        tz = Config.get_tz()
        for ev in events:
            try:
                utc_dt = datetime.fromisoformat(ev["event_timestamp_utc"])
                local_str = utc_dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                local_str = ev["event_timestamp_utc"]

            writer.writerow([
                ev["id"],
                ev["registration_number_snapshot"],
                ev["rider_name_snapshot"],
                ev["owner_type_snapshot"],
                ev["campus_id_snapshot"] or "",
                ev["event_type"],
                ev["gate_name"],
                ev["event_timestamp_utc"],
                local_str,
                ev["operator_username"],
                ev["block_index"] if ev["block_index"] is not None else "",
                ev["block_hash"] if ev["block_hash"] is not None else "",
                ev["notes"] or "",
            ])

        timestamp_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"gateledger_records_{timestamp_tag}.csv"

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # -------------------------------------------------------------
    # Vehicle Catalog & History
    # -------------------------------------------------------------
    @app.route("/vehicles")
    @auth.login_required
    def vehicle_list():
        conn = get_current_db()
        search = request.args.get("search", "").strip()
        status_filter = request.args.get("status", "").strip().upper()
        owner_type = request.args.get("category", "").strip()

        vehicles = database.list_all_vehicles(
            conn=conn,
            search=search,
            status_filter=status_filter,
            owner_type=owner_type,
        )
        return render_template(
            "vehicles.html",
            vehicles=vehicles,
            search=search,
            status_filter=status_filter,
            category=owner_type,
        )

    @app.route("/vehicles/new", methods=["GET", "POST"])
    @auth.login_required
    def vehicle_new():
        conn = get_current_db()
        if request.method == "POST":
            raw_reg = request.form.get("registration_number", "").strip()
            owner_name = request.form.get("owner_name", "").strip()
            owner_type = request.form.get("owner_type", "Student").strip()
            campus_id = request.form.get("campus_id", "").strip()
            phone = request.form.get("phone", "").strip()
            make_model = request.form.get("make_model", "").strip()

            if not raw_reg or not owner_name:
                flash("Registration number and Owner name are required.", "danger")
                return render_template("vehicle_detail.html", is_new=True, form_data=request.form)

            try:
                vehicle = database.create_or_update_vehicle(
                    conn=conn,
                    registration_number=raw_reg,
                    owner_name=owner_name,
                    owner_type=owner_type,
                    campus_id=campus_id if campus_id else None,
                    phone=phone if phone else None,
                    make_model=make_model if make_model else None,
                )
                flash(f"Vehicle {vehicle['display_registration']} registered successfully.", "success")
                return redirect(url_for("vehicle_detail_view", vehicle_id=vehicle["id"]))
            except ValueError as ve:
                flash(str(ve), "danger")
                return render_template("vehicle_detail.html", is_new=True, form_data=request.form)

        return render_template("vehicle_detail.html", is_new=True, form_data={})

    @app.route("/vehicles/<int:vehicle_id>")
    @auth.login_required
    def vehicle_detail_view(vehicle_id: int):
        conn = get_current_db()
        vehicle = database.get_vehicle_by_id(conn, vehicle_id)
        if not vehicle:
            abort(404, description="Vehicle not found.")

        history = database.get_vehicle_event_history(conn, vehicle_id)
        change_requests = database.get_change_requests_for_vehicle(conn, vehicle_id)
        return render_template(
            "vehicle_detail.html",
            is_new=False,
            vehicle=vehicle,
            history=history,
            change_requests=change_requests,
        )

    @app.route("/vehicles/<int:vehicle_id>/edit", methods=["POST"])
    @auth.admin_required
    def vehicle_edit(vehicle_id: int):
        """Administrator-only direct vehicle profile update."""
        conn = get_current_db()
        vehicle = database.get_vehicle_by_id(conn, vehicle_id)
        if not vehicle:
            abort(404, description="Vehicle not found.")

        owner_name = request.form.get("owner_name", "").strip()
        owner_type = request.form.get("owner_type", "Student").strip()
        campus_id = request.form.get("campus_id", "").strip()
        phone = request.form.get("phone", "").strip()
        make_model = request.form.get("make_model", "").strip()

        if not owner_name:
            flash("Owner name cannot be empty.", "danger")
            return redirect(url_for("vehicle_detail_view", vehicle_id=vehicle_id))

        try:
            database.create_or_update_vehicle(
                conn=conn,
                registration_number=vehicle["registration_number"],
                owner_name=owner_name,
                owner_type=owner_type,
                campus_id=campus_id if campus_id else None,
                phone=phone if phone else None,
                make_model=make_model if make_model else None,
            )
            flash("Vehicle profile updated successfully by Administrator. Historical event logs remain immutable.", "success")
        except Exception as e:
            flash(f"Error updating vehicle: {str(e)}", "danger")

        return redirect(url_for("vehicle_detail_view", vehicle_id=vehicle_id))

    @app.route("/vehicles/<int:vehicle_id>/request-change", methods=["POST"])
    @auth.login_required
    def vehicle_request_change(vehicle_id: int):
        """Security Guard submission of a profile correction request (Maker-Checker Workflow)."""
        conn = get_current_db()
        vehicle = database.get_vehicle_by_id(conn, vehicle_id)
        if not vehicle:
            abort(404, description="Vehicle not found.")

        proposed_name = request.form.get("proposed_owner_name", "").strip()
        proposed_type = request.form.get("proposed_owner_type", "Student").strip()
        proposed_campus_id = request.form.get("proposed_campus_id", "").strip()
        proposed_phone = request.form.get("proposed_phone", "").strip()
        proposed_make_model = request.form.get("proposed_make_model", "").strip()
        reason = request.form.get("reason", "").strip()

        if not proposed_name or not reason:
            flash("Proposed owner name and a clear reason for the change are required.", "danger")
            return redirect(url_for("vehicle_detail_view", vehicle_id=vehicle_id))

        try:
            req = database.create_change_request(
                conn=conn,
                vehicle_id=vehicle_id,
                requester_id=session["user_id"],
                proposed_owner_name=proposed_name,
                proposed_owner_type=proposed_type,
                proposed_campus_id=proposed_campus_id,
                proposed_phone=proposed_phone,
                proposed_make_model=proposed_make_model,
                reason=reason,
            )
            flash(
                f"Change Request #{req['id']} submitted to Administrator for verification. "
                "The current profile remains unchanged until an Administrator reviews and approves it.",
                "info",
            )
        except Exception as e:
            flash(f"Error submitting change request: {str(e)}", "danger")

        return redirect(url_for("vehicle_detail_view", vehicle_id=vehicle_id))

    @app.route("/admin/requests")
    @auth.admin_required
    def admin_change_requests():
        """Administrator dashboard to inspect, approve, or reject guard profile modification requests."""
        conn = get_current_db()
        status_filter = request.args.get("status", "").strip()
        requests_list = database.list_change_requests(conn, status_filter=status_filter)
        return render_template(
            "admin_requests.html",
            requests=requests_list,
            status_filter=status_filter,
        )

    @app.route("/admin/requests/<int:request_id>/approve", methods=["POST"])
    @auth.admin_required
    def admin_approve_request(request_id: int):
        conn = get_current_db()
        success, msg = database.approve_change_request(conn, request_id, session["user_id"])
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("admin_change_requests"))

    @app.route("/admin/requests/<int:request_id>/reject", methods=["POST"])
    @auth.admin_required
    def admin_reject_request(request_id: int):
        conn = get_current_db()
        notes = request.form.get("review_notes", "").strip()
        success, msg = database.reject_change_request(conn, request_id, session["user_id"], notes)
        if success:
            flash(msg, "warning")
        else:
            flash(msg, "danger")
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("admin_change_requests"))

    # -------------------------------------------------------------
    # Blockchain Explorer & Tamper Simulation
    # -------------------------------------------------------------
    @app.route("/blockchain")
    @auth.login_required
    def blockchain_explorer():
        conn = get_current_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                bb.*,
                ge.registration_number_snapshot,
                ge.event_type,
                ge.rider_name_snapshot
            FROM blockchain_blocks bb
            LEFT JOIN gate_events ge ON bb.event_id = ge.id
            ORDER BY bb.block_index ASC
            """
        )
        blocks = [dict(r) for r in cur.fetchall()]

        # Latest verification result
        verification = blockchain.verify_blockchain(
            conn=conn, difficulty=app.config["POW_DIFFICULTY"]
        )

        return render_template(
            "blockchain.html",
            blocks=blocks,
            total_blocks=len(blocks),
            chain_head_hash=blocks[-1]["block_hash"] if blocks else None,
            difficulty=app.config["POW_DIFFICULTY"],
            verification=verification,
        )

    @app.route("/blockchain/verify", methods=["POST"])
    @auth.login_required
    def verify_chain_route():
        conn = get_current_db()
        verification = blockchain.verify_blockchain(
            conn=conn, difficulty=app.config["POW_DIFFICULTY"]
        )
        if verification["is_valid"]:
            flash(
                f"Blockchain Integrity Verified! All {verification['total_blocks']} blocks are valid, "
                f"sequentially linked, and satisfied Proof-of-Work (Target prefix: {'0' * app.config['POW_DIFFICULTY']}).",
                "success",
            )
        else:
            flash(
                f"Integrity Alert: Chain validation failed at Block #{verification['invalid_block_index']}. "
                f"Reason: {verification['reason']}",
                "danger",
            )
        return redirect(url_for("blockchain_explorer"))

    @app.route("/blockchain/simulate-tamper", methods=["POST"])
    @auth.login_required
    def simulate_tampering_route():
        conn = get_current_db()
        try:
            target_index = request.form.get("block_index")
            blk_idx = int(target_index) if target_index else None
            field = request.form.get("tamper_field", "rider_name")
            value = request.form.get("tamper_value", "UNAUTHORIZED_MODIFICATION_TEST")

            result = blockchain.simulate_tampering(
                conn=conn,
                block_index=blk_idx,
                tamper_field=field,
                tamper_value=value,
                difficulty=app.config["POW_DIFFICULTY"],
            )

            # Store result in session for display on blockchain page
            session["tamper_simulation_result"] = result
            flash("Safe tampering simulation executed on in-memory ledger copy.", "info")
        except Exception as e:
            flash(f"Tamper simulation error: {str(e)}", "danger")

        return redirect(url_for("blockchain_explorer"))

    @app.route("/api/blockchain/block/<int:block_index>")
    @auth.login_required
    def api_block_detail(block_index: int):
        conn = get_current_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                bb.*,
                ge.registration_number_snapshot,
                ge.event_type,
                ge.rider_name_snapshot,
                ge.gate_name
            FROM blockchain_blocks bb
            LEFT JOIN gate_events ge ON bb.event_id = ge.id
            WHERE bb.block_index = ?
            """,
            (block_index,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Block not found."}), 404
        return jsonify(dict(row))

    # -------------------------------------------------------------
    # Administrator User Management
    # -------------------------------------------------------------
    @app.route("/admin/users", methods=["GET"])
    @auth.admin_required
    def admin_users():
        conn = get_current_db()
        users = database.list_users(conn)
        return render_template("admin_users.html", users=users)

    @app.route("/admin/users/new", methods=["POST"])
    @auth.admin_required
    def admin_create_user():
        conn = get_current_db()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "guard").strip().lower()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("admin_users"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("admin_users"))

        if role not in ("admin", "guard"):
            flash("Role must be 'admin' or 'guard'.", "danger")
            return redirect(url_for("admin_users"))

        existing = database.get_user_by_username(conn, username)
        if existing:
            flash(f"User '{username}' already exists.", "danger")
            return redirect(url_for("admin_users"))

        p_hash = generate_password_hash(password)
        database.create_user(conn, username, p_hash, role)
        flash(f"User account '{username}' ({role.upper()}) created successfully.", "success")
        return redirect(url_for("admin_users"))

    @app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
    @auth.admin_required
    def admin_toggle_user(user_id: int):
        conn = get_current_db()
        success, msg = database.toggle_user_active_status(conn, user_id)
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
        return redirect(url_for("admin_users"))

    # -------------------------------------------------------------
    # HTTP Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request_error(e):
        return render_template("errors/400.html", description=e.description), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template("errors/403.html", description=e.description), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template("errors/404.html", description=e.description), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500

    return app


# Default application instance for WSGI servers / 'flask run'
app = create_app()


if __name__ == "__main__":
    # Development server running on 127.0.0.1:5000
    app.run(host="127.0.0.1", port=5000, debug=False)
