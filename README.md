# RPY Perspector

A hardware input console that eliminates 90% of palm movements in 3D CAD 
and animation workflows. Three independently rotatable concentric ring annuli, 
a curved capacitive touch surface, and an underlying mouse — built to match 
the cognitive logic of sketch-based 3D modelling.

**Demo video:**
https://youtu.be/DvIXj57UrYQ

## What it does

- **6D viewport navigation** — rotate two AS5600 magnetic encoder rings to 
  orbit the 3D viewport (yaw + pitch), no palm movement required
- **Snap to plane** — tap the copper tape capacitive surface to snap 
  instantly to Top or Left view
- Designed for OnShape (current POC); extensible to Blender, SolidWorks, Plasticity

## Hardware

| Component | Role | Pins |
|-----------|------|------|
| AS5600 magnetic encoder #1 | Yaw (ring 1 rotation) | Hardware I2C — SDA/SCL |
| AS5600 magnetic encoder #2 | Pitch (ring 2 rotation) | Soft I2C — D3 (SDA), D4 (SCL) |
| Capacitive sensor (copper tape) | Snap-to-plane trigger | D7 (send), D8 (receive) |
| Arduino (Uno/Nano) | Serial bridge to Python | USB |

## Repository structure
    rpy-perspector/
    ├── firmware/
    │   └── dual_encoder_4cap.ino
    ├── src/
    │   └── onshape_control.py
    ├── hardware/
    └── demo/


## Installation

**Requirements:** Python 3.9+, Arduino IDE, Chrome browser

### 1. Flash the Arduino

Open `firmware/dual_encoder_4cap.ino` in Arduino IDE.

Install these libraries via Arduino Library Manager:
- `SoftI2C`
- `CapacitiveSensor`

Flash to your Arduino. Open Serial Monitor at 9600 baud — you should 
see output like:
185.4,92.1,v1:23,v2:23

### 2. Install Python dependencies

```bash
pip install pyserial selenium webdriver-manager
```

### 3. Configure serial port

Open `src/onshape_control.py` and update:
```python
SERIAL_PORT = "/dev/cu.usbmodem3101"  # Mac example
# Windows: "COM3"
# Linux:   "/dev/ttyUSB0"
```

### 4. Launch Chrome with remote debugging

Close all Chrome windows first, then run:

**Mac:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```
**Windows:**
```bash
chrome.exe --remote-debugging-port=9222
```

Open OnShape in that Chrome window and load a document.

### 5. Run the controller

```bash
cd src
python onshape_control.py
```

## Usage

| Action | Result |
|--------|--------|
| Rotate ring 1 | Orbits viewport horizontally (yaw) |
| Rotate ring 2 | Orbits viewport vertically (pitch) |
| Tap copper tape (light) | Snap to Top view |
| Tap copper tape (firm) | Snap to Left view |

Sensitivity can be adjusted in `onshape_control.py`:
```python
SENSITIVITY = 0.4  # increase if rotation feels too slow
CAP_THRESHOLD = 40  # capacitive tap sensitivity
```

## Traction

- Accepted into **IITM Nirmaan pre-incubator**
- 10+ iterated 3D-printed mechanical prototypes
- Customer validation with MTech Engineering Design students at IIT Madras
- In discussion with Keiretsu Forum angel investors (pre-seed)

## Status

Active — working POC with two-ring assembly, snap-back mechanism, 
and clickable ring edges. Expanding to full 5-function device.
