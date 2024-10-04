class SerialWriter:
    def __init__(self, serial_conn):
        self.ser = serial_conn

    def send_data_to_serial(self, data):
        try:
            self.ser.write(data.encode('utf-8'))
            print(f"Sent data: {data}")
            print(f"{self.ser.readline().decode('utf-8', errors='ignore').strip()}")
            time.sleep(0.1)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Data Written Successfully")
