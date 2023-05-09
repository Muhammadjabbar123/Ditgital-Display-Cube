import asyncio
from bleak import BleakScanner

async def main():
  async with BleakScanner() as scanner:
      devices = await scanner.discover()
      return devices
def devices_found():

    temp = asyncio.run(main())
    print(temp)
    return temp