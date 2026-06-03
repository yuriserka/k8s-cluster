import math
import random
import aiohttp
import asyncio

async def task(session: aiohttp.ClientSession, request_id: str):
  url = "http://localhost:8000/fetch-image?url=https://images.unsplash.com/photo-1579353977828-2a4eab540b9a"
  url = "http://localhost:8000/update-event/9e0e0615-1427-46bd-bd0a-80661ac312b2"
  response = await session.put(url, headers={'X-Request-ID': request_id})
  print(f"response {response.status} for {request_id}")
  return await response.json()

async def main():
  image_key_name_start_idx = 0
  session = aiohttp.ClientSession()

  try:
    while True:
      coros = [
        task(session, f"event_{image_key_name_start_idx + i}")
        for i in range(int(math.ceil(random.uniform(15, 30))))
      ]

      ids = await asyncio.gather(*coros, return_exceptions=True)
      
      next_round_sleep = max(1, random.gauss(2.0, 1.5))
      print(f"sleeping for {next_round_sleep} seconds before next incoming messages")
      await asyncio.sleep(next_round_sleep)

      print(f"processed {len(ids)} calls this round out of {image_key_name_start_idx}")
      image_key_name_start_idx += len(ids)
  finally:
    await session.close()


if __name__ == '__main__':
  asyncio.run(main())