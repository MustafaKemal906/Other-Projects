#!/usr/bin/env python3

import asyncio
import aiohttp
import json
from mavsdk import System

async def run():
    # Drone 1 setup
    drone1 = System()
    await drone1.connect(system_address="udp://:14541")
    asyncio.ensure_future(process_drone_telemetry(drone1, "Drone 1", "http://0.0.0.0:5000/api/telemetri_gonder"))

    # Drone 2 setup
    drone2 = System()
    await drone2.connect(system_address="udp://:14542")
    asyncio.ensure_future(process_drone_telemetry(drone2, "Drone 2", "http://0.0.0.0:5000/api/telemetri_gonder"))

    while True:
        await asyncio.sleep(1)

async def process_drone_telemetry(drone, drone_name, server_address):
    telemetry_data = {}

    async def print_and_store_data(data_type, data):
        telemetry_data[data_type] = data
        print(f"{drone_name} {data_type}: {data}")

    async def send_data():
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    payload = {"drone_name": drone_name, "telemetry": telemetry_data}
                    async with session.post(server_address, json=payload) as response:
                        if response.status == 200:
                            server_response = await response.text()
                            print(f"{drone_name} Server Response: {server_response}")
                        else:
                            print(f"{drone_name} Error sending telemetry: Status code {response.status}")
                            error_text = await response.text()
                            print(f"{drone_name} Error content: {error_text}")
                except aiohttp.ClientError as e:
                    print(f"{drone_name} Connection error: {e}")
                await asyncio.sleep(1)

    async def get_battery(drone):
        async for battery in drone.telemetry.battery():
            print_and_store_data("battery", battery.remaining_percent)

    async def get_gps_info(drone):
        async for gps_info in drone.telemetry.gps_info():
            print_and_store_data("gps_info", {"num_satellites": gps_info.num_satellites, "fix_type": gps_info.fix_type.value})

    async def get_in_air(drone):
        async for in_air in drone.telemetry.in_air():
            print_and_store_data("in_air", in_air)

    async def get_position(drone):
        async for position in drone.telemetry.position():
            print_and_store_data("position", {"latitude_deg": position.latitude_deg, "longitude_deg": position.longitude_deg, "absolute_altitude_m": position.absolute_altitude_m, "relative_altitude_m": position.relative_altitude_m})


    asyncio.ensure_future(get_battery(drone))
    asyncio.ensure_future(get_gps_info(drone))
    asyncio.ensure_future(get_in_air(drone))
    asyncio.ensure_future(get_position(drone))
    asyncio.ensure_future(send_data())



if __name__ == "__main__":
    asyncio.run(run())