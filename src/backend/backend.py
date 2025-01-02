from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import numpy as np
from scipy.fft import fft
import asyncio
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AudioProcessor:
    def __init__(self):
        # Audio settings optimized for full spectrum coverage
        self.CHUNK = 4096  # Increased for better frequency resolution
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100  # Standard audio rate
        self.p = None
        self.stream = None
        
        # Calculate frequency bins
        self.freq_bins = self.CHUNK // 2 + 1
        self.frequencies = np.linspace(0, self.RATE/2, self.freq_bins)
        
        # Create Hanning window
        self.window = np.hanning(self.CHUNK)
        
        # Reference level for dB calculation
        self.ref_level = 1e-20

    def start_stream(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
        self.stream = None
        self.p = None

    def get_audio_data(self):
        if not self.stream:
            return None
        
        try:
            # Read audio data
            data = np.frombuffer(
                self.stream.read(self.CHUNK, exception_on_overflow=False),
                dtype=np.float32
            )
            
            # Apply window function
            data = data * self.window
            
            # Compute FFT
            fft_data = np.abs(fft(data)[:self.freq_bins])
            
            # Convert to dB scale with proper reference
            with np.errstate(divide='ignore'):
                db_data = 20 * np.log10(fft_data / max(fft_data.max(), self.ref_level))
            
            # Normalize dB scale from -120dB to 0dB
            db_data = np.clip(db_data, -120, 0)
            normalized_data = (db_data + 120) / 120
            
            # Create frequency info for initial setup
            freq_info = {
                "freqMin": 0,
                "freqMax": self.RATE // 2,
                "binCount": self.freq_bins,
                "dbMin": -120,
                "dbMax": 0,
                "binFreqs": self.frequencies.tolist()
            }
            
            return {
                "type": "audio_data",
                "data": normalized_data.tolist(),
                "freq_info": freq_info
            }

        except Exception as e:
            print(f"Error processing audio: {e}")
            return None

audio_processor = AudioProcessor()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            command = await websocket.receive_text()
            
            if command == "start":
                audio_processor.start_stream()
                # Send initial frequency information
                first_data = audio_processor.get_audio_data()
                if first_data:
                    await websocket.send_json(first_data)
                
                while True:
                    try:
                        data = audio_processor.get_audio_data()
                        if data:
                            await websocket.send_json(data)
                        await asyncio.sleep(0.03)  # ~30 fps
                    except Exception:
                        break
                        
            elif command == "stop":
                audio_processor.stop_stream()
                await websocket.send_json({
                    "type": "status",
                    "message": "Recording stopped"
                })
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        audio_processor.stop_stream()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)