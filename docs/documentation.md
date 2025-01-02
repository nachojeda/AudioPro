# Real-time Spectrogram Application Documentation

This documentation covers a real-time audio spectrogram application that visualizes audio frequency data. The application consists of a Python backend that processes audio input and a JavaScript frontend that renders the visualization.

## Backend Documentation (Python)

The backend is built using FastAPI and handles real-time audio processing using PyAudio and NumPy.

### Key Components

#### FastAPI Server Setup
```python
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- Initializes a FastAPI application with CORS middleware to allow cross-origin requests
- Essential for WebSocket communication with the frontend

#### AudioProcessor Class

##### Initialization Parameters
```python
CHUNK = 4096        # Buffer size for audio processing
FORMAT = paFloat32  # Audio format (32-bit float)
CHANNELS = 1        # Mono audio
RATE = 44100       # Sample rate in Hz
```

##### Key Methods

1. `__init__()`:
   - Initializes audio processing parameters
   - Sets up frequency bins and Hanning window for FFT
   - Establishes reference level for dB calculations

2. `start_stream()`:
   - Initializes PyAudio instance
   - Opens audio input stream with configured parameters

3. `stop_stream()`:
   - Safely closes audio stream and terminates PyAudio instance

4. `get_audio_data()`:
   - Reads audio chunk from stream
   - Applies Hanning window to reduce spectral leakage
   - Performs FFT and converts to dB scale
   - Normalizes data for frontend visualization
   - Returns frequency information and normalized data

#### WebSocket Handler
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket)
```
- Manages WebSocket connections
- Handles start/stop commands
- Streams processed audio data at ~30fps

### Data Processing Flow

1. **Audio Capture**
   - Captures raw audio data in chunks
   - Uses PyAudio for real-time audio input

2. **Signal Processing**
   - Applies Hanning window to reduce spectral leakage
   - Performs FFT to convert time-domain to frequency-domain
   - Converts to dB scale with proper reference level
   - Normalizes data for visualization

3. **Data Streaming**
   - Sends processed data via WebSocket
   - Includes frequency information and normalized magnitude values
   - Maintains ~30fps update rate

## Frontend Documentation (JavaScript)

The frontend is built using vanilla JavaScript and HTML5 Canvas for visualization.

### SpectrogramVisualizer Class

#### Core Components

1. **Canvas Setup**
   - Responsive canvas sizing
   - WebGL context initialization
   - Grid and axis generation

2. **State Management**
   ```javascript
   initializeState() {
       this.spectrogramData = [];
       this.isRecording = false;
       this.freqInfo = null;
       this.maxHistoryLength = 167; // 5 seconds at ~30fps
   }
   ```

3. **WebSocket Communication**
   - Establishes connection with backend
   - Handles real-time data reception
   - Manages connection lifecycle

#### Visualization Features

1. **Spectrogram Rendering**
   - Color mapping based on magnitude
   - Logarithmic frequency scaling
   - Real-time updates
   - History management

2. **Interactive Elements**
   - Tooltip with frequency and magnitude information
   - Start/Stop recording controls
   - History clearing
   - Image export functionality

3. **Axis and Grid System**
   - Logarithmic frequency axis (20Hz - 20kHz)
   - Time axis with seconds
   - dB scale (-120dB to 0dB)
   - Dynamic grid lines

### UI Components

1. **Control Panel**
   - Start/Stop recording buttons
   - Clear history button
   - Export image button
   - Status indicator

2. **Visualization Container**
   - Main spectrogram canvas
   - Frequency axis (Y-axis)
   - Time axis (X-axis)
   - dB scale with gradient

3. **Interactive Features**
   - Hover tooltips with detailed information
   - Real-time updates
   - Responsive layout

## Suggested Improvements

### Backend Improvements

1. **Error Handling**
   - Implement more robust error handling for audio device issues
   - Add reconnection logic for dropped WebSocket connections
   - Include input device selection capability

2. **Performance Optimization**
   - Consider using `numpy.fft.rfft` instead of `fft` for real signals
   - Implement buffer pooling to reduce memory allocations
   - Add optional downsampling for slower clients

3. **Feature Additions**
   - Add audio device selection capability
   - Implement different window function options
   - Add configurable FFT size and overlap
   - Include audio recording functionality

### Frontend Improvements

1. **Performance**
   - Consider using WebGL for rendering
   - Implement data decimation for long recordings
   - Add frame skipping for slower devices

2. **User Experience**
   - Add zoom and pan capabilities
   - Implement frequency band selection
   - Add different color scheme options
   - Include amplitude threshold controls

3. **Data Management**
   - Add local storage for settings
   - Implement session recording
   - Add data export in various formats

4. **Visualization**
   - Add multiple visualization modes (waterfall, line graph)
   - Implement peak holding
   - Add frequency marker capabilities
   - Include scale customization options

### General Improvements

1. **Configuration**
   - Add configuration file for backend parameters
   - Implement user-adjustable settings
   - Add presets for different use cases

2. **Documentation**
   - Add API documentation
   - Include setup instructions
   - Add usage examples
   - Include troubleshooting guide

3. **Testing**
   - Add unit tests for both frontend and backend
   - Implement integration tests
   - Add performance benchmarks

4. **Security**
   - Implement proper WebSocket authentication
   - Add rate limiting
   - Implement secure data transmission