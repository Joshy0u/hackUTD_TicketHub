#!/usr/bin/env python3
"""
dc_datacenter_path_api.py

All-in-one Flask service that:

- Connects to your Amazon RDS PostgreSQL instance.
- Ensures the database 'datacenter_db' exists (creates it if needed).
- Ensures schema tables exist.
- Ensures a single fixed-layout datacenter exists (creates if needed).
- Provides APIs for:
    - managing servers
    - listing servers
    - computing shortest paths from door to a server's rack
    - ASCII visualization of the path.

Layout (10x9):

  Row 0: WWWWWWWWWW
  Row 1: WBBWBBWBBW
  Row 2: WBBWBBWBBW
  Row 3: WBBWBBWBBW
  Row 4: WBBWBBWBBW
  Row 5: WBBWBBWBBW
  Row 6: WBBWBBWBBW
  Row 7: WWWWWWWWWW
  Row 8: DWWWWWWWWW

W = free space
B = rack (each B is its own rack, up to 8 servers)
D = door (entry point at x=0,y=8, treated as free)
"""

import os
from heapq import heappush, heappop

from flask import Flask, jsonify, request, Response
import psycopg2

# =========================
# Config
# =========================

# Your RDS endpoint (default), can still be overridden with DB_HOST env var if needed.
DB_HOST = os.environ.get(
    "DB_HOST",
    "database-1.csfc6cuael0m.us-east-1.rds.amazonaws.com"
)
DB_PORT = int(os.environ.get("DB_PORT", "5432"))

# The logical database that this app uses inside the RDS instance
DB_NAME = os.environ.get("DB_NAME", "datacenter_db")

# RDS user credentials (defaults to your provided values)
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "CREDS NO LEAK")

# Door (entry) coordinates in our fixed layout
ENTRY_X = 0
ENTRY_Y = 8

app = Flask(__name__)


# =========================
# DB helpers
# =========================

def get_conn():
    """Connect to the application database (datacenter_db)."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def ensure_database_exists():
    """
    Ensure the logical database DB_NAME exists on the RDS instance.
    Connects to the maintenance 'postgres' DB, creates DB_NAME if needed.

    IMPORTANT: CREATE DATABASE must run outside a transaction,
    so we use autocommit and DO NOT wrap this in "with conn:".
    """
    maintenance_db = "postgres"
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=maintenance_db,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
            exists = cur.fetchone()
            if not exists:
                cur.execute(f'CREATE DATABASE "{DB_NAME}";')
    finally:
        conn.close()


def init_schema():
    """Create schema tables if they don't exist in DB_NAME."""
    ddl_statements = [

        # Datacenter
        """
        CREATE TABLE IF NOT EXISTS datacenter (
            datacenter_id   SERIAL PRIMARY KEY,
            name            VARCHAR(100) NOT NULL
        );
        """,

        # Aisle
        """
        CREATE TABLE IF NOT EXISTS aisle (
            aisle_id        SERIAL PRIMARY KEY,
            datacenter_id   INTEGER NOT NULL,
            label           VARCHAR(20) NOT NULL,
            CONSTRAINT fk_aisle_datacenter
                FOREIGN KEY (datacenter_id)
                REFERENCES datacenter(datacenter_id)
                ON DELETE CASCADE,
            CONSTRAINT uq_aisle_label_per_dc
                UNIQUE (datacenter_id, label)
        );
        """,

        # Rack: each B is one rack, up to 8 servers.
        """
        CREATE TABLE IF NOT EXISTS rack (
            rack_id         SERIAL PRIMARY KEY,
            aisle_id        INTEGER NOT NULL,
            label           VARCHAR(20) NOT NULL,
            max_servers     INTEGER NOT NULL DEFAULT 8,
            CONSTRAINT fk_rack_aisle
                FOREIGN KEY (aisle_id)
                REFERENCES aisle(aisle_id)
                ON DELETE CASCADE,
            CONSTRAINT uq_rack_label_per_aisle
                UNIQUE (aisle_id, label)
        );
        """,

        # Server: each server has a rack + slot 1..8 (location within rack)
        """
        CREATE TABLE IF NOT EXISTS server (
            server_id       SERIAL PRIMARY KEY,
            rack_id         INTEGER NOT NULL,
            hostname        VARCHAR(100) NOT NULL UNIQUE,
            serial_number   VARCHAR(100) NOT NULL UNIQUE,
            slot            INTEGER NOT NULL,
            CONSTRAINT fk_server_rack
                FOREIGN KEY (rack_id)
                REFERENCES rack(rack_id)
                ON DELETE CASCADE,
            CONSTRAINT uq_server_rack_slot UNIQUE (rack_id, slot),
            CONSTRAINT chk_server_slot_range CHECK (slot BETWEEN 1 AND 8)
        );
        """,

        # Grid cells (FREE vs RACK only)
        """
        CREATE TABLE IF NOT EXISTS datacenter_cell (
            cell_id       SERIAL PRIMARY KEY,
            datacenter_id INTEGER NOT NULL,
            x             INTEGER NOT NULL,
            y             INTEGER NOT NULL,
            is_rack       BOOLEAN NOT NULL DEFAULT FALSE,
            rack_id       INTEGER,
            CONSTRAINT fk_cell_datacenter
                FOREIGN KEY (datacenter_id)
                REFERENCES datacenter(datacenter_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_cell_rack
                FOREIGN KEY (rack_id)
                REFERENCES rack(rack_id)
                ON DELETE SET NULL,
            CONSTRAINT uq_cell_coord UNIQUE (datacenter_id, x, y)
        );
        """
    ]

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                for ddl in ddl_statements:
                    cur.execute(ddl)
    finally:
        conn.close()


