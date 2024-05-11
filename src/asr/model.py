import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import config as cfg
import json


device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

print(f'Model is using {"CUDA ..." if torch.cuda.is_available() else "CPU ..."}')

model_id = "openai/whisper-large-v3"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
    cache_dir=cfg.MODEL_PATH,
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=30,
    batch_size=16,
    return_timestamps=True,
    torch_dtype=torch_dtype,
    device=device,
)

# dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
# sample = dataset[0]["audio"]

# result = pipe(sample)
result = pipe(f"{cfg.AUDIO_RAW_PATH}/{cfg.TWO_PEOPLE_ID}.mp3")
print(result)
with open(f"{cfg.PATH}/results/{cfg.TWO_PEOPLE_ID}.json", "w+") as f:
    json.dump(result, f, indent=2)
