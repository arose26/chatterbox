import os
import shutil
import re
import torchaudio
from tts_server import model
from chatterbox.tts import ChatterboxTTS




model = ChatterboxTTS.from_pretrained("cuda")

import re
def process_text(text):
    """Process text to remove extra spaces and newlines"""
    #Remove [01:13:16] timestamps
    text = re.sub(r'\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]', '', text.strip())
    text = text.replace('hte', 'the').replace('ok','okay').replace('okayay','okay').replace('look','luck')
    return text

def sanitize_filename(filename, replacement=""):
    # Remove invalid characters
    sanitized = re.sub(r'[^a-zA-Z]', '', filename)
    return sanitized[:96]


####
# For really long sentences (>350 chars), generate them independently then concat the mp3
###
import scipy.io.wavfile as wavfile
import io
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

def generate(input_text="Hi, my jock strap fell off.", index=None):
    filename = sanitize_filename(input_text) + '.wav'
    if index:
        filename = str(index) + '.' + filename

    #kwargs same as local
    kwargs = dict(repetition_penalty=1.2,
        min_p=0.05,
        top_p=1.0,
        exaggeration=0.35, cfg_weight=0.65, audio_prompt_path="reference_long.mp3",
        temperature=0.8)
    
    if len(input_text) <= 350:
        audio = list(model.generate(input_text, **kwargs))[0]
        if audio.ndim == 1:
          audio = audio.unsqueeze(0)
        torchaudio.save(filename, audio, 24000)

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


with open('narration.txt', 'r') as f:
  texts = [process_text(line) for line in f if line]
#For texts over 350 characters, we find the last sentence and split it into a new line
for i, text in enumerate(texts):
    generate(text, i+1)
    