def ensure_datacenter_exists():
    """
    Ensure exactly one datacenter/layout exists.
    - If a datacenter already exists, return its info.
    - If none exists, create our fixed layout and return its info.

    Returns dict:
    {
      "datacenter_id": ...,
      "entry": {"x": ..., "y": ...},
      "rack_count": ...,
      "created": True/False
    }
    """
    global ENTRY_X, ENTRY_Y

    ensure_database_exists()
    init_schema()

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # Check if a datacenter already exists
                cur.execute("SELECT datacenter_id FROM datacenter LIMIT 1;")
                row = cur.fetchone()
                if row:
                    dc_id = row[0]

                    # Load door coords if present (we know layout uses 0,8)
                    cur.execute(
                        """
                        SELECT x, y FROM datacenter_cell
                        WHERE datacenter_id = %s
                          AND x = %s AND y = %s
                        LIMIT 1;
                        """,
                        (dc_id, ENTRY_X, ENTRY_Y)
                    )
                    entry = cur.fetchone()
                    if entry:
                        ENTRY_X, ENTRY_Y = entry

                    # Count racks for this datacenter
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM rack r
                        JOIN aisle a ON a.aisle_id = r.aisle_id
                        WHERE a.datacenter_id = %s;
                        """,
                        (dc_id,)
                    )
                    (rack_count,) = cur.fetchone()

                    return {
                        "datacenter_id": dc_id,
                        "entry": {"x": ENTRY_X, "y": ENTRY_Y},
                        "rack_count": rack_count,
                        "created": False,
                    }

                # Otherwise, create it fresh
                cur.execute(
                    "INSERT INTO datacenter (name) VALUES (%s) RETURNING datacenter_id;",
                    ("DC-FIXED",)
                )
                dc_id = cur.fetchone()[0]

                cur.execute(
                    "INSERT INTO aisle (datacenter_id, label) VALUES (%s, %s) RETURNING aisle_id;",
                    (dc_id, "A1")
                )
                aisle_id = cur.fetchone()[0]

                layout = [
                    "WWWWWWWWWW",  # y = 0
                    "WBBWBBWBBW",  # y = 1
                    "WBBWBBWBBW",  # y = 2
                    "WBBWBBWBBW",  # y = 3
                    "WBBWBBWBBW",  # y = 4
                    "WBBWBBWBBW",  # y = 5
                    "WBBWBBWBBW",  # y = 6
                    "WWWWWWWWWW",  # y = 7
                    "DWWWWWWWWW",  # y = 8
                ]

                rack_count = 0

                for y, row_layout in enumerate(layout):
                    for x, cell in enumerate(row_layout):
                        if cell == "B":
                            rack_count += 1
                            label = f"R{rack_count}"
                            cur.execute(
                                """
                                INSERT INTO rack (aisle_id, label, max_servers)
                                VALUES (%s, %s, %s)
                                RETURNING rack_id;
                                """,
                                (aisle_id, label, 8)
                            )
                            rack_id = cur.fetchone()[0]

                            cur.execute(
                                """
                                INSERT INTO datacenter_cell (datacenter_id, x, y, is_rack, rack_id)
                                VALUES (%s, %s, %s, TRUE, %s);
                                """,
                                (dc_id, x, y, rack_id)
                            )

                        elif cell == "W":
                            cur.execute(
                                """
                                INSERT INTO datacenter_cell (datacenter_id, x, y, is_rack)
                                VALUES (%s, %s, %s, FALSE);
                                """,
                                (dc_id, x, y)
                            )

                        elif cell == "D":
                            cur.execute(
                                """
                                INSERT INTO datacenter_cell (datacenter_id, x, y, is_rack)
                                VALUES (%s, %s, %s, FALSE);
                                """,
                                (dc_id, x, y)
                            )
                            ENTRY_X, ENTRY_Y = x, y

                return {
                    "datacenter_id": dc_id,
                    "entry": {"x": ENTRY_X, "y": ENTRY_Y},
                    "rack_count": rack_count,
                    "created": True,
                }

    finally:
        conn.close()


# =========================
# Pathfinding (A*)
# =========================

def neighbors(x, y):
    """4-directional neighbors."""
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        yield x + dx, y + dy


def heuristic(a, b):
    """Manhattan distance."""
    (x1, y1), (x2, y2) = a, b
    return abs(x1 - x2) + abs(y1 - y2)


def astar(start, goal, grid):
    """
    A* over a dict grid: (x,y) -> 0 (free) or 1 (blocked).
    start, goal are (x, y).
    Returns list of (x, y) or None.
    """
    if start not in grid or goal not in grid:
        return None
    if grid[start] == 1 or grid[goal] == 1:
        return None

    open_set = []
    heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))

        # Explore neighbors
        for nx, ny in neighbors(*current):
            neighbor = (nx, ny)
            if neighbor not in grid:
                continue
            if grid[neighbor] == 1:  # blocked (rack)
                continue

            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                heappush(open_set, (f, neighbor))

    return None


# =========================
# Data helpers
# =========================

def load_grid(conn, datacenter_id):
    """Return dict: (x,y) -> 0 (free) or 1 (rack)."""
    grid = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT x, y, is_rack
            FROM datacenter_cell
            WHERE datacenter_id = %s;
            """,
            (datacenter_id,)
        )
        for x, y, is_rack in cur.fetchall():
            grid[(x, y)] = 1 if is_rack else 0
    return grid


