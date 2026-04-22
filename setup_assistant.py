import openwakeword
import os

print("Downloading wake word models... this may take a minute.")
openwakeword.utils.download_models()

# Verification check
model_path = os.path.join(openwakeword.resources.__path__[0], "models")
models = [f for f in os.listdir(model_path) if f.endswith('.onnx')]

print(f"\n✅ Models located in: {model_path}")
print(f"Available models: {models}")