import serial
import serial.tools.list_ports


def find_device_port(baudrate=38400, timeout=2, query=b'\r\n'):
    serial_ports = []
    available_ports = serial.tools.list_ports.comports()

    if not available_ports:
        print("No COM ports found.")
        return None

    for port in available_ports:
        port_name = port.device
        print(f"Checking port: {port_name}")

        try:
            with serial.Serial(port.device, baudrate=baudrate, timeout=timeout) as ser:
                # Flush input and output buffers to ensure a clean state
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                # Send a simple query or command to check if a device responds
                ser.write(query)

                # Read a response from the device
                response = ser.read(100)  # Read up to 100 bytes from the port

                if response:
                    serial_ports.append(port_name)
                    print(f"Device found on port: {port_name}")
                else:
                    print(f"No response from port: {port_name}")

        except serial.SerialException as e:
            print(f"Could not open port {port_name}: {e}")
        except PermissionError:
            print(f"Permission denied for port {port_name}")

    if serial_ports:
        # Check for preferred ports first
        preferred_ports = [port for port in serial_ports if port not in ['COM3', 'COM1']]
        if preferred_ports:
            print(f"Connected to port {preferred_ports[0]}")
            return preferred_ports[0]

        # Fallback to specific ports
        if 'COM3' in serial_ports:
            print(f"Connected to port COM3")
            return 'COM3'
        if 'COM1' in serial_ports:
            print(f"Connected to port COM1")
            return 'COM1'

    # If no serial ports are found
    print("No device connected on any of the detected ports.")
    return None


# Usage example
if __name__ == "__main__":
    device_port = find_device_port()
    if device_port:
        print(f"Auto-detected port: {device_port}")
    else:
        print("No device found on any port.")
