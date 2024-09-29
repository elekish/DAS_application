import time
import serial
from openpyxl import Workbook
from collections import deque
import threading

BUFFER_SIZE = 200  # Buffer size for permanent buffer
TEMP_BUFFER_SIZE = 50  # Buffer size for temporary buffer


class SerialReader:
    """Initializing the serial port and workbook"""

    def __init__(self, serial_conn, num_channels=4, retry_attempts=3, retry_delay=0.00001):
        self.ser = serial_conn
        self.num_channels = num_channels
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.buffer = deque(maxlen=BUFFER_SIZE)
        self.temp_buffer = deque(maxlen=TEMP_BUFFER_SIZE)  # Temporary buffer for incoming data
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(["Serial Number", "Channel 0", "Channel 1", "Channel 2", "Channel 3"])
        self.lock = threading.Lock()

    def is_valid_data(self, data):
        """Check if the data is valid and corresponds to the expected format."""
        try:
            parts = data.split()
            if len(parts) < (self.num_channels + 1):  # Total channels + serial number
                raise ValueError("Incomplete Data Received")

            # Attempt to convert each value to float or handle underscores as None
            parsed_data = [None if '_' in part else part for part in parts]
            parsed_data = [float(value) if value and value != 'None' else None for value in parsed_data]
            return parsed_data
        except (ValueError, IndexError) as e:
            print(f"Invalid Serial Data: {data}.....Error: {e}")
            return None

    def read_and_store_serial_data(self):
        """Read data, buffer it, and process in chunks."""
        try:
            while True:
                # Check for incoming serial data
                if self.ser.in_waiting > 0:
                    serial_data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    parsed_data = self.is_valid_data(serial_data)

                    if parsed_data and len(parsed_data) > 4:
                        parsed_data = parsed_data[len(parsed_data) - 5:]  # Get the last 5 elements

                    if "battery" in serial_data.lower():
                        self._process_temp_buffer()
                        yield "Reset detected, stopping data capture."
                        return "Stopped"

                    if parsed_data:
                        # Use lock to safely access the buffer
                        with self.lock:
                            self.temp_buffer.append(parsed_data)
                            # Process the temporary buffer if it is full
                            if len(self.temp_buffer) >= TEMP_BUFFER_SIZE:
                                self._process_temp_buffer()

                        yield parsed_data  # Yield the valid parsed data

                    else:
                        print(f"Skipping invalid data: {serial_data}")

                # Small delay to avoid excessive CPU usage
                time.sleep(0.01)

        except Exception as e:
            print(f"Data capture stopped due to error: {e}")
            return "Stopped"

        finally:
            if self.temp_buffer:
                self._process_temp_buffer()
            return "Stopped"

    def _process_temp_buffer(self):
        """Move data from temporary buffer to the main buffer and write to Excel."""
        with self.lock:
            while self.temp_buffer:
                self.buffer.append(self.temp_buffer.popleft())  # Move data to the permanent buffer
            # Process the buffer if it's full
            if len(self.buffer) >= BUFFER_SIZE:
                self._process_buffer()

    def _process_buffer(self):
        """Write the data from the main buffer to the Excel file and clear the buffer."""
        for data in self.buffer:
            self.ws.append(data)

        self.wb.save("Serial_data2.xlsx")
        self.buffer.clear()
