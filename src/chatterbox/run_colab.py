try:
    import IPython
    from google.colab import files
except:
    pass
import torch
import os
import torchaudio
import shutil
import chatterbox
import re
import scipy.io.wavfile as wavfile
import io
from pydub import AudioSegment
import requests
import time
#!pip install git+https://github.com/arose26/chatterbox.git

def chatterbox_to(model, device, dtype):
    print(f"Moving model to {str(device)}, {str(dtype)}")
    model.ve.to(device=device)
    model.t3.to(device=device, dtype=dtype)
    model.s3gen.to(device=device, dtype=dtype)
    # due to "Error: cuFFT doesn't support tensor of type: BFloat16" from torch.stft
    model.s3gen.tokenizer.to(dtype=torch.float32)
    model.conds.to(device=device)
    model.device = device
    torch.cuda.empty_cache()
    return model



def get_model( model_name="just_a_placeholder", device=torch.device("cuda"), dtype=torch.float32):
    from chatterbox.tts import ChatterboxTTS
    model = ChatterboxTTS.from_pretrained(device)
    #model = ChatterboxTTS.from_("/content/dl", device)
    return chatterbox_to(model, device, dtype)





def concat_mp3s(input_filenames, output_filename='concat.wav'):
  # List your MP3 filenames here
  #mp3_files = ['file1.mp3', 'file2.mp3', 'file3.mp3']  # Replace with your files

  # Start with an empty audio segment
  combined = AudioSegment.empty()

  # Concatenate all wav files
  for input_file in input_filenames:
      audio = AudioSegment.from_wav(input_file)
      combined += audio

  # Export the result to 'concat.mp3'
  combined.export(output_filename, format='wav')


def process_text(text):
    """Process text to remove extra spaces and newlines"""
    #Remove [01:13:16] timestamps
    text = re.sub(r'\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]', '', text.strip())
    text = text.replace(" ok ", " OK ").replace(" im ", " I'm ")
    return text

def sanitize_filename(filename, replacement=""):
    # Remove invalid characters
    sanitized = re.sub(r'[^a-zA-Z]', '', filename)
    return sanitized[:30]


####
# For really long sentences (>350 chars), generate them independently then concat the mp3
###

def split_sentences(text):
    # Splits on period or ellipsis or question mark followed by space or end of string
    pattern = re.compile(r'(.*?(?:\.|\?)+)')
    sentences = pattern.findall(text)
    print(sentences)
    if not sentences:
        # Fallback: split on period
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
    return sentences

def group_sentences(sentences, max_len=350):
    chunks = []
    current_chunk = ''
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_len:
            current_chunk += sentence + ' '
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def generate(input_text="Hi there.", index=None):
    filename = sanitize_filename(input_text) + '.wav'
    if index:
        filename = str(index) + '.' + filename


    # Get the directory where the current file resides
    current_file_dir = os.path.dirname(os.path.realpath(__file__))



    #kwargs same as local
    kwargs = dict(repetition_penalty=1.2,
        min_p=0.05,
        top_p=1.0,
        exaggeration=0.4, cfg_weight=0.6,
        audio_prompt_path=os.path.join(current_file_dir, "reference_long.mp3"),
        temperature=0.8)

    if len(input_text) <= 350:
        audio = list(model.generate(input_text, **kwargs))[0]
        if audio.ndim == 1:
          audio = audio.unsqueeze(0)
        torchaudio.save(filename, audio, 24000)
        files.download(filename)
        return

    #New - long passage support
    sentences = split_sentences(input_text)
    chunks = group_sentences(sentences, max_len=350)

    temp_files = []
    for i, chunk in enumerate(chunks):
        audio = list(model.generate(chunk, **kwargs))[0]
        if audio.ndim == 1:
          audio = audio.unsqueeze(0)
        temp_filename = f"temp_{i}.wav"
        torchaudio.save(temp_filename, audio, 24000)
        temp_files.append(temp_filename)

    concat_mp3s(temp_files)

    if os.path.exists('concat.wav'):
        shutil.move('concat.wav', filename)
        files.download(filename)
    else:
        print("Error: concat.wav not found")

    for f in temp_files:
        os.remove(f)


def run():
    global model
    try:
        assert model is not None
    except:
        model = get_model(model_name="just_a_placeholder", device=torch.device("cuda"), dtype=torch.float32 )
    #list(model.generate("""test."""))
    
    
    #url = "https://pastebin.com/raw/13kcemCK"  # Use the raw link for plain text
    #url_with_cachebust = f"{url}?cachebust={int(time.time())}"
    #response = requests.get(url_with_cachebust)
    
   # response.raise_for_status()  # Raise an error if the request failed
    #lines = response.text.splitlines()


    with open('narration.txt', 'r') as f:
        texts = [process_text(line) for line in f if line]

    for i, text in enumerate(texts):
        generate(text, i+1)
