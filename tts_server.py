import random
import numpy as np
import torch
import io
import base64
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import scipy.io.wavfile as wavfile
from chatterbox.tts import ChatterboxTTS


MODEL_PATH = "dl"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)


class TTSRequest(BaseModel):
    text: str
    audio_prompt_path: Optional[str] = None
    exaggeration: float = 0.5
    temperature: float = 0.8
    seed_num: int = 0
    cfg_weight: float = 0.5
    min_p: float = 0.05
    top_p: float = 1.0
    repetition_penalty: float = 1.2
    return_format: str = "wav"  # "wav" or "base64"


class TTSResponse(BaseModel):
    success: bool
    message: str
    sample_rate: Optional[int] = None
    audio_base64: Optional[str] = None


# Global model instance
model = None

app = FastAPI(title="ChatterboxTTS Server", description="Fast TTS API with model persistence")


@app.on_event("startup")
async def load_model():
    global model
    print(f"Loading ChatterboxTTS model on {DEVICE}...")
    #model = ChatterboxTTS.from_pretrained(DEVICE)
    model = ChatterboxTTS.from_local(MODEL_PATH, DEVICE)
    #model = ChatterboxTTS.from_local('checkpoints_lora/merged_model', device='cuda')
    print("Model loaded successfully!")









def generate(text, audio_prompt_path, exaggeration, temperature, seed_num, cfgw, min_p, top_p, repetition_penalty):
    global model
    
    if seed_num != 0:
        set_seed(int(seed_num))

    wav = model.generate(
        text,
        audio_prompt_path=audio_prompt_path,
        exaggeration=exaggeration,
        temperature=temperature,
        cfg_weight=cfgw,
        min_p=min_p,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
    )
    return (model.sr, wav.squeeze(0).numpy())


@app.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Generate audio
        sample_rate, audio_data = generate(
            text=request.text,
            audio_prompt_path=request.audio_prompt_path,
            exaggeration=request.exaggeration,
            temperature=request.temperature,
            seed_num=request.seed_num,
            cfgw=request.cfg_weight,
            min_p=request.min_p,
            top_p=request.top_p,
            repetition_penalty=request.repetition_penalty
        )
        
        if request.return_format == "base64":
            # Convert to base64 for JSON response
            buffer = io.BytesIO()
            wavfile.write(buffer, sample_rate, audio_data)
            audio_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return TTSResponse(
                success=True,
                message="Audio generated successfully",
                sample_rate=sample_rate,
                audio_base64=audio_base64
            )
        else:
            return TTSResponse(
                success=True,
                message="Use /generate_wav endpoint for WAV file response",
                sample_rate=sample_rate
            )
            
    except Exception as e:
        return TTSResponse(
            success=False,
            message=f"Error generating audio: {str(e)}"
        )


@app.post("/generate_wav")
async def generate_tts_wav(request: TTSRequest):
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Generate audio
        sample_rate, audio_data = generate(
            text=request.text,
            audio_prompt_path=request.audio_prompt_path,
            exaggeration=request.exaggeration,
            temperature=request.temperature,
            seed_num=request.seed_num,
            cfgw=request.cfg_weight,
            min_p=request.min_p,
            top_p=request.top_p,
            repetition_penalty=request.repetition_penalty
        )
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio_data)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=generated.wav"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": DEVICE
    }


@app.get("/")
async def root():
    return {
        "message": "ChatterboxTTS Server",
        "endpoints": {
            "/generate": "POST - Generate TTS with JSON response (base64 audio)",
            "/generate_wav": "POST - Generate TTS with WAV file response",
            "/health": "GET - Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 