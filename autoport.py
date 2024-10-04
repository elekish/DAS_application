from usbserial4a import usb

def find_device_port(baudrate=38400, timeout=2, query=b'\r\n'):
    devices = usb.get_usb_device_list()

    if not devices:
        print("No USB devices found.")
        return None

    for device in devices:
        print(f"Checking device: {device.getDeviceName()} - Vendor: {device.getVendorId()} - Product: {device.getProductId()}")

        try:
            port_name = '/dev/ttyUSB0'  # You may need to adapt this based on your device
            serial_conn = serial_for_url(port_name, baudrate=baudrate, timeout=timeout)
            serial_conn.reset_input_buffer()
            serial_conn.reset_output_buffer()

            # Send a simple query or command to check if a device responds
            serial_conn.write(query)

            # Read a response from the device
            response = serial_conn.read(100)  # Read up to 100 bytes from the port

            if response:
                print(f"Device found on port: {port_name}")
                return port_name

            print(f"No response from port: {port_name}")
            serial_conn.close()  # Close connection if no response

        except Exception as e:
            print(f"Could not access device {device}: {e}")

    print("No device connected on any of the detected ports.")
    return None
