import serial
import time
from PIL import Image

# --- Configuration ---
PORT = "COM3"  # Double-check this in Device Manager
BAUD = 115200
WIDTH = 128
HEIGHT = 160
CHUNK_SIZE = 512  # Matching the Pico's buffer size


def prepare_image(path):
    """Resizes and converts image to RGB565 bytes."""
    print(f"Opening {path}...")
    img = Image.open(path).resize((WIDTH, HEIGHT)).convert("RGB")
    raw_data = bytearray()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = img.getpixel((x, y))
            # Convert to 16-bit RGB565
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            # Send High byte then Low byte
            raw_data.append((rgb565 >> 8) & 0xFF)
            raw_data.append(rgb565 & 0xFF)
    return raw_data


def send_to_pico(image_path):
    data = prepare_image(image_path)
    total_bytes = len(data)

    with serial.Serial(PORT, BAUD, timeout=2) as ser:
        print("Connecting and putting Pico into Raw Mode...")

        # 1. Enter Raw REPL mode
        # This prevents the Pico from crashing if it sees bytes like 0x03 (Ctrl+C)
        ser.write(b'\r\x03\x03')  # Stop any running script
        time.sleep(0.1)
        ser.write(b'\x01')  # Ctrl+A: Enter Raw REPL
        time.sleep(0.1)

        # 2. Trigger the function on the Pico
        ser.write(b"receive_image()\r\n")

        # 3. Wait for the 'READY' signal from the Pico
        ready = False
        while not ready:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if "READY" in line:
                ready = True
                print("Pico is READY. Streaming data...")

        # 4. Stream the bytes in chunks
        start_time = time.time()
        for i in range(0, total_bytes, CHUNK_SIZE):
            chunk = data[i: i + CHUNK_SIZE]
            ser.write(chunk)

            # Tiny delay to allow Pico to move data from Serial to SPI
            time.sleep(0.005)

            if (i // CHUNK_SIZE) % 10 == 0:
                print(f"Sent: {i}/{total_bytes} bytes ({(i / total_bytes) * 100:.1f}%)", end='\r')

        # 5. Finalize
        print(f"\nSuccess! Total time: {time.time() - start_time:.2f}s")

        # Exit Raw REPL / Soft Reset the Pico to return to normal
        ser.write(b'\x02')
        print("Pico reset to normal mode.")


if __name__ == "__main__":
    try:
        send_to_pico("image.png")  # Make sure image.png is in the same folder
    except Exception as e:
        print(f"\nAn error occurred: {e}")