# Syntropic Sense — In-Home Hub Installation & Operations Guide

This guide details how to deploy and operate the **Syntropic Sense In-Home Ambient Sensing Hub** for dementia and cognitive care. It covers both **Development Mode** (local workstations / laptops) and **In-Home Production Mode** (dedicated fanless x86_64 Mini PC).

---

## 1. System Overview & Architecture

The Syntropic Sense platform provides continuous, camera-free, zero-PII health and safety monitoring by analyzing RF Channel State Information (CSI) disturbance patterns from ambient ESP32 sensing nodes.

```
                   +-----------------------------------------------+
                   |                In-Home Network                |
                   +-----------------------------------------------+
                                          |
    +-------------------------+           | UDP Port 5005
    | ESP32 Ambient CSI Nodes | ----------+ (CSI RF Broadcasts)
    +-------------------------+           |
                                          v
                   +-----------------------------------------------+
                   |        Local In-Home Hub (Mini PC)            |
                   |                                               |
                   |  [syntropic-hub] (Rust Core Sensing Server)   |
                   |   * Digital Signal Processing (FFT / Welford) |
                   |   * Gait, Fall & Wandering Detection          |
                   |   * Local SQLite Telemetry Database           |
                   |   * REST API (:3000) & WebSocket (:3001)      |
                   |                                               |
                   |  [syntropic-kiosk] (Local Dashboard Web App)  |
                   |   * Wall Kiosk Mode / Dementia Clock          |
                   |   * Caregiver Portal                          |
                   +-----------------------------------------------+
                               |                     |
                               | LAN WebSocket       | Outbound Push
                               v                     v
                   [In-Home Wall Tablet]    [Caregiver Mobile / SMS]
```

---

## 2. Hardware Prerequisites

### Production Hub (In-Home)
- **Recommended Platform**: x86_64 Fanless Mini PC (Intel N100 / N97 / N200)
- **Memory**: 8 GB to 16 GB DDR4/DDR5
- **Storage**: 128 GB+ NVMe SSD
- **OS**: Ubuntu 24.04 LTS Server or Debian 12 (Bookworm)
- **Networking**: Dual Gigabit Ethernet or Wi-Fi 6 (connected to the home 2.4/5 GHz LAN)
- **Power**: 12V DC (~6W–12W continuous draw)

### Ambient Sensor Nodes
- 2 to 6 ESP32-S3 or ESP32-C6 nodes running `firmware/esp32-csi-node/`
- Standard 5V USB wall adapters placed in key rooms (bedroom, hallway, bathroom, main living area).

---

## 3. Production Deployment (In-Home Mini PC)

Production uses containerized services via Docker Compose with automated system recovery, isolated user privileges, and health checks.

### Step 3.1: Install Docker & Dependencies

On the clean Mini PC Linux installation:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker Engine and Docker Compose plugin
sudo apt install -y curl git ca-certificates
curl -fsSL https://get.docker.com | sudo sh

# Allow running docker without root
sudo usermod -aG docker $USER
newgrp docker
```

### Step 3.2: Configure the Hub Environment

Clone the repository with submodules (or run `git submodule update --init --recursive`), then set up production environment variables:

```bash
cd /opt
sudo git clone --recurse-submodules https://github.com/syntropic-labs/syntropic-sense.git hub
sudo chown -R $USER:$USER /opt/hub
cd /opt/hub

# If cloned without --recurse-submodules, initialize them now:
git submodule update --init --recursive

# Generate production environment
cp example.env .env
```

Configure `.env` for production:
```bash
# Data source: real CSI from in-home ESP32 nodes
CSI_SOURCE=esp32

# Logging level (info / warn)
RUST_LOG=info

# Bind address: 0.0.0.0 allows tablets/phones on the same LAN to access the dashboard
RUVIEW_BIND_ADDR=0.0.0.0

# Optional API Token for securing LAN endpoints
RUVIEW_API_TOKEN=generate_a_secure_token_here

# Dementia care thresholds
BATHROOM_MAX_MINUTES=30
NIGHT_GUARD_START=22:00
NIGHT_GUARD_END=06:00
```

### Step 3.3: Build & Launch with Docker Compose

Run the production containers in detached mode:

```bash
cd /opt/hub/docker
docker compose -f docker-compose.yml up -d --build sensing-server
```

Verify service health:
```bash
docker compose ps
docker compose logs -f sensing-server
```

The hub will immediately start listening on:
- `UDP 5005`: Ingesting CSI packets from ESP32 nodes.
- `TCP 3000`: REST API.
- `TCP 3001`: Real-time WebSocket streaming.

### Step 3.4: Configure Auto-Start on Boot (systemd)

Ensure the hub restarts automatically after power outages or home reboots:

Create `/etc/systemd/system/syntropic-hub.service`:
```ini
[Unit]
Description=Syntropic Sense In-Home Ambient Care Hub
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/hub/docker
ExecStart=/usr/bin/docker compose up -d sensing-server
ExecStop=/usr/bin/docker compose down
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable syntropic-hub.service
sudo systemctl start syntropic-hub.service
```

---

## 4. Development Deployment (Workstation / Laptop)

For development, testing algorithms, and UI iteration without physical ESP32 hardware, the server can run in simulated CSI mode.

### Step 4.1: Prerequisites
- **Rust Toolchain**: 1.80+ (`rustup default stable`)
- **System Build Packages**: `pkg-config`, `libssl-dev`, `build-essential`
- **Git Submodules**: Must be initialized for vendor dependencies (`rufield`, `ruvector`, `rvcsi`, `worldgraph`)
- **Node.js**: v20+ with npm
- **Python**: 3.11+ (optional for analysis scripts)

Install build packages (Ubuntu / Debian):
```bash
sudo apt update && sudo apt install -y pkg-config libssl-dev build-essential git
```

Install Rust (if not installed):
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

Ensure vendor submodules are populated:
```bash
git submodule update --init --recursive
```

### Step 4.2: Running the Sensing Server (Rust)

Run the backend server locally using synthetic CSI simulation:

```bash
cd v2
cargo run --release -p wifi-densepose-sensing-server -- \
  --source simulated \
  --http-port 3000 \
  --ws-port 3001 \
  --tick-ms 100 \
  --load-rvf docker/wifi-densepose-v1.rvf
```

*Tip: For live code reloading during backend development, use `cargo watch -x 'run -p wifi-densepose-sensing-server -- --source simulated'`.*

> **Note on `/api/v1/model/info` and RVF Containers:**
> If you query `http://localhost:3000/api/v1/model/info` and receive:
> ```json
> {"message": "No RVF container loaded. Use --load-rvf <path> to load one.", "status": "no_model"}
> ```
> This indicates that the server started without an explicit pre-trained neural neural network model container (`.rvf` = RuVector Format). 
> - **Is this an error?** No. The server's real-time digital signal processing (FFT, Welford statistical filters, breathing rate, and gait analysis) runs fully without a neural model.
> - **How to load one:** Pass `--load-rvf docker/wifi-densepose-v1.rvf` (or set `MODELS_DIR=data/models` in `.env` / Docker) to enable the progressive deep neural network pose estimator.

### Step 4.3: Running the Web Dashboard / Kiosk

In a second terminal:

```bash
cd dashboard
npm install
npm run dev
```
Open your browser at `http://localhost:5173`. The dashboard will connect to the local WebSocket server at `ws://localhost:3001`.

### Step 4.4: Running the Caregiver Mobile App (Expo / React Native)

In a third terminal:

```bash
cd ui/mobile
npm install
npm start
```
Press `w` to open in a web browser, or scan the QR code using Expo Go on your mobile device (ensure your device is connected to the same Wi-Fi network).

---

## 5. ESP32 Ambient Sensor Node Setup

### Step 5.1: Flashing Sensor Nodes
Navigate to `firmware/esp32-csi-node/`:
```bash
cd firmware/esp32-csi-node
idf.py set-target esp32s3
idf.py menuconfig
```
Under `Syntropic CSI Node Configuration`:
1. Set the home **Wi-Fi SSID** and **Password**.
2. Set the **Destination Hub IP** (the static or reserved LAN IP of the Mini PC, e.g. `192.168.1.150`).
3. Set the **Destination Port** to `5005`.
4. Flash the node:
   ```bash
   idf.py -p /dev/ttyACM0 flash monitor
   ```

### Step 5.2: Node Placement Guidelines
- **Bedroom**: Mount 1.2m above floor level, opposite the bed, oriented toward the sleeping zone.
- **Bathroom**: Place near the entrance outside moisture zones, pointed toward the shower/toilet path.
- **Main Living Room**: Mount at chest height in a central corner with an unobstructed field across the room.
- **Hallway**: Placed to capture transit cadence between the bedroom and exterior exit doors.

---

## 6. Verification & Health Diagnostics

Run the quick verification check from any computer on the home network:

```bash
# Check REST API Status
curl http://<HUB_IP>:3000/api/health

# Check WebSocket Connectivity
wscat -c ws://<HUB_IP>:3001/ws
```

Expected response from `/api/health`:
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "source": "esp32",
  "nodes_active": 3,
  "last_packet_age_ms": 42
}
```

---

## 7. Troubleshooting & Recovery

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| `Could not find directory of OpenSSL installation` / `pkg-config could not be found` | Missing C build tools and OpenSSL headers on host | Run `sudo apt install -y pkg-config libssl-dev build-essential`. |
| `failed to read .../vendor/rufield/crates/rufield-adapters/Cargo.toml` | Git submodules are not checked out | Run `git submodule update --init --recursive` in the repository root. |
| `permission denied while trying to connect to the docker API` | Non-root user is not in the `docker` group | Run `sudo usermod -aG docker $USER && newgrp docker`, or execute with `sudo docker compose ...`. |
| `exit code 78` on server startup | No CSI packets detected from ESP32 nodes | Verify ESP32 nodes are powered and configured with the hub's LAN IP. Use `--source simulated` for dev testing. |
| `No RVF container loaded` on `/api/v1/model/info` | Server started without `--load-rvf <path>` | Optional: DSP and vitals continue working without it. To load, pass `--load-rvf docker/wifi-densepose-v1.rvf` or mount a model in Docker. |
| Dashboard shows "Disconnected" | WebSocket port 3001 blocked by host firewall | Run `sudo ufw allow 3000/tcp && sudo ufw allow 3001/tcp && sudo ufw allow 5005/udp`. |
| Packet drop / High latency | 2.4 GHz Wi-Fi congestion in the home | Switch ESP32 broadcast channel in `menuconfig` to an uncongested channel (1, 6, or 11). |
| Mini PC rebooted | Power outage / surge | Verify `syntropic-hub.service` is enabled via `systemctl is-enabled syntropic-hub`. Consider attaching an inexpensive UPS battery backup. |
