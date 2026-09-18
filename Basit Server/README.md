# Multi-Drone Telemetry Sender

A lightweight Python application for collecting telemetry from multiple MAVSDK-connected drones and sending the latest telemetry data to an HTTP server.

The current implementation connects to two drones through separate UDP ports, listens to their telemetry streams asynchronously, and sends the most recent telemetry snapshot to a REST endpoint once per second.

---

## Overview

The application currently connects to:

```text
Drone 1 → udp://:14541
Drone 2 → udp://:14542
```

Telemetry is sent to:

```text
http://0.0.0.0:5000/api/telemetri_gonder
```

Main data flow:

```text
Drone 1 ── MAVSDK ──┐
                     ├── Telemetry Collection ── HTTP POST ── Server
Drone 2 ── MAVSDK ──┘
```

Each drone is processed independently with asynchronous telemetry tasks.

---

## Collected Telemetry

The script subscribes to the following MAVSDK telemetry streams:

- Battery percentage
- GPS information
- In-air status
- Position
- Absolute altitude
- Relative altitude

Example telemetry payload:

```json
{
  "drone_name": "Drone 1",
  "telemetry": {
    "battery": 0.82,
    "gps_info": {
      "num_satellites": 14,
      "fix_type": 3
    },
    "in_air": true,
    "position": {
      "latitude_deg": 39.000000,
      "longitude_deg": 32.000000,
      "absolute_altitude_m": 1020.4,
      "relative_altitude_m": 43.8
    }
  }
}
```

The telemetry dictionary contains the latest value received from each active MAVSDK stream.

---

## Example Stored Data Structure

A server can organize incoming telemetry by drone name and timestamp.

Example:

```json
{
  "Drone 1": {
    "2025-03-12T16:48:39.547125": {},
    "2025-03-12T16:48:40.549860": {},
    "2025-03-12T16:48:41.553649": {},
    "2025-03-12T16:48:42.556461": {}
  }
}
```

With telemetry values included, the same structure can be extended as:

```json
{
  "Drone 1": {
    "2025-03-12T16:48:39.547125": {
      "battery": 0.82,
      "gps_info": {
        "num_satellites": 14,
        "fix_type": 3
      },
      "in_air": true,
      "position": {
        "latitude_deg": 39.000000,
        "longitude_deg": 32.000000,
        "absolute_altitude_m": 1020.4,
        "relative_altitude_m": 43.8
      }
    }
  }
}
```

Timestamp generation and persistent storage are expected to be handled by the receiving server.

---

## Requirements

- Python 3
- MAVSDK
- aiohttp
- asyncio

Install Python dependencies with:

```bash
pip install mavsdk aiohttp
```

---

## Project Structure

A minimal repository can be organized as:

```text
.
├── telemetry_sender.py
└── README.md
```

---

## How It Works

### 1. Drone Connections

Two independent MAVSDK `System` objects are created:

```python
drone1 = System()
await drone1.connect(system_address="udp://:14541")

drone2 = System()
await drone2.connect(system_address="udp://:14542")
```

Each drone is passed to its own telemetry-processing coroutine.

---

### 2. Telemetry Collection

For every drone, a shared dictionary stores the latest telemetry values:

```python
telemetry_data = {}
```

The intended structure is:

```python
{
    "battery": ...,
    "gps_info": ...,
    "in_air": ...,
    "position": ...
}
```

Each MAVSDK telemetry stream runs asynchronously.

---

### 3. Battery

Battery information is read from:

```python
drone.telemetry.battery()
```

Stored value:

```text
battery.remaining_percent
```

---

### 4. GPS Information

GPS information is read from:

```python
drone.telemetry.gps_info()
```

Stored fields:

```text
num_satellites
fix_type
```

---

### 5. In-Air State

Flight state is read from:

```python
drone.telemetry.in_air()
```

The value indicates whether the vehicle is currently airborne.

---

### 6. Position

Position is read from:

```python
drone.telemetry.position()
```

Stored fields:

```text
latitude_deg
longitude_deg
absolute_altitude_m
relative_altitude_m
```

---

## HTTP Communication

