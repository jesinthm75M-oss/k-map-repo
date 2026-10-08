# Live Translation for Indic Languages - Backend

Modular, production-ready asynchronous backend for real-time speech translation across Indic languages (Tamil, Hindi, Telugu, Kannada, Malayalam) and English. Built for **HACKNEX 2026**.

---

## 1. Pipeline Architecture

```
Microphone
    │
    ▼
[Streaming Audio Chunks (PCM 16kHz Mono)]
    │
    ▼
[VAD (Voice Activity Detection)] ──(Silence)──> [Skip heavy stages / emit WAIT]
    │ (Speech detected)
    ▼
[Streaming ASR Engine] ──> Partial / Final Hypothesis
    │
    ▼
[Language ID & Code-Mixing Detection] ──> Script distribution & bilingual check
    │
    ▼
[Adaptive Decision Agent] ───────────────┐
    ├── WAIT      (insufficient context) ──┴──> Client notified (awaits next audio chunk)
    ├── TRANSLATE (stable clause / boundary)
    └── CORRECT   (semantic reversal / homograph update)
            │
            ▼
[Machine Translation (IndicTrans2 Adapter)]
            │
            ▼
[Translation Stabilization & Correction Service] ──> Emits correction event with segment_id
            │
            ▼
[Optional Voice-Preserving TTS Engine]
            │
            ▼
[WebSocket Live Output Stream to Client]
```

---

## 2. Folder Structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI application factory & router mounting
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Pydantic BaseSettings (.env loading)
│   │   └── logging.py                   # Privacy-safe structured logging (no raw audio logged)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py                # GET /health
│   │   │   ├── languages.py             # GET /languages
│   │   │   ├── translate.py             # POST /translate (one-shot REST)
│   │   │   ├── tts.py                   # POST /voice/enroll & POST /voice/generate
│   │   │   └── sessions.py              # POST /session/create & GET /session/{session_id}
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── translation_ws.py        # WS /ws/translate live bidirectional streaming
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py              # Pipeline orchestrator managing stages & events
│   │   ├── session_manager.py           # In-memory async session store & lifecycle
│   │   ├── state_machine.py             # Session lifecycle state machine
│   │   └── latency.py                   # High-precision time.perf_counter() latency tracker
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── decision_agent.py            # WAIT / TRANSLATE / CORRECT decision agent
│   │   ├── language_agent.py            # Code-mixing & language switch detector
│   │   └── correction_agent.py          # Translation revision difference evaluator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── asr/
│   │   │   ├── __init__.py
│   │   │   └── streaming_asr.py         # BaseStreamingASR & DevStreamingASRAdapter
│   │   ├── translation/
│   │   │   ├── __init__.py
│   │   │   └── indictrans.py            # BaseIndicTranslationModel & DevIndicTransAdapter
│   │   ├── tts/
│   │   │   ├── __init__.py
│   │   │   └── voice_tts.py             # BaseVoiceTTSModel & DevVoiceTTSAdapter
│   │   ├── voice/
│   │   │   ├── __init__.py
│   │   │   └── speaker_embedding.py     # BaseSpeakerEmbeddingModel & DevSpeakerEmbeddingAdapter
│   │   └── vad/
│   │       ├── __init__.py
│   │       └── vad.py                   # BaseVADModel & DevVADAdapter
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_service.py             # Base64 audio decoding, chunk validation, RMS
│   │   ├── language_detection.py        # Indic script & Unicode lexical language detection
│   │   ├── translation_service.py       # Indic translation dispatcher & language validation
│   │   ├── voice_service.py             # Speaker enrollment (with consent) & TTS synthesis
│   │   └── correction_service.py        # Translation stabilization & revision emitter
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── websocket.py                 # Client & Server WebSocket Pydantic models
│   │   ├── translation.py               # REST translation & voice request/response schemas
│   │   └── session.py                   # Session state schemas
│   └── utils/
│       ├── __init__.py
│       ├── audio.py                     # Audio bytes, RMS energy, and WAV header builders
│       ├── text.py                      # Text cleaning, sentence bounds, Unicode ranges
│       └── timestamps.py                # Monotonic timing & ISO utilities
├── tests/
│   ├── __init__.py
│   ├── test_health.py                   # Health, languages, and latency tests
│   ├── test_agent.py                    # Decision agent, language detection, correction tests
│   ├── test_translation.py              # Translation service, REST translate, session lifecycle
│   └── test_websocket.py                # WebSocket connection, audio stream, and error tests
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
└── README.md
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)

