from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Depends
import os
import tempfile
import aiofiles
from app.config import settings
from app.dependencies import get_router_service
from app.services.router import RouterService
from app.core.providers import PROVIDER_REGISTRY

router = APIRouter()

@router.post("/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    language: str = Form("vi"),
    router_svc: RouterService = Depends(get_router_service),
):
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

        normalized_language = "en" if language.lower().startswith("en") else "vi"
        transcription_prompt = (
            "This is an English learner speaking. Preserve filler words and possible recognition mistakes."
            if normalized_language == "en"
            else "Đây là câu nói tiếng Việt."
        )

        audio_chain = ["groq", "openai"]
        success = False
        last_error = None
        text = ""

        for provider_key in audio_chain:
            provider = PROVIDER_REGISTRY.get(provider_key)
            if not provider or not router_svc._has_api_key(provider):
                continue

            model = "whisper-large-v3" if provider_key == "groq" else "whisper-1"
            try:
                client = router_svc.get_client(provider)
                with open(temp_path, "rb") as audio_file:
                    transcription = await client.audio.transcriptions.create(
                        file=audio_file,
                        model=model,
                        language=normalized_language,
                        temperature=0.0,
                        prompt=transcription_prompt,
                        response_format="json"
                    )
                text = transcription.text.strip()
                success = True
                break
            except Exception as e:
                last_error = str(e)
                continue

        if not success:
            raise HTTPException(status_code=500, detail=f"All STT providers failed. Last error: {last_error}")

        # Lọc bỏ các kết quả bịa đặt thường gặp của Whisper
        if not text or text in ["1", "1.", "Đây là câu nói tiếng Việt.", transcription_prompt]:
            return {"text": ""}

        return {"text": text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    router_svc: RouterService = websocket.app.state.router_service

    try:
        while True:
            data = await websocket.receive_bytes()
            temp_path = None
            try:
                # Detect audio format from magic bytes
                suffix = ".webm"
                if data[:4] == b'\x1aE\xdf\xa3':  # webm
                    suffix = ".webm"
                elif b'ftyp' in data[:32]:  # mp4
                    suffix = ".mp4"

                fd, temp_path = tempfile.mkstemp(suffix=suffix)
                os.close(fd)

                async with aiofiles.open(temp_path, "wb") as temp_file:
                    await temp_file.write(data)

                # Failover audio chain
                audio_chain = ["groq", "openai"]
                success = False
                last_error = None
                text = ""

                for provider_key in audio_chain:
                    provider = PROVIDER_REGISTRY.get(provider_key)
                    if not provider or not router_svc._has_api_key(provider):
                        continue

                    model = "whisper-large-v3" if provider_key == "groq" else "whisper-1"
                    try:
                        client = router_svc.get_client(provider)
                        with open(temp_path, "rb") as audio_file:
                            transcription = await client.audio.transcriptions.create(
                                file=audio_file,
                                model=model,
                                language="vi",
                                temperature=0.0,
                                prompt="Đây là câu nói tiếng Việt.",
                                response_format="json"
                            )
                        text = transcription.text.strip()
                        success = True
                        break
                    except Exception as e:
                        last_error = str(e)
                        continue

                if success:
                    # Lọc bỏ các kết quả bịa đặt thường gặp của Whisper
                    if text and text not in ["1", "1.", "Đây là câu nói tiếng Việt."]:
                        await websocket.send_json({"text": text})
                else:
                    await websocket.send_json({"error": f"Transcription failed: {last_error}"})

            except Exception as e:
                print(f"WebSocket STT Error: {e}")
                await websocket.send_json({"error": str(e)})
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
    except WebSocketDisconnect:
        print("Client disconnected from audio stream")
