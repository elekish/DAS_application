class SerialReader:
    def __init__(self, serial_conn, num_channels=4, retry_attempts=3, retry_delay=0.00001):
        self.ser = serial_conn
        self.num_channels = num_channels
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.buffer = deque(maxlen=BUFFER_SIZE)
        self.temp_buffer = deque(maxlen=TEMP_BUFFER_SIZE)
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(["Serial Number", "Channel 0", "Channel 1", "Channel 2", "Channel 3"])
        self.lock = threading.Lock()

    def is_valid_data(self, data):
        try:
            parts = data.split()
            if len(parts) < (self.num_channels + 1):
                raise ValueError("Incomplete Data Received")
            parsed_data = [None if '_' in part else part for part in parts]
            parsed_data = [float(value) if value and value != 'None' else None for value in parsed_data]
            return parsed_data
        except (ValueError, IndexError) as e:
            print(f"Invalid Serial Data: {data}.....Error: {e}")
            return None

    def read_and_store_serial_data(self):
        try:
            while True:
                if self.ser.in_waiting > 0:
                    serial_data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    parsed_data = self.is_valid_data(serial_data)

                    if parsed_data and len(parsed_data) > 4:
                        parsed_data = parsed_data[len(parsed_data) - 5:]

                    if "battery" in serial_data.lower():
                        self._process_temp_buffer()
                        yield "Reset detected, stopping data capture."
                        return "Stopped"

                    if parsed_data:
                        with self.lock:
                            self.temp_buffer.append(parsed_data)
                            if len(self.temp_buffer) >= TEMP_BUFFER_SIZE:
                                self._process_temp_buffer()
                        yield parsed_data
                    else:
                        print(f"Skipping invalid data: {serial_data}")

                time.sleep(0.01)
        except Exception as e:
            print(f"Data capture stopped due to error: {e}")
            return "Stopped"
        finally:
            if self.temp_buffer:
                self._process_temp_buffer()
            return "Stopped"

    def _process_temp_buffer(self):
        with self.lock:
            while self.temp_buffer:
                self.buffer.append(self.temp_buffer.popleft())
            if len(self.buffer) >= BUFFER_SIZE:
                self._process_buffer()

    def _process_buffer(self):
        for data in self.buffer:
            self.ws.append(data)
        self.wb.save("Serial_data2.xlsx")
        self.buffer.clear()