### 1. Create and Activate Virtual Environment
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or
cp .env.example .env     # Linux / macOS
```

Available environment variables:
| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind host address |
| `PORT` | `8000` | Bind port |
| `DEBUG` | `false` | Enable auto-reload |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ASR_MODEL` | `mock-asr` | ASR model identifier / adapter selection |
| `TRANSLATION_MODEL` | `mock-indictrans2` | Translation adapter selection |
| `TTS_MODEL` | `mock-tts` | TTS model identifier |
| `AI_ENDPOINT` | None | Optional external inference endpoint |
| `AI_API_KEY` | None | API Key (never hardcode in code) |
| `VAD_ENERGY_THRESHOLD` | `0.01` | Minimum RMS energy to register speech |

---

## 4. Starting the Server

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or running app/main.py directly
python -m app.main
```

Interactive OpenAPI Swagger UI is available at:
`http://localhost:8000/docs`

---

## 5. WebSocket Endpoint & Message Protocol

WebSocket endpoint:
```
ws://localhost:8000/ws/translate
```

### Client → Server Messages

#### 1. Start Session (`start`)
```json
{
  "type": "start",
  "source_language": "ta",
  "target_language": "en",
  "enable_tts": false
}
```

#### 2. Send Audio Chunk (`audio`)
```json
{
  "type": "audio",
  "data": "<BASE64_ENCODED_PCM16_16KHZ_BYTES>",
  "seq_id": 1,
  "is_last": false
}
```

#### 3. Change Language on the Fly (`change_language`)
```json
{
  "type": "change_language",
  "source_language": "hi",
  "target_language": "en"
}
```

#### 4. Stop Session (`stop`)
```json
{
  "type": "stop"
}
```

---

### Server → Client Messages

| Event Type | Purpose | Example Payload |
|---|---|---|
| `session_started` | Confirms session ID & active language pair | `{"type": "session_started", "session_id": "...", "source_language": "ta", "target_language": "en"}` |
| `vad` | Real-time speech activity probability | `{"type": "vad", "is_speech": true, "speech_prob": 0.88}` |
| `transcript` | Partial or final speech-to-text hypothesis | `{"type": "transcript", "segment_id": "seg_1", "text": "நான் வங்கித் தேர்வு", "is_final": false}` |
| `language` | Identified language & code-mixing flag | `{"type": "language", "language": "ta", "confidence": 0.95, "code_mixed": false}` |
| `decision` | Agent decision with explicit rationale | `{"type": "decision", "decision": "TRANSLATE", "reason": "Terminal punctuation encountered"}` |
| `translation` | Translated segment | `{"type": "translation", "segment_id": "seg_1", "source_text": "...", "translated_text": "I am writing a bank exam."}` |
| `correction` | Stabilized correction replacing earlier translation | `{"type": "correction", "affected_segment_id": "seg_1", "original_translation": "I am going to the bank.", "corrected_translation": "I am writing a bank exam.", "reason": "Contextual revision"}` |
| `audio` | Synthesized TTS WAV audio (if `enable_tts` was true) | `{"type": "audio", "segment_id": "seg_1", "audio_base64": "...", "format": "wav", "sample_rate": 16000}` |
| `latency` | High-precision stage-by-stage timings | `{"type": "latency", "metrics": {"asr_latency_ms": 14.2, "agent_latency_ms": 1.1, "translation_latency_ms": 18.5, "end_to_end_latency_ms": 38.6}}` |
| `error` | Resilient error event (never crashes socket) | `{"type": "error", "code": "UNSUPPORTED_LANGUAGE", "message": "..."}` |
| `session_finished`| Final session summary upon stop | `{"type": "session_finished", "session_id": "...", "summary": {...}}` |

---

## 6. How the Adaptive Decision Agent Works

The Adaptive Decision Agent (`app/agents/decision_agent.py`) is designed specifically for low-latency streaming speech translation where words arrive incrementally.

It returns strictly one of:
1. `WAIT`
   - Triggered when the current utterance is too short (< 2 words), the ASR confidence is low (< 0.65), or speech is actively mid-clause without syntactic closure.
   - Prevents emitting premature, jerky, or half-translated outputs.
2. `TRANSLATE`
   - Triggered when:
     - Sentence boundary or terminal punctuation (`.`, `!`, `?`, `।`, `॥`) is encountered.
     - VAD detects a speech pause after a complete phrase.
     - `is_final` flag is signaled by the client/ASR.
     - Contextual clause threshold (>= 5 words with high ASR confidence) is achieved.
3. `CORRECT`
   - Triggered when newly arrived tokens fundamentally change the meaning of a previously translated segment (such as polysemy disambiguation or late-arriving negation).
   - **Example**:
     - *Early chunk*: "நான் வங்கிக்குச்..." translated to *"I am going to the bank."*
     - *Subsequent chunk*: "...தேர்வு எழுதுகிறேன்" (exam writing) disambiguates "வங்கி" (bank) into *"bank exam"*.
     - The agent issues `CORRECT` with reason `Semantic disambiguation: 'bank' shifted context by 'exam'`, and `CorrectionService` emits a `correction` event containing the affected `segment_id`.

---

## 7. Replacing Development Adapters with Real AI Models

Every AI model is isolated behind an **Abstract Base Class (ABC)**. To plug in real neural models, create your implementation and swap it in the service or orchestrator:

### 1. Streaming ASR (`app/models/asr/streaming_asr.py`)
Replace `DevStreamingASRAdapter` with your Whisper / NeMo / IndicConformer pipeline:
```python
from app.models.asr.streaming_asr import BaseStreamingASR, ASRResult

class RealWhisperStreamingASR(BaseStreamingASR):
    def __init__(self, model_size: str = "medium"):
        import whisper
        self.model = whisper.load_model(model_size)
        self.buffer = bytearray()

    async def process_audio_chunk(self, audio_bytes: bytes, language: str = "ta", is_last: bool = False) -> ASRResult:
        # Pass audio_bytes to streaming feature extractor
        ...
        return ASRResult(text=transcription, is_final=is_last, confidence=0.94, duration_ms=..., is_development_adapter=False)

    async def reset(self) -> None:
        self.buffer.clear()
```

### 2. IndicTrans2 Machine Translation (`app/models/translation/indictrans.py`)
Replace `DevIndicTransAdapter` with AI4Bharat IndicTrans2:
```python
from app.models.translation.indictrans import BaseIndicTranslationModel, TranslationResult

class IndicTrans2Model(BaseIndicTranslationModel):
    def __init__(self, checkpoint_path: str):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint_path, trust_remote_code=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint_path, trust_remote_code=True).to("cuda")

    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> TranslationResult:
        # Preprocess with IndicProcessor & generate
        ...
        return TranslationResult(source_text=text, translated_text=output, source_language=src_lang, target_language=tgt_lang, confidence=0.98, model_name="indictrans2-1B", is_development_adapter=False)
```
Then in `app/services/translation_service.py`:
```python
translation_service.set_adapter(IndicTrans2Model("/path/to/weights"))
```

### 3. Voice Enrollment & TTS (`app/models/voice/` and `app/models/tts/`)
- In `app/models/voice/speaker_embedding.py`: implement `BaseSpeakerEmbeddingModel` using **ECAPA-TDNN** (SpeechBrain) or **pyannote.audio**.
- In `app/models/tts/voice_tts.py`: implement `BaseVoiceTTSModel` using **Indic-TTS** or **Coqui XTTS v2** for voice cloning with the speaker embedding.

---

## 8. Running Tests

```bash
# Run entire test suite
pytest tests -v

# Run specific test modules
pytest tests/test_websocket.py -v
pytest tests/test_agent.py -v
```
