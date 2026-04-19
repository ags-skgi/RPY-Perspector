import serial
import time
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ── Configuration ──────────────────────────────────────────────
SERIAL_PORT   = "/dev/cu.usbmodem3101"  # change to your port
BAUD_RATE     = 9600
CAP_THRESHOLD = 40       # capacitive tap threshold
SENSITIVITY   = 0.4      # how many pixels to drag per degree change
                         # increase if rotation feels too slow

WINDOW_SIZE = 10
cap_buffer = []
# ───────────────────────────────────────────────────────────────

def open_serial(port, baud):
    try:
        return serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open serial port {port}: {e}")
        raise

def read_data(ser):
    """Parse 'yaw,pitch,v1:xxx,v2:xxx' from serial."""
    try:
        line  = ser.readline().decode("utf-8").strip()
        parts = line.split(",")
        if len(parts) == 4:
            yaw   = float(parts[0])
            pitch = float(parts[1])

            v2_str = parts[3]  # "v2:xxx"
            val = float(v2_str.split(":")[1])

            return yaw, pitch, val
    except (ValueError, UnicodeDecodeError):
        pass
    return None

def attach_to_chrome():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service("/Users/arvingopal5794/.wdm/drivers/chromedriver/mac64/146.0.7680.80/chromedriver-mac-arm64/chromedriver")
    driver  = webdriver.Chrome(service=service, options=options)
    print(f"Attached to Chrome. Current page: {driver.title}")
    return driver

def get_viewport(driver):
    """Find the OnShape 3D viewport canvas element."""
    try:
        # OnShape's main canvas
        canvas = driver.find_element(By.CSS_SELECTOR, "canvas.node-3d-canvas")
        return canvas
    except Exception:
        try:
            # fallback selector
            canvas = driver.find_element(By.TAG_NAME, "canvas")
            return canvas
        except Exception as e:
            print(f"Could not find viewport canvas: {e}")
            return None

def rotate_viewport(driver, canvas, dx_deg, dy_deg):
    """
    Simulate right-click drag to rotate OnShape viewport.
    dx_deg = horizontal rotation (yaw delta)
    dy_deg = vertical rotation (pitch delta)
    """
    if abs(dx_deg) < 5.0 and abs(dy_deg) < 5.0:
        return

    px = int(dx_deg * SENSITIVITY)
    py = int(dy_deg * SENSITIVITY)

    if px == 0 and py == 0:
        return

    # Get canvas centre
    size = canvas.size
    cx   = size["width"]  // 2
    cy   = size["height"] // 2

    actions = ActionChains(driver)
    # OnShape rotates on right-click drag
    actions.move_to_element_with_offset(canvas, cx, cy)
    actions.click_and_hold()   # right button via JS below
    actions.move_by_offset(px, py)
    actions.release()

    # Use JS to simulate right-click drag more reliably
    driver.execute_script("""
        var canvas = arguments[0];
        var dx = arguments[1];
        var dy = arguments[2];
        var cx = canvas.width  / 2;
        var cy = canvas.height / 2;

        function makeEvent(type, x, y, button) {
            return new MouseEvent(type, {
                bubbles: true, cancelable: true,
                clientX: x, clientY: y,
                button: button, buttons: button === 2 ? 2 : 0
            });
        }

        canvas.dispatchEvent(makeEvent('mousedown', cx,      cy,      2));
        canvas.dispatchEvent(makeEvent('mousemove', cx + dx, cy + dy, 2));
        canvas.dispatchEvent(makeEvent('mouseup',   cx + dx, cy + dy, 2));
    """, canvas, px, py)

def snap_to_top(driver):
    try:
        canvas = driver.find_element(By.CSS_SELECTOR, "canvas")
        actions = ActionChains(driver)
        # First escape any popup
        actions.move_to_element(canvas)
        actions.send_keys(Keys.ESCAPE)
        actions.pause(0.3)
        # Then send Shift+5
        actions.key_down(Keys.SHIFT)
        actions.send_keys('5')
        actions.key_up(Keys.SHIFT)
        actions.perform()
        print("Snapped to Top view")
    except Exception as e:
        print(f"Snap to top failed: {e}")

def snap_to_left(driver):
    try:
        canvas = driver.find_element(By.CSS_SELECTOR, "canvas")
        actions = ActionChains(driver)

        actions.move_to_element(canvas)
        actions.send_keys(Keys.ESCAPE)
        actions.pause(0.3)

        # Shift+6 (OnShape bottom view shortcut)
        actions.key_down(Keys.SHIFT)
        actions.send_keys('3')
        actions.key_up(Keys.SHIFT)

        actions.perform()
        print("Snapped to Left view")
    except Exception as e:
        print(f"Snap to bottom failed: {e}")

def angle_delta(prev, curr):
    """Shortest angular difference, handling 0/360 wraparound."""
    delta = curr - prev
    if delta >  180: delta -= 360
    if delta < -180: delta += 360
    return delta

def main():
    print("Attaching to Chrome...")
    driver = attach_to_chrome()

    print("Finding OnShape viewport...")
    canvas = get_viewport(driver)
    if canvas is None:
        print("ERROR: Could not find OnShape canvas. Make sure OnShape is open and a document is loaded.")
        return

    print("Opening serial port...")
    ser = open_serial(SERIAL_PORT, BAUD_RATE)

    prev_yaw   = None
    prev_pitch = None
    last_cap_above = False  # track finger up/down for tap detection

    print("Running. Rotate rings to orbit viewport. Tap Cu tape to snap to Top view.")
    print("Press Ctrl+C to quit.\n")

    lval = 800
    uval = 4000

    while True:
        result = read_data(ser)
        if result is None:
            continue

        yaw, pitch, capval = result

        # Initialise previous values on first valid read
        if prev_yaw is None:
            prev_yaw   = yaw
            prev_pitch = pitch
            continue

        # ── Running max window for stable snapping ──
        cap_buffer.append(capval)
        
        if len(cap_buffer) >= WINDOW_SIZE:
            max_val = max(cap_buffer)
        
            state = None
            if 100 < max_val < uval:
                state = "TOP"
            elif max_val > uval:
                state = "LEFT"
        
            # Trigger only on state change
            if state == "TOP" and last_cap_above != "TOP":
                snap_to_top(driver)
                time.sleep(0.5)
        
            elif state == "LEFT" and last_cap_above != "LEFT":
                snap_to_left(driver)
                time.sleep(0.5)
        
            last_cap_above = state
        
            # reset buffer
            cap_buffer.clear()

        # ── Viewport rotation ──
        dy = angle_delta(prev_yaw,   yaw)
        dp = angle_delta(prev_pitch, pitch)

        rotate_viewport(driver, canvas, dy, dp)

        prev_yaw   = yaw
        prev_pitch = pitch

        time.sleep(0.02)  # ~50Hz

if __name__ == "__main__":
    main()
