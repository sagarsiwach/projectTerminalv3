import asyncio
import httpx
from bs4 import BeautifulSoup
from config import read_config
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable httpx logging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

# Read configuration from the CSV file
config = read_config()

# Base URL for the website
base_url = "https://gotravspeed.com"

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': base_url,
    'Upgrade-Insecure-Requests': '1'
}

async def login():
    # Create a new client instance for each login attempt
    async with httpx.AsyncClient() as client:
        # Step 1: Navigate to the main page
        response = await client.get(base_url, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to access the main page")
            raise Exception("Failed to access the main page")

        # Step 2: Submit login credentials
        login_data = {
            'name': 'scar',
            'password': 'satkabir'
        }
        response = await client.post(base_url, data=login_data, headers=headers)
        if "Login failed" in response.text:
            logger.error("Login failed")
            raise Exception("Login failed")
        else:
            logger.info("Login successful")

        # Step 3: Navigate to the server selection page
        response = await client.get(base_url + "/game/servers", headers=headers)
        if response.status_code != 200:
            logger.error("Failed to access the server selection page")
            raise Exception("Failed to access the server selection page")

        # Step 4: Select a server (server ID 9 in this example)
        server_data = {
            'action': 'server',
            'value': '9'
        }
        response = await client.post(base_url + "/game/servers", data=server_data, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to select server")
            raise Exception("Failed to select server")

        # Step 5: Log in to the selected server
        server_login_data = {
            'action': 'serverLogin',
            'value[pid]': '9',
            'value[server]': '9'
        }
        response = await client.post(base_url + "/game/servers", data=server_login_data, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to log in to server")
            raise Exception("Failed to log in to server")

        # Step 6: Access a specific page in the game (e.g., village1.php)
        response = await client.get("https://fun.gotravspeed.com/village1.php", headers=headers)
        if response.status_code != 200:
            logger.error("Failed to access the game page")
            raise Exception("Failed to access the game page")

        logger.info("Successfully logged in and accessed the game page")
        # Return the cookies from the new client instance
        return client.cookies


    

async def construct_and_upgrade_building(cookies, village_id, building_id, loops):
    async with httpx.AsyncClient(cookies=cookies) as client:
        for _ in range(loops):
            try:
                construction_page_url = f"https://fun.gotravspeed.com/build.php?id={village_id}"
                response = await client.get(construction_page_url)
                if response.status_code != 200:
                    logging.error(f"Failed to access the construction page at {construction_page_url}. Status code: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                build_link = soup.find('a', class_='build')
                if not build_link:
                    logging.warning(f"Construction link not found for village ID {village_id}, building ID {building_id}.")
                    continue

                href = build_link['href']
                csrf_token = href.split('&k=')[-1]

                upgrade_message = soup.find('p', class_='none')
                if upgrade_message and "Fully Updated" in upgrade_message.text:
                    logging.info(f"Building ID {building_id} in village ID {village_id} is fully upgraded.")
                    break

                construct_url = f"https://fun.gotravspeed.com/village2.php?id={village_id}&b={building_id}&k={csrf_token}"
                response = await client.get(construct_url)
                if response.status_code != 200:
                    logging.error(f"Failed to construct/upgrade at {construct_url}. Status code: {response.status_code}")
                else:
                    logging.info(f"Successfully constructed/upgraded building ID {building_id} at {construct_url}")
            except Exception as e:
                logging.error(f"An error occurred during the construction/upgrade process: {str(e)}")


async def construct_and_upgrade_villages(cookies):
    for village_type in config["buidling"]:
        village_name = village_type["type"]
        logging.info(f"Constructing and upgrading {village_name} village...")
        for building in village_type["construction"]:
            pid = building["pid"]
            bid = building["bid"]
            loop = building["loop"]
            await construct_and_upgrade_building(cookies, village_id=pid, building_id=bid, loops=loop)
            # Add a delay here if needed

async def research_academy(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        while True:
            response = await client.get(f"{base_url}/build.php?id=33")  # Academy building ID
            soup = BeautifulSoup(response.text, 'html.parser')
            research_links = soup.select('table.build_details .act a.build')
            if not research_links:
                logging.info("All troops in the Academy are fully researched.")
                break

            for link in research_links:
                research_url = f"{base_url}/{link['href']}"
                await client.get(research_url)
                logging.info("Researching new troop in the Academy")
                break  # Break after researching one troop to re-check the Academy page

async def upgrade_armory(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        while True:
            response = await client.get(f"{base_url}/build.php?id=29")  # Armory building ID
            soup = BeautifulSoup(response.text, 'html.parser')
            upgrade_links = soup.select('table.build_details .act a.build')
            if not upgrade_links:
                logging.info("All troops in the Armory are fully upgraded.")
                break

            for link in upgrade_links:
                troop_info = link.find_previous('div', class_='tit').text
                troop_level = int(troop_info.split('(')[-1].split(')')[0].split(' ')[-1])
                if troop_level < 20:
                    upgrade_url = f"{base_url}/{link['href']}"
                    await client.get(upgrade_url)
                    logging.info(f"Upgrading {troop_info.split('(')[0].strip()} to level {troop_level + 1} in the Armory")
                    break  # Break after upgrading one troop to re-check the Armory page


async def upgrade_smithy(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        while True:
            response = await client.get(f"{base_url}/build.php?id=21")  # Smithy building ID
            soup = BeautifulSoup(response.text, 'html.parser')
            upgrade_links = soup.select('table.build_details .act a.build')
            if not upgrade_links:
                logging.info("All troops in the Smithy are fully upgraded.")
                break

            for link in upgrade_links:
                troop_info = link.find_previous('div', class_='tit').text
                troop_level = int(troop_info.split('(')[-1].split(')')[0].split(' ')[-1])
                if troop_level < 20:
                    upgrade_url = f"{base_url}/{link['href']}"
                    await client.get(upgrade_url)
                    logging.info(f"Upgrading {troop_info.split('(')[0].strip()} to level {troop_level + 1} in the Smithy")
                    break  # Break after upgrading one troop to re-check the Smithy page

async def switch_village(cookies, village_id):
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{base_url}/village2.php?vid={village_id}")
        if response.status_code == 200:
            logging.info(f"Switched to village ID {village_id}")
        else:
            logging.error(f"Failed to switch to village ID {village_id}")

async def construct_capital(cookies, village_id=""):
    # await switch_village(cookies, village_id)
    capital_data = next((item for item in config["building"] if item["type"] == "capital"), None)
    if capital_data is None:
        logging.error("Capital data not found in config")
        return

    for building in capital_data["construction"]:
        pid = building["pid"]
        bid = building["bid"]
        loop = building["loop"]
        await construct_and_upgrade_building(cookies, village_id=pid, building_id=bid, loops=loop)

        if bid in [13, 12, 33]:  # Armory, Smithy, Academy
            if bid == 13:
                await upgrade_armory(cookies)
            elif bid == 12:
                await upgrade_smithy(cookies)
            elif bid == 33:
                await research_academy(cookies)

async def construct_artefact(cookies, village_id):
    await switch_village(cookies, village_id)
    artefact_data = next((item for item in config["building"] if item["type"] == "artefact"), None)
    if artefact_data is None:
        logging.error("Artefact data not found in config")
        return

    for building in artefact_data["construction"]:
        pid = building["pid"]
        bid = building["bid"]
        loop = building["loop"]
        await construct_and_upgrade_building(cookies, village_id=pid, building_id=bid, loops=loop)

async def construct_secondary(cookies, village_id):
    await switch_village(cookies, village_id)
    secondary_data = next((item for item in config["building"] if item["type"] == "secondary"), None)
    if secondary_data is None:
        logging.error("Secondary data not found in config")
        return

    for building in secondary_data["construction"]:
        pid = building["pid"]
        bid = building["bid"]
        loop = building["loop"]
        await construct_and_upgrade_building(cookies, village_id=pid, building_id=bid, loops=loop)


async def main():
    try:
        cookies = await login()  # Login and get cookies
        if not cookies:
            print("Login failed.")
            return
        
        print("Choose an action: 1: Capital, 2: Artefact, 3: Secondary")
        choice = input("Enter choice: ")

        if choice == '1':
            village_id = input("Enter the village ID for the capital: ")
            await construct_capital(cookies, village_id)
        elif choice == '2':
            village_id = input("Enter the village ID for the artefact: ")
            await construct_artefact(cookies, village_id)
        elif choice == '3':
            village_id = input("Enter the village ID for secondary buildings: ")
            await construct_secondary(cookies, village_id)
        else:
            print("Invalid choice.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(main())