def find_goal_cell_for_server(conn, server_id):
    """
    Given server_id, find:
    - datacenter_id
    - a FREE cell adjacent to that server's rack cells
    Returns (datacenter_id, (goal_x, goal_y)) or None.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.rack_id, a.datacenter_id
            FROM server s
            JOIN rack r ON r.rack_id = s.rack_id
            JOIN aisle a ON a.aisle_id = r.aisle_id
            WHERE s.server_id = %s;
            """,
            (server_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        rack_id, datacenter_id = row

        cur.execute(
            """
            SELECT x, y
            FROM datacenter_cell
            WHERE datacenter_id = %s
              AND rack_id = %s
              AND is_rack = TRUE;
            """,
            (datacenter_id, rack_id)
        )
        rack_cells = cur.fetchall()
        if not rack_cells:
            return None

        cur.execute(
            """
            SELECT DISTINCT c2.x, c2.y
            FROM datacenter_cell r
            JOIN datacenter_cell c2
              ON c2.datacenter_id = r.datacenter_id
             AND c2.is_rack = FALSE
             AND (
                    (c2.x = r.x + 1 AND c2.y = r.y)
                 OR (c2.x = r.x - 1 AND c2.y = r.y)
                 OR (c2.x = r.x AND c2.y = r.y + 1)
                 OR (c2.x = r.x AND c2.y = r.y - 1)
                 )
            WHERE r.datacenter_id = %s
              AND r.rack_id = %s
              AND r.is_rack = TRUE
            LIMIT 1;
            """,
            (datacenter_id, rack_id)
        )
        adj = cur.fetchone()
        if not adj:
            return None

        goal_x, goal_y = adj
        return datacenter_id, (goal_x, goal_y)


def create_server_with_location(conn, rack_id, hostname, serial_number, slot=None):
    """
    Create a server in a rack, enforcing:
    - rack exists
    - hostname & serial are unique
    - slot in [1..max_servers] and not already used
    If slot is None, assign the first free slot.
    Returns (server_id, assigned_slot).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT max_servers FROM rack WHERE rack_id = %s;",
            (rack_id,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Rack {rack_id} does not exist.")
        (max_servers,) = row

        cur.execute(
            """
            SELECT 1
            FROM server
            WHERE hostname = %s OR serial_number = %s;
            """,
            (hostname, serial_number)
        )
        if cur.fetchone():
            raise ValueError("Hostname or serial_number already in use.")

        cur.execute(
            "SELECT slot FROM server WHERE rack_id = %s ORDER BY slot;",
            (rack_id,)
        )
        used_slots = [r[0] for r in cur.fetchall()]

        if slot is None:
            assigned_slot = None
            for s in range(1, max_servers + 1):
                if s not in used_slots:
                    assigned_slot = s
                    break
            if assigned_slot is None:
                raise ValueError(f"Rack {rack_id} is full.")
        else:
            if slot < 1 or slot > max_servers:
                raise ValueError(f"Slot must be between 1 and {max_servers}.")
            if slot in used_slots:
                raise ValueError(f"Slot {slot} is already occupied on rack {rack_id}.")
            assigned_slot = slot

        cur.execute(
            """
            INSERT INTO server (rack_id, hostname, serial_number, slot)
            VALUES (%s, %s, %s, %s)
            RETURNING server_id;
            """,
            (rack_id, hostname, serial_number, assigned_slot)
        )
        (server_id,) = cur.fetchone()
        return server_id, assigned_slot


# =========================
# Routes
# =========================

@app.route("/init_datacenter", methods=["POST"])
def init_datacenter():
    """
    Ensure datacenter layout exists, return its info.
    Safe to call multiple times; only one DC will ever be created.
    """
    info = ensure_datacenter_exists()
    return jsonify({
        "status": "ok",
        "message": "Datacenter created" if info["created"] else "Datacenter already exists",
        "datacenter_id": info["datacenter_id"],
        "entry": info["entry"],
        "rack_count": info["rack_count"],
    })


@app.route("/servers", methods=["POST"])
def add_server():
    """
    Add a server to a rack.

    JSON body:
    {
      "rack_id": 123,
      "hostname": "web-01",
      "serial_number": "SN-ABC-123",
      "slot": 3   # optional; if omitted, first free slot 1..8 is used
    }
    """
    ensure_datacenter_exists()

    data = request.get_json(force=True) or {}
    rack_id = data.get("rack_id")
    hostname = data.get("hostname")
    serial_number = data.get("serial_number")
    slot = data.get("slot")

    if rack_id is None or not hostname or not serial_number:
        return jsonify({
            "status": "error",
            "message": "rack_id, hostname, and serial_number are required"
        }), 400

    conn = get_conn()
    try:
        with conn:
            try:
                server_id, assigned_slot = create_server_with_location(
                    conn, rack_id, hostname, serial_number, slot
                )
            except ValueError as e:
                return jsonify({"status": "error", "message": str(e)}), 400

        return jsonify({
            "status": "ok",
            "server_id": server_id,
            "rack_id": rack_id,
            "hostname": hostname,
            "serial_number": serial_number,
            "slot": assigned_slot
        })

    finally:
        conn.close()


@app.route("/servers/<hostname>", methods=["DELETE"])
def delete_server(hostname):
    """
    Delete a server by hostname.

    Assumes hostname is globally unique.
    """
    ensure_datacenter_exists()

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM server
                    WHERE hostname = %s
                    RETURNING server_id, rack_id, slot;
                    """,
                    (hostname,)
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({
                        "status": "error",
                        "message": f"No server found with hostname '{hostname}'"
                    }), 404

                server_id, rack_id, slot = row

        return jsonify({
            "status": "ok",
            "message": "Server deleted",
            "server_id": server_id,
            "rack_id": rack_id,
            "hostname": hostname,
            "slot": slot
        })

    finally:
        conn.close()


@app.route("/servers/list", methods=["GET"])
def list_servers():
    """
    List all servers currently on racks in the (single) datacenter.
    """
    ensure_datacenter_exists()

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        s.server_id,
                        s.hostname,
                        s.serial_number,
                        s.slot,
                        r.rack_id,
                        r.label AS rack_label,
                        a.aisle_id,
                        a.label AS aisle_label,
                        d.datacenter_id,
                        d.name AS datacenter_name
                    FROM server s
                    JOIN rack r ON r.rack_id = s.rack_id
                    JOIN aisle a ON a.aisle_id = r.aisle_id
                    JOIN datacenter d ON d.datacenter_id = a.datacenter_id
                    ORDER BY d.datacenter_id, a.aisle_id, r.rack_id, s.slot;
                    """
                )
                rows = cur.fetchall()

        servers = []
        for (
            server_id,
            hostname,
            serial_number,
            slot,
            rack_id,
            rack_label,
            aisle_id,
            aisle_label,
            dc_id,
            dc_name,
        ) in rows:
            servers.append({
                "server_id": server_id,
                "hostname": hostname,
                "serial_number": serial_number,
                "slot": slot,
                "rack": {
                    "id": rack_id,
                    "label": rack_label,
                },
                "aisle": {
                    "id": aisle_id,
                    "label": aisle_label,
                },
                "datacenter": {
                    "id": dc_id,
                    "name": dc_name,
                },
            })

        return jsonify({
            "status": "ok",
            "servers": servers
        })

    finally:
        conn.close()


@app.route("/path/<int:server_id>", methods=["GET"])
def get_path(server_id):
    """
    Compute shortest path from the door (D) to a given server's rack (by server_id).
    Returns JSON with start, goal, and path coordinates.
    """
    info = ensure_datacenter_exists()
    datacenter_id = info["datacenter_id"]

    conn = get_conn()
    try:
        with conn:
            goal_info = find_goal_cell_for_server(conn, server_id)
            if not goal_info:
                return jsonify({
                    "status": "error",
                    "message": "Could not find datacenter/rack cells for this server_id"
                }), 404

            dc_id_for_server, (goal_x, goal_y) = goal_info
            if dc_id_for_server != datacenter_id:
                return jsonify({
                    "status": "error",
                    "message": "Server belongs to a different datacenter (unexpected)"
                }), 400

            grid = load_grid(conn, datacenter_id)

        start = (ENTRY_X, ENTRY_Y)
        goal = (goal_x, goal_y)

        path = astar(start, goal, grid)
        if path is None:
            return jsonify({
                "status": "error",
                "message": "No path found",
                "datacenter_id": datacenter_id,
                "start": {"x": start[0], "y": start[1]},
                "goal": {"x": goal[0], "y": goal[1]}
            }), 400

        path_list = [{"x": x, "y": y} for (x, y) in path]

        return jsonify({
            "status": "ok",
            "server_id": server_id,
            "datacenter_id": datacenter_id,
            "start": {"x": start[0], "y": start[1]},
            "goal": {"x": goal[0], "y": goal[1]},
            "path": path_list
        })

    finally:
        conn.close()


@app.route("/path/hostname/<hostname>", methods=["GET"])
def get_path_by_hostname(hostname):
    """
    Compute path from the door (D) to a given server's rack by hostname.
    """
    ensure_datacenter_exists()
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT server_id FROM server WHERE hostname = %s;", (hostname,))
                row = cur.fetchone()
                if not row:
                    return jsonify({
                        "status": "error",
                        "message": f"No server found with hostname '{hostname}'"
                    }), 404
                (server_id,) = row
    finally:
        conn.close()

    return get_path(server_id)


@app.route("/visualize/<int:server_id>", methods=["GET"])
def visualize(server_id):
    """
    ASCII visualization of the datacenter grid with path to the given server.

    Legend:
      D = Door (start)
      B = Rack cell
      W = Free cell
      * = Path (free cells on path)
      G = Goal (free cell adjacent to server's rack)
    """
    info = ensure_datacenter_exists()
    datacenter_id = info["datacenter_id"]

    conn = get_conn()
    try:
        with conn:
            goal_info = find_goal_cell_for_server(conn, server_id)
            if not goal_info:
                return Response(
                    f"Error: could not find datacenter/rack cells for server_id={server_id}\n",
                    mimetype="text/plain",
                    status=404
                )

            dc_id_for_server, (goal_x, goal_y) = goal_info
            if dc_id_for_server != datacenter_id:
                return Response(
                    "Error: server belongs to a different datacenter (unexpected)\n",
                    mimetype="text/plain",
                    status=400
                )

            grid = load_grid(conn, datacenter_id)

        start = (ENTRY_X, ENTRY_Y)
        goal = (goal_x, goal_y)

        path = astar(start, goal, grid)
        path_set = set(path) if path else set()

        xs = [x for (x, _) in grid.keys()]
        ys = [y for (_, y) in grid.keys()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        lines = []
        for y in range(min_y, max_y + 1):
            row_chars = []
            for x in range(min_x, max_x + 1):
                pos = (x, y)
                is_rack = (grid.get(pos, 1) == 1)

                if pos == (ENTRY_X, ENTRY_Y):
                    ch = "D"
                elif pos == (goal_x, goal_y):
                    ch = "G"
                elif pos in path_set and not is_rack:
                    ch = "*"
                elif is_rack:
                    ch = "B"
                else:
                    ch = "W"

                row_chars.append(ch)
            lines.append(" ".join(row_chars))

        ascii_map = "\n".join(lines) + "\n"
        return Response(ascii_map, mimetype="text/plain")

    finally:
        conn.close()


@app.route("/visualize/hostname/<hostname>", methods=["GET"])
def visualize_by_hostname(hostname):
    """
    ASCII visualization of path to server, by hostname instead of ID.
    """
    ensure_datacenter_exists()
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT server_id FROM server WHERE hostname = %s;", (hostname,))
                row = cur.fetchone()
                if not row:
                    return Response(
                        f"Error: no server found with hostname '{hostname}'\n",
                        mimetype="text/plain",
                        status=404
                    )
                (server_id,) = row
    finally:
        conn.close()

    return visualize(server_id)


@app.route("/health", methods=["GET"])
def health():
    """
    Simple health check: verifies DB connection and datacenter existence.
    """
    try:
        info = ensure_datacenter_exists()
        return jsonify({
            "status": "ok",
            "datacenter_id": info["datacenter_id"],
            "entry": info["entry"],
            "racks": info["rack_count"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# Main
# =========================

if __name__ == "__main__":
    # Auto-init the database + datacenter ON STARTUP (idempotent)
    try:
        info = ensure_datacenter_exists()
        print(
            f"Datacenter ready. id={info['datacenter_id']}, "
            f"entry={info['entry']}, racks={info['rack_count']}, "
            f"created={info['created']}"
        )
    except Exception as e:
        print(f"Failed to ensure datacenter exists at startup: {e}")

    # Bind to 0.0.0.0 so it’s reachable on EC2; default port 8000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
