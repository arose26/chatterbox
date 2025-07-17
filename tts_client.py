import requests
import json
import base64
import argparse
import time
from pathlib import Path
import re
from datetime import datetime

class TTSClient:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        
    def check_health(self):
        """Check if the server is running and model is loaded"""
        try:
            response = requests.get(f"{self.server_url}/health")
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def generate_tts(self, text, output_file=None, **kwargs):
        """Generate TTS audio"""
        # Prepare request data
        request_data = {
            "text": text,
            **kwargs
        }
        
        if output_file:
            # Get WAV file directly
            response = requests.post(f"{self.server_url}/generate_wav", json=request_data)
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                return {"success": True, "file": output_file}
            else:
                return {"success": False, "error": response.text}
        else:
            # Get base64 response
            request_data["return_format"] = "base64"
            response = requests.post(f"{self.server_url}/generate", json=request_data)
            return response.json()



def process_text(text):
    """Process text to remove extra spaces and newlines"""
    #Remove [01:13:16] timestamps
    text = re.sub(r'\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]', '', text)
    return text



def sanitize_filename(text):
    """Sanitize filename by removing special characters"""
    return re.sub(r'[^A-Za-z0-9]', '', text)



def main():
    parser = argparse.ArgumentParser(description="TTS Client for ChatterboxTTS Server")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--text", type=str, help="Single text to synthesize")
    parser.add_argument("--folder", type=str, help="Output folder for single generation")
    parser.add_argument("--batch_file", type=str, help="File containing texts to batch process")
    
    # TTS parameters
    parser.add_argument("--exaggeration", type=float, default=0.4)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--cfg_weight", type=float, default=0.6)
    parser.add_argument("--min_p", type=float, default=0.05)
    parser.add_argument("--top_p", type=float, default=1.0)
    parser.add_argument("--repetition_penalty", type=float, default=1.2)
    parser.add_argument("--audio_prompt_path", type=str, default=None)
    
    args = parser.parse_args()
    
    # Create client
    client = TTSClient(args.server)
    
    # Check server health
    print("Checking server health...")
    health = client.check_health()
    print(f"Server status: {health}")
    
    if "error" in health:
        print("Server is not accessible. Make sure it's running with: python tts_server.py")
        return
        
    if not health.get("model_loaded", False):
        print("Model is not loaded on the server!")
        return
    
    # Common TTS parameters
    tts_params = {
        "exaggeration": args.exaggeration,
        "temperature": args.temperature,
        "seed_num": args.seed,
        "cfg_weight": args.cfg_weight,
        "min_p": args.min_p,
        "top_p": args.top_p,
        "repetition_penalty": args.repetition_penalty,
        "audio_prompt_path": args.audio_prompt_path
    }
    
    if args.text:
        # Single generation
        print(f"Generating TTS for: {args.text}")
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = args.folder + "/" +current_time + "_" + sanitize_filename(args.text[:40]) + ".wav"
        result = client.generate_tts(args.text, output_file, **tts_params)
        print(f"Result: {result}")
        
    elif args.batch_file:
        # Batch generation
        print(f"Loading texts from {args.batch_file}")
        with open(args.batch_file, 'r') as f:
            texts = [process_text(line.strip()) for line in f if line.strip()]
            texts = [text for text in texts if text != "" and '<' not in text and '>' not in text]
        
        print(f"Processing {len(texts)} texts...")
        results = client.batch_generate(texts, args.output_dir, **tts_params)
        
        # Print summary
        successful = sum(1 for r in results if r["result"].get("success", False))
        print(f"\nSummary: {successful}/{len(texts)} generations successful")
        
    else:
        print("Please provide either --text for single generation or --batch_file for batch processing")


if __name__ == "__main__":
    main() 