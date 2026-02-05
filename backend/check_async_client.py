import sys
import os
import asyncio
from httpx import AsyncClient

# Ensure backend dir is in path
sys.path.append(os.getcwd())

async def main():
    try:
        print("Importing app...")
        from app.main import app
        print("App imported. Starting AsyncClient...")
        async with AsyncClient(app=app, base_url="http://test") as ac:
            print("AsyncClient started.")
            response = await ac.get("/health")
            print(f"Health check: {response.status_code}")
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
