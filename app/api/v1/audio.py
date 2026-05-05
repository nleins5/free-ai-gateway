from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
import os
import tempfile
import aiofiles
from app.config import settings

router = APIRouter()

@router.post("/transcriptions")
async def create_transcription(file: UploadFile = File(...)):
    groq_api_key = settings.groq_api_key
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in configuration")
        
    client = AsyncOpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
    
    # Using tempfile and aiofiles to avoid blocking the event loop
    temp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".webm"
        # Create a named temporary file and get its path, then close it immediately
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        
        async with aiofiles.open(temp_path, "wb") as temp_file:
            # Read in chunks to avoid loading large files into memory
            while chunk := await file.read(8192):
                await temp_file.write(chunk)
                
        with open(temp_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="json"
            )
            
        return {"text": transcription.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    nvidia_api_key = settings.nvidia_api_key or os.getenv("NVIDIA_API_KEY")
    if not nvidia_api_key:
        await websocket.close(code=1011)
        return

    try:
        while True:
            data = await websocket.receive_bytes()
            temp_path = None
            try:
                fd, temp_path = tempfile.mkstemp(suffix=".webm")
                os.close(fd)

                async with aiofiles.open(temp_path, "wb") as temp_file:
                    await temp_file.write(data)

                # Call NVIDIA transcription API
                import httpx
                async with httpx.AsyncClient() as client:
                    with open(temp_path, "rb") as audio_file:
                        response = await client.post(
                            "https://integrate.api.nvidia.com/v1/audio/transcriptions",
                            headers={"Authorization": f"Bearer {nvidia_api_key}"},
                            files={"file": (temp_path, audio_file, "audio/webm")},
                            data={"model": "whisper-large-v3"}
                        )

                    if response.status_code == 200:
                        result = response.json()
                        await websocket.send_json({"text": result.get("text", "")})
                    else:
                        await websocket.send_json({"error": f"NVIDIA API error: {response.text}"})
            except Exception as e:
                print(f"WebSocket STT Error: {e}")
                await websocket.send_json({"error": str(e)})
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
    except WebSocketDisconnect:
        print("Client disconnected from audio stream")
