import asyncio
from app.cqrs.queries.flight_queries import FlightQueries
from app.gateway import TravelProvider

async def test():
    async with TravelProvider() as gw:
        q = FlightQueries(gw)
        result = await q.get_user_bookings(1)
        print("Success!")
        print(result)

if __name__ == "__main__":
    asyncio.run(test())
