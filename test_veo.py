import os
from google import genai
from google.genai import types

api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing files...")
files = list(client.files.list())
if not files:
    print("No files found on Gemini.")
    exit(1)

f1 = files[-1]
print(f"Using file: {f1.name} URI: {f1.uri}")

try:
    source = types.GenerateVideosSource(
        image=f1
    )
    print("Source Image Assigned directly to File object")
except Exception as e:
    print("Cannot assign File directly to source.image:", e)

try:
    ref = types.VideoGenerationReferenceImage(
        reference_type="ASSET",
        image=f1
    )
    print("Reference Assigned directly to File object")
except Exception as e:
    print("Cannot assign File directly to reference.image:", e)
