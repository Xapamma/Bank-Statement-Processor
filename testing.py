import subprocess
import json
import re

# Full path to Ollama executable
ollama_path = r"C:\Users\Savanna\AppData\Local\Programs\Ollama\ollama.exe"


prompt = "Categorize this transaction as JSON: 'Deposit RoundUp Deposit'"
result = subprocess.run(
    [ollama_path, "chat", "--model", "mistral", "--prompt", prompt],
    capture_output=True,
    text=True
)
print(result.stdout)