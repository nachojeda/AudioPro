import sys
import pyaudio
import numpy as np
from scipy.fft import fft
import wave
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class SpectrogramRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Spectrogram Recorder")
        self.setGeometry(100, 100, 800, 600)

        # Audio settings
        self.CHUNK = 1024 * 2
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100
        self.recording = False
        self.frames = []

        # FFT and spectrogram settings
        self.freq_bins = self.CHUNK // 2
        self.time_bins = 100
        self.spectrogram_data = np.zeros((self.time_bins, self.freq_bins))
        
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = None

        # Setup UI
        self.setup_ui()
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.setInterval(30)  # 30ms update interval

    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)

        # Create buttons
        self.start_button = QPushButton("Start Recording")
        self.start_button.setStyleSheet("background-color: green; color: white;")
        self.start_button.clicked.connect(self.start_recording)

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.setStyleSheet("background-color: red; color: white;")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)

        self.status_label = QLabel("Status: Ready")

        # Add widgets to control layout
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

        # Create pyqtgraph plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')  # black background
        self.plot_widget.setLabel('left', 'Frequency', units='Hz')
        self.plot_widget.setLabel('bottom', 'Time')
        
        # Create image item for spectrogram
        self.img = pg.ImageItem()
        self.plot_widget.addItem(self.img)
        
        # Setup colormap
        colormap = pg.colormap.get('viridis')
        self.img.setColorMap(colormap)

        # Add widgets to main layout
        layout.addWidget(control_panel)
        layout.addWidget(self.plot_widget)

    def start_recording(self):
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=False,
            frames_per_buffer=self.CHUNK
        )
        
        self.recording = True
        self.frames = []
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Recording")
        self.status_label.setStyleSheet("color: red;")
        
        # Start timer for updates
        self.timer.start()

    def stop_recording(self):
        self.recording = False
        self.timer.stop()
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Save recording
        self.save_recording()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Ready")
        self.status_label.setStyleSheet("color: black;")
        
        # Clear spectrogram
        self.spectrogram_data = np.zeros((self.time_bins, self.freq_bins))
        self.img.setImage(self.spectrogram_data, autoLevels=True)

    def update_plot(self):
        if not self.recording:
            return
            
        # Read audio data
        data = np.frombuffer(
            self.stream.read(self.CHUNK, exception_on_overflow=False),
            dtype=np.float32
        )
        self.frames.append(data.tobytes())
        
        # Apply Hanning window
        data = data * np.hanning(len(data))
        
        # Compute FFT and normalize
        fft_data = np.abs(fft(data)[:self.freq_bins])
        fft_data = np.log10(fft_data + 1e-10)
        
        # Roll spectrogram data and update
        self.spectrogram_data = np.roll(self.spectrogram_data, 1, axis=0)
        self.spectrogram_data[0] = fft_data
        
        # Update image
        self.img.setImage(self.spectrogram_data, autoLevels=True)

    def save_recording(self):
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recordings/recording_{timestamp}.wav"
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paFloat32))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        self.status_label.setText(f"Status: Saved to {filename}")
        self.status_label.setStyleSheet("color: green;")

    def closeEvent(self, event):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpectrogramRecorder()
    window.show()
    sys.exit(app.exec_())