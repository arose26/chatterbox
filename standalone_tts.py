import random
import numpy as np
import torch
import scipy.io.wavfile as wavfile
import argparse
from chatterbox.tts import ChatterboxTTS


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)


def load_model():
    model = ChatterboxTTS.from_pretrained(DEVICE)
    return model


def generate(model, text, audio_prompt_path, exaggeration, temperature, seed_num, cfgw, min_p, top_p, repetition_penalty):
    if model is None:
        model = ChatterboxTTS.from_pretrained(DEVICE)

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


def main():
    parser = argparse.ArgumentParser(description="Standalone TTS using ChatterboxTTS")
    parser.add_argument("--text", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--output", type=str, default="output.wav", help="Output audio file path")
    parser.add_argument("--ref_audio", type=str, default=None, help="Reference audio file path")
    parser.add_argument("--exaggeration", type=float, default=0.5, help="Exaggeration factor (default: 0.5)")
    parser.add_argument("--temperature", type=float, default=0.8, help="Temperature (default: 0.8)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (0 for random)")
    parser.add_argument("--cfg_weight", type=float, default=0.5, help="CFG weight (default: 0.5)")
    parser.add_argument("--min_p", type=float, default=0.05, help="Min p (default: 0.05)")
    parser.add_argument("--top_p", type=float, default=1.0, help="Top p (default: 1.0)")
    parser.add_argument("--repetition_penalty", type=float, default=1.2, help="Repetition penalty (default: 1.2)")
    
    args = parser.parse_args()
    
    print(f"Loading model on {DEVICE}...")
    model = load_model()
    
    print(f"Generating audio for text: '{args.text}'")
    sample_rate, audio_data = generate(
        model=model,
        text=args.text,
        audio_prompt_path=args.ref_audio,
        exaggeration=args.exaggeration,
        temperature=args.temperature,
        seed_num=args.seed,
        cfgw=args.cfg_weight,
        min_p=args.min_p,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty
    )
    
    print(f"Saving audio to {args.output}...")
    wavfile.write(args.output, sample_rate, audio_data)
    print(f"Audio saved successfully to {args.output}")


if __name__ == "__main__":
    main() 