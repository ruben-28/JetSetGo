import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

import huggingface_hub
print(f"Hugging Face Hub Version: {huggingface_hub.__version__}")

# Assuming the token is in env or we can try without if it's a public model, 
# but usually we need one for inference api if rate limited.
# I'll rely on the environment variable being present or the user providing it if the script fails.
# The user's code uses "HF_API_TOKEN"

try:
    token = os.environ.get("HF_API_TOKEN")
    if not token:
        print("Warning: HF_API_TOKEN not found in env, trying without token (might fail)")
    
    client = InferenceClient(provider="hf-inference", api_key=token)
    
    text = "Find me a flight to Paris"
    candidates = [
        "flight_search", "hotel_search", "package_search",
        "booking_history", "budget_advice", "inspiration", "general"
    ]
    model = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    
    print(f"Testing model: {model}")
    print(f"Text: {text}")
    print(f"Candidates: {candidates}")

    result = client.zero_shot_classification(
        text,
        candidates,
        model=model
    )
    
    print("Success!")
    print(result)

except Exception as e:
    print("\nCaught Exception:")
    print(e)
