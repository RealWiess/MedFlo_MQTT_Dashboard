import asyncio
from bleak import BleakScanner

async def run():
    print("Starting BLE scan for 10 seconds...")
    print("Looking for any MAC starting with F44E or F4:4E...")
    
    def callback(device, adv):
        mac = device.address.upper()
        if mac.startswith("F4:4E") or mac.startswith("F44E"):
            print(f"\n[FOUND!] MAC: {mac}")
            print(f"Name: {device.name}")
            print(f"RSSI: {adv.rssi}")
            print(f"Manufacturer Data: {adv.manufacturer_data}")
            print(f"Service Data: {adv.service_data}")
            print("-" * 40)
            
    scanner = BleakScanner(callback)
    await scanner.start()
    await asyncio.sleep(10.0)
    await scanner.stop()
    print("Scan finished.")

if __name__ == "__main__":
    asyncio.run(run())
