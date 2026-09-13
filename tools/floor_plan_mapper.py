#!/usr/bin/env python3
"""
Syntropic Sense — Floor Plan to Fixed Node Coordinates Tool

Allows technicians and family caregivers to describe room dimensions and node placement
in plain language (e.g. "bedroom is 4x3 meters, node 1 on south wall center, node 2 in NE corner")
and generates the exact `--node-positions` argument for Point 3 of the deployment sequence.

Usage:
  python3 tools/floor_plan_mapper.py interactive
  python3 tools/floor_plan_mapper.py --rooms layout.json
  python3 tools/floor_plan_mapper.py --quick "living_room:5x4:n1=south-center,n2=north-east;bedroom:4x3:n3=west-center"
"""

import sys
import json
import argparse

WALL_POSITIONS = {
    # Wall midpoints and corners (normalized 0.0 to 1.0 in x, y)
    "south-west": (0.0, 0.0),
    "sw": (0.0, 0.0),
    "south-center": (0.5, 0.0),
    "sc": (0.5, 0.0),
    "south": (0.5, 0.0),
    "south-east": (1.0, 0.0),
    "se": (1.0, 0.0),
    "east-center": (1.0, 0.5),
    "ec": (1.0, 0.5),
    "east": (1.0, 0.5),
    "north-east": (1.0, 1.0),
    "ne": (1.0, 1.0),
    "north-center": (0.5, 1.0),
    "nc": (0.5, 1.0),
    "north": (0.5, 1.0),
    "north-west": (0.0, 1.0),
    "nw": (0.0, 1.0),
    "west-center": (0.0, 0.5),
    "wc": (0.0, 0.5),
    "west": (0.0, 0.5),
    "center": (0.5, 0.5),
}

DEFAULT_MOUNT_HEIGHT = 1.2  # meters (chest height)

def parse_relative_wall(pos_name: str, width: float, length: float, height: float = DEFAULT_MOUNT_HEIGHT):
    key = pos_name.strip().lower().replace("_", "-")
    if key not in WALL_POSITIONS:
        # Check if direct offset like "north+1.2" or fallback to center
        print(f"  [Warning] Unknown position '{pos_name}', defaulting to 'center'", file=sys.stderr)
        key = "center"
    
    norm_x, norm_y = WALL_POSITIONS[key]
    return round(norm_x * width, 2), round(norm_y * length, 2), height

def parse_quick_string(layout_str: str):
    """
    Format:
    "room_name:WxL[:offset_x,offset_y]:node_id=pos,node_id=pos;..."
    """
    nodes = {}
    rooms = [r.strip() for r in layout_str.split(";") if r.strip()]
    
    room_origin_x = 0.0
    for r in rooms:
        parts = r.split(":")
        if len(parts) < 3:
            continue
        room_name = parts[0]
        dim_str = parts[1]
        try:
            w, l = [float(d) for d in dim_str.lower().split("x")]
        except ValueError:
            print(f"Error parsing dimensions '{dim_str}', use format WxL e.g. 4x3", file=sys.stderr)
            continue
        
        node_parts = parts[2:]
        for np in node_parts:
            # e.g. "1=south-center,2=north-east"
            for item in np.split(","):
                if "=" in item:
                    nid_str, pos = item.split("=", 1)
                    nid = nid_str.lower().replace("n", "").replace("node", "").strip()
                    rx, ry, rz = parse_relative_wall(pos, w, l)
                    # Global coordinate relative to home origin
                    gx = round(room_origin_x + rx, 2)
                    gy = round(ry, 2)
                    nodes[nid] = (gx, gy, rz, room_name, pos)
        
        # Advance room origin along X axis for consecutive rooms
        room_origin_x += w + 0.2  # +20cm wall thickness
        
    return nodes

