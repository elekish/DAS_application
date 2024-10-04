import sys
import serial
import serial_reader as sr
import serial_writer as sw
from auto_port_detection_qt import find_device_port
import threading
from collections import deque

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit
from PySide6.QtCore import QTimer, Qt


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.serial_conn = None
        self.reader = None
        self.writer = None
        self.reading = False
        self.data_buffer = deque(maxlen=2100)  # Limit buffer size to prevent excessive memory usage
        self.user_scrolled = False  # Track if the user has manually scrolled

        self.layout = QVBoxLayout(self)

        self.data_output = QTextEdit()
        self.data_output.setText("No connection yet.")
        self.data_output.setReadOnly(True)
        self.data_output.setLineWrapMode(QTextEdit.NoWrap)
        self.data_output.verticalScrollBar().valueChanged.connect(self.on_scroll)  # Connect scrollbar event
        self.layout.addWidget(self.data_output)

        self.read_button = QPushButton("Start Reading Data")
        self.read_button.clicked.connect(self.start_reading)
        self.layout.addWidget(self.read_button)

        self.stop_button = QPushButton("Stop Reading Data")
        self.stop_button.clicked.connect(self.stop_reading)
        self.layout.addWidget(self.stop_button)

        self.write_input = QLineEdit()
        self.write_input.setPlaceholderText("Enter data to send")
        self.layout.addWidget(self.write_input)

        self.write_button = QPushButton("Send Data")
        self.write_button.clicked.connect(self.send_data)
        self.layout.addWidget(self.write_button)

        # Create Quit button
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.quit_app)
        self.layout.addWidget(self.quit_button)

        self.reset_serial_connection()

        # Timer to update UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)  # Update every 100 ms

    def start_reading(self):
        if self.serial_conn:
            if not self.reading:
                self.reading = True
                self.read_thread = threading.Thread(target=self.read_data_thread)
                self.read_thread.daemon = True
                self.read_thread.start()
        else:
            self.data_output.append("Serial connection not established.")
            self.reset_serial_connection()

    def read_data_thread(self):
        while self.reading:
            try:
                data = next(self.reader.read_and_store_serial_data())
                if "Stopped" not in data:
                    print(f"Data received: {data}")  # Debugging line
                    self.data_buffer.append(data)
                else:
                    self.stop_reading()
                    self.reset_serial_connection()
            except StopIteration:
                pass
            except Exception as e:
                print(f"Error reading data: {e}")
                self.stop_reading()
                self.reset_serial_connection()

    def stop_reading(self):
        self.reading = False

    def send_data(self):
        if self.writer:
            data = self.write_input.text()
            if data.lower() != 'clear':
                self.writer.send_data_to_serial(data)
            else:
                self.update_data_output('clear')
            self.write_input.clear()

    def quit_app(self):
        self.stop_reading()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        QApplication.quit()

    def reset_serial_connection(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

        port = find_device_port()
        if port:
            try:
                self.serial_conn = serial.Serial(port=port, baudrate=38400, timeout=1)
                self.reader = sr.SerialReader(self.serial_conn)
                self.writer = sw.SerialWriter(self.serial_conn)
                self.data_output.setText("Connection established. Awaiting data...")
            except serial.SerialException as e:
                print(f"Error accessing serial port: {e}")
                self.data_output.setText("Failed to connect to serial port.")
        else:
            self.data_output.setText("No connection yet.")

    def update_ui(self):
        while self.data_buffer:
            new_data = self.data_buffer.popleft()
            self.update_data_output(new_data)
        # Ensure scrollbar is at the bottom only if the user hasn't scrolled manually
        if not self.user_scrolled:
            self.data_output.verticalScrollBar().setValue(self.data_output.verticalScrollBar().maximum())

    def update_data_output(self, new_data):
        if new_data != 'clear':
            formatted_data = ' '.join(map(str, new_data))
            self.data_output.append(formatted_data)
        else:
            self.data_output.clear()

    def on_scroll(self, value):
        # Track if the user has manually scrolled
        self.user_scrolled = True

    def on_scroll_end(self):
        # Called when the user stops scrolling to reset the flag
        self.user_scrolled = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
