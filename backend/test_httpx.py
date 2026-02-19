import asyncio
import httpx

async def test_httpx():
    print("Testing httpx...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://www.google.com")
            print(f"Status: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_httpx())