def format_output(nodes: dict):
    if not nodes:
        return "No nodes configured."
    
    # Format: "node_id:x,y,z;node_id:x,y,z;..."
    items = []
    summary_lines = []
    for nid in sorted(nodes.keys(), key=lambda k: int(k) if k.isdigit() else k):
        x, y, z, rname, rpos = nodes[nid]
        items.append(f"{nid}:{x:.2f},{y:.2f},{z:.2f}")
        summary_lines.append(f"  • Node {nid} ({rname} - {rpos}): x={x:.2f}m, y={y:.2f}m, z={z:.2f}m")
    
    arg_value = ";".join(items)
    
    out = [
        "=================================================================",
        " Syntropic Sense — Generated Node Placement Coordinates",
        "=================================================================",
        "\nHuman Room Layout Summary:",
        "\n".join(summary_lines),
        "\n-----------------------------------------------------------------",
        "1. Direct CLI Flag:",
        f'  --node-positions "{arg_value}"',
        "\n2. Docker / Environment Variable (/opt/hub/docker/.env):",
        f'  NODE_POSITIONS="{arg_value}"',
        "\n3. Full Sensing Server Command:",
        f'  cargo run --release -p wifi-densepose-sensing-server -- \\',
        f'    --source esp32 \\',
        f'    --node-positions "{arg_value}" \\',
        f'    --calibrate',
        "================================================================="
    ]
    return "\n".join(out)

def interactive_wizard():
    print("\n--- Syntropic Sense: In-Home Floor Plan Setup Wizard ---")
    print("Answer a few quick questions to map your nodes to room coordinates.\n")
    
    nodes = {}
    try:
        num_rooms_str = input("How many rooms are you monitoring? [Default: 2]: ").strip()
        num_rooms = int(num_rooms_str) if num_rooms_str else 2
    except ValueError:
        num_rooms = 2

    global_x_offset = 0.0
    for r in range(num_rooms):
        print(f"\n--- Room {r+1} ---")
        room_name = input(f"Room name (e.g. Bedroom, Living Room, Hallway) [Room {r+1}]: ").strip() or f"Room {r+1}"
        
        dim_input = input(f"Room dimensions Width x Length in meters (e.g. 4x3.5) [4x3]: ").strip() or "4x3"
        try:
            w, l = [float(v) for v in dim_input.lower().split("x")]
        except Exception:
            w, l = 4.0, 3.0
            print("  Defaulted to 4.0m x 3.0m")
        
        nodes_in_room_str = input(f"How many ESP32 nodes are in {room_name}? [Default: 1]: ").strip()
        nodes_in_room = int(nodes_in_room_str) if nodes_in_room_str else 1
        
        for n in range(nodes_in_room):
            nid = input(f"  Node ID (e.g. 1, 2, 3) [{len(nodes)+1}]: ").strip() or str(len(nodes)+1)
            print("  Placement options: south-center, north-center, west-center, east-center,")
            print("                     south-west, south-east, north-west, north-east, center")
            pos_prompt = input(f"  Where on the wall is Node {nid} mounted? [south-center]: ").strip() or "south-center"
            
            rx, ry, rz = parse_relative_wall(pos_prompt, w, l)
            gx = round(global_x_offset + rx, 2)
            gy = round(ry, 2)
            nodes[nid] = (gx, gy, rz, room_name, pos_prompt)
        
        global_x_offset += w + 0.2
        
    print("\n" + format_output(nodes))

def main():
    parser = argparse.ArgumentParser(description="Map human room dimensions to Syntropic Sense --node-positions coordinates.")
    parser.add_argument("mode", nargs="?", default="interactive", choices=["interactive", "quick"],
                        help="Run interactive wizard or quick parser")
    parser.add_argument("--quick", type=str, help="Quick layout string (e.g. 'bedroom:4x3:n1=south-center;living_room:5x4:n2=north-east,n3=west-center')")
    parser.add_argument("--json-out", action="store_true", help="Output raw JSON instead of formatted text")

    args = parser.parse_args()

    if args.quick:
        nodes = parse_quick_string(args.quick)
        if args.json_out:
            print(json.dumps({k: {"x": v[0], "y": v[1], "z": v[2], "room": v[3], "wall": v[4]} for k, v in nodes.items()}, indent=2))
        else:
            print(format_output(nodes))
    else:
        interactive_wizard()

if __name__ == "__main__":
    main()
