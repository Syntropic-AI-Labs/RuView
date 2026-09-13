# Syntropic Sense — In-Home Deployment & Field Calibration Guide

This document outlines the standard operating procedure (SOP) for deploying and calibrating the **Syntropic Sense** ambient RF sensing system in a resident's home. 

Following this sequence ensures reliable fall detection, gait stability analysis, and wandering monitoring while minimizing false positives and signal jitter.

---

## 1. Pre-Deployment Site Survey & Node Placement

Ambient RF sensing measures how physical bodies disturb 2.4 GHz radio waves. Proper geometry is essential.

### 1.1 Placement Architecture (Minimum 3-Node Mesh)
Deploy at least 3 nodes to establish multi-angle geometric coverage:

```
        [Node 1: Bedroom]
               |
               | (RF Link: Bed Exit & Sleep Restlessness)
               v
        [Node 2: Hallway / Exit Door]
               |
               | (RF Link: Transit Cadence & Night Wandering)
               v
        [Node 3: Living Room / Bathroom Approach]
```

### 1.2 Placement Rules
- **Height**: Mount 1.2 m to 1.5 m (4 to 5 ft) above floor level (chest/torso height).
- **Line of Sight**: Avoid placing nodes directly behind large metallic obstructions (refrigerators, metal cabinets, mirrors) or within 1 meter of microwaves.
- **Orientation**: Point the antenna broadside into the open room volume, not flat against concrete or metal studs.
- **Dedicated RF Channel**: Fix all nodes and the home 2.4 GHz network to an uncongested channel (preferably **Channel 1, 6, or 11** in `menuconfig`) to eliminate frequency-hopping jitter.

---

## 2. In-Home Hub Setup & Verification

1. **Power on the Hub** (Mini PC connected to the local home router via Ethernet or 5 GHz Wi-Fi).
2. **Verify Container & Port Health**:
   ```bash
   # Check that the hub is receiving UDP packets from nodes on port 5005
   sudo tcpdump -i any -n udp port 5005 -c 10
   ```
3. **Verify Node Heartbeats**:
   ```bash
   curl http://localhost:3000/api/health
   ```
   Confirm all deployed nodes show as `active` with `last_packet_age_ms < 150`.

---

## 3. The Calibration Sequence (Required Before Live Use)

Calibration establishes the stationary background matrix so static furniture, walls, and structural reflections are subtracted from dynamic human motion.

### Step 3.1: Empty-Room Static Calibration (`empty_baseline`)
*Crucial: The room must be completely unoccupied during this step.*

1. Ensure all residents and pets leave the monitored zones.
2. Close moving curtains/blinds and turn off oscillating fans.
3. Trigger background calibration via the CLI or server flag:
   ```bash
   # Via Sensing Server automatic boot calibration:
   cargo run --release -p wifi-densepose-sensing-server -- \
     --source esp32 \
     --calibrate \
     --tick-ms 50
   ```
   *Or via the dedicated calibration utility*:
   ```bash
   cd v2
   cargo run --release -p wifi-densepose-cli -- calibrate \
     --duration-s 30 \
     --output /opt/hub/data/calibration/empty_room.json
   ```
4. **Verification**: Confirm that the average CSI variance drops below `0.02` when the room is empty.

---

### Step 3.2: Room Coordinate Mapping (`node-positions`)
To eliminate coordinate jumping and spatial jitter, establish fixed node coordinates. You do not need to calculate Cartesian coordinates manually; use the included **Floor Plan Mapper tool**:

```bash
# Run the interactive setup wizard:
python3 tools/floor_plan_mapper.py

# Or generate coordinates from a quick layout string:
python3 tools/floor_plan_mapper.py --quick "bedroom:4x3:n1=south-center,n2=north-east;hallway:5x2:n3=east-center"
```

The tool asks for plain-language dimensions (e.g. `Bedroom: 4x3 meters`) and wall positions (e.g. `south-center`, `north-east`), and generates the exact `--node-positions` string to paste into `/opt/hub/docker/.env`:

```bash
NODE_POSITIONS="1:2.00,0.00,1.20;2:4.00,3.00,1.20;3:9.20,1.00,1.20"
```

---

### Step 3.3: Guided Care Anchor Enrollment (Optional High-Accuracy Pass)
For high-risk residents requiring precision fall and vitals monitoring, capture guided posture anchors using the CLI enrollment wizard:

```bash
cd v2
cargo run --release -p wifi-densepose-cli -- room enroll \
  --room "Resident Bedroom" \
  --output /opt/hub/data/calibration/resident_bedroom_anchors.json
```

Follow the interactive prompts:
| Anchor | Duration | Action | What It Calibrates |
|---|---|---|---|
| `empty` | 20s | Room vacant | Static noise floor ($Z < 1.0$) |
| `stand_still` | 20s | Subject stands in center | Upright posture phase profile |
| `sit` | 20s | Subject sits on chair/bed | Mid-level dwell reflection |
| `lie_down` | 20s | Subject lies down on bed | Sleeping posture baseline |
| `breathe_normal` | 30s | Subject resting calmly | Respiration subcarrier filter |
| `small_move` | 20s | Subject gentle pacing | Low-cadence gait signatures |

Train the local room specialist model:
```bash
cargo run --release -p wifi-densepose-cli -- room train \
  --input /opt/hub/data/calibration/resident_bedroom_anchors.json \
  --output /opt/hub/data/models/bedroom_specialist.rvf
```

---

## 4. Caregiver Safety Policy Configuration

Tune safety thresholds in `/opt/hub/docker/.env` based on the resident's specific mobility profile:

```ini
# -------------------------------------------------------------
# Syntropic Sense Safety Rules & Dementia Monitoring Policy
# -------------------------------------------------------------

# Bathroom Linger Alert:
# Warns caregiver if continuous presence in bathroom exceeds this limit
BATHROOM_MAX_MINUTES=30
BATHROOM_WARN_MINUTES=20

# Night Wandering & Exit Guard:
# Active monitoring window for exit doors and hallway transit
NIGHT_GUARD_START=22:00
NIGHT_GUARD_END=06:00

# Bed Exit Thresholds:
# Minutes allowed out of bed during night hours before escalating
NIGHT_BED_EXIT_MAX_MINUTES=15

# Fall Verification Window:
# Consecutive seconds of sudden floor-level inactivity required to confirm fall
FALL_CONFIRM_SECONDS=10
```

---

## 5. Verification & Final Sign-Off Checklist

Before leaving the home, verify the following:

- [ ] **Empty Room Test**: Stand outside the room; verify Observatory / Dashboard displays `Empty / Vacant` with occupancy `0`.
- [ ] **Bed Exit Test**: Have someone enter the bed, lie down for 60 seconds, then exit. Confirm the transition registers on the Zones screen.
- [ ] **Night Guard Test**: Walk toward the simulated exit door. Confirm the event triggers on the Caregiver Mobile App / Dashboard.
- [ ] **Power Cycle Recovery**: Unplug the Mini PC hub, plug it back in, and verify that all services recover automatically via `syntropic-hub.service` within 90 seconds without user intervention.
- [ ] **Kiosk Glance View**: If a wall tablet is installed, ensure it is set to **Glance Mode (Dementia Clock)** showing Day, Time of Day, and reassuring message ("You are safe at home").
