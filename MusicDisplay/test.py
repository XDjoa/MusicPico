import serial, base64, os
from PIL import Image

PORT = "COM3"

def send_image(file_path, size=(128, 128)):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    # 1. Process Image
    img = Image.open(file_path).resize(size).convert("RGB")
    pixels = bytearray()
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b = img.getpixel((x, y))
            rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixels.extend([(rgb >> 8) & 0xFF, rgb & 0xFF])

    data = base64.b64encode(pixels)

    # 2. Stream to Pico
    with serial.Serial(PORT, 115200, timeout=2) as ser:
        ser.write(b'\n')
        if b"READY" in ser.readline():
            print(f"Sending {file_path}...")
            for i in range(0, len(data), 512):
                ser.write(data[i:i+512])
                ser.read_until(b"OK")
            print("Done.")

# --- Example Usage ---
if __name__ == "__main__":
    send_image("image.png")
