"""
Sample WebSocket streaming client to test the backend /ws/translate endpoint.
Run this script while the FastAPI server is running:
    python test_client.py
"""

import asyncio
import base64
import json
import struct
import websockets


def generate_synthetic_pcm_chunk(sample_rate=16000, duration_sec=0.2, frequency=440.0) -> bytes:
    """Generates synthetic 16-bit mono PCM audio chunk."""
    import math
    num_samples = int(sample_rate * duration_sec)
    frames = bytearray()
    for i in range(num_samples):
        t = float(i) / sample_rate
        sample = int(8000.0 * math.sin(2.0 * math.pi * frequency * t))
        frames.extend(struct.pack("<h", sample))
    return bytes(frames)


async def test_live_translation():
    uri = "ws://localhost:8000/ws/translate"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        print("[CONNECTED] WebSocket connection established.")

        # 1. Send start
        start_msg = {
            "type": "start",
            "source_language": "ta",
            "target_language": "en",
            "enable_tts": True,
        }
        await ws.send(json.dumps(start_msg))
        print(f"[SENT] start message: {start_msg}")

        # Receive start response
        resp = await ws.recv()
        print(f"[RECV] {resp}")

        # 2. Stream 4 audio chunks simulating incoming speech
        for chunk_idx in range(1, 5):
            await asyncio.sleep(0.3)
            is_last = (chunk_idx == 4)
            pcm_chunk = generate_synthetic_pcm_chunk()
            b64_data = base64.b64encode(pcm_chunk).decode("ascii")

            audio_msg = {
                "type": "audio",
                "data": b64_data,
                "seq_id": chunk_idx,
                "is_last": is_last,
            }
            await ws.send(json.dumps(audio_msg))
            print(f"\n[SENT] audio chunk #{chunk_idx} (is_last={is_last})")

            # Read responses for this chunk until latency message arrives
            while True:
                msg_str = await ws.recv()
                data = json.loads(msg_str)
                event_type = data.get("type")
                print(f"  -> [{event_type.upper()}] {msg_str[:120]}...")
                if event_type in ("latency", "error"):
                    break

        # 3. Send stop
        await asyncio.sleep(0.5)
        stop_msg = {"type": "stop"}
        await ws.send(json.dumps(stop_msg))
        print(f"\n[SENT] stop message")
        final_resp = await ws.recv()
        print(f"[RECV] Final: {final_resp}")


if __name__ == "__main__":
    try:
        asyncio.run(test_live_translation())
    except ConnectionRefusedError:
        print("\n[ERROR] Could not connect to ws://localhost:8000/ws/translate.")
        print("Please ensure the FastAPI server is running: 'uvicorn app.main:app --port 8000'")