The latest telemetry data are wrapped in the following payload:

```python
payload = {
    "drone_name": drone_name,
    "telemetry": telemetry_data
}
```

The payload is sent using an HTTP POST request:

```python
async with session.post(
    server_address,
    json=payload
) as response:
    ...
```

The sender waits approximately one second between requests:

```python
await asyncio.sleep(1)
```

This produces an approximate telemetry transmission rate of:

```text
1 Hz
```

---

## Running

Start MAVSDK/PX4/SITL or the real vehicle connections so that the expected UDP ports are available.

Then run:

```bash
python3 telemetry_sender.py
```

The application remains active continuously:

```python
while True:
    await asyncio.sleep(1)
```

Stop it with:

```text
Ctrl + C
```

---

## Multi-Drone Architecture

Current architecture:

```text
                    ┌──────────────────┐
                    │     Drone 1      │
                    │    UDP 14541     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ MAVSDK System 1  │
                    └────────┬─────────┘
                             │
                             │
                             ▼
                    ┌──────────────────┐
                    │ Telemetry Task 1 │
                    └────────┬─────────┘
                             │
                             │
                             ├───────────────┐
                             │               │
                             ▼               ▼
                     Latest State        HTTP POST
                             │               │
                             └───────┬───────┘
                                     │
                                     ▼
                              REST API Server

                    ┌──────────────────┐
                    │     Drone 2      │
                    │    UDP 14542     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ MAVSDK System 2  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Telemetry Task 2 │
                    └────────┬─────────┘
                             │
                             ▼
                              REST API Server
```

The same structure can be extended to more drones by assigning each vehicle a separate connection address and launching another telemetry-processing task.

---

## Server Response Handling

If the server returns HTTP status code `200`, the response body is printed:

```text
Drone 1 Server Response: ...
```

For non-200 responses, the application prints:

```text
Error sending telemetry
Status code
Response content
```

Network errors raised by `aiohttp` are also caught so the telemetry loop can continue running.

---

## Configuration

The current values are hard-coded in the script:

```python
drone1.connect(system_address="udp://:14541")
drone2.connect(system_address="udp://:14542")
```

and:

```text
http://0.0.0.0:5000/api/telemetri_gonder
```

For a reusable application, these values can later be moved to:

- command-line arguments
- environment variables
- JSON/YAML configuration files
- ROS parameters

---

## Important Network Note

`0.0.0.0` is normally used by servers as a bind address.

If the HTTP API is running on the same computer as this telemetry sender, the client address will commonly be:

```text
http://127.0.0.1:5000/api/telemetri_gonder
```

If the server is running on another machine, replace the host with that machine's reachable IP address.

---

## Current Implementation Note

The source defines:

```python
async def print_and_store_data(data_type, data):
    telemetry_data[data_type] = data
```

but the telemetry reader functions call it without `await`.

For example:

```python
print_and_store_data("battery", battery.remaining_percent)
```

Because the helper is declared with `async def`, it should either be awaited:

```python
await print_and_store_data(
    "battery",
    battery.remaining_percent
)
```

or changed into a regular function:

```python
def print_and_store_data(data_type, data):
    telemetry_data[data_type] = data
    print(f"{drone_name} {data_type}: {data}")
```

Since this helper performs no asynchronous I/O, making it a normal function is the simpler option.

---

## Future Improvements

Possible improvements include:

- configuration file support
- automatic drone discovery
- reconnection logic
- connection-state monitoring
- telemetry timestamps
- local JSON logging
- database storage
- WebSocket telemetry streaming
- configurable send frequency
- per-drone health monitoring
- more MAVSDK telemetry fields
- authentication for the REST endpoint

---

## Purpose

This project provides a simple asynchronous architecture for collecting telemetry from multiple MAVSDK drones and forwarding the latest state to a centralized HTTP server.

The design separates:

```text
Vehicle Connection
       ↓
Telemetry Collection
       ↓
Latest State
       ↓
HTTP Transmission
       ↓
Central Storage / Monitoring
```

This makes it suitable as a starting point for multi-UAV telemetry dashboards, ground-control applications, logging systems, and swarm-monitoring experiments.
