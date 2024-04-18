from bs4 import BeautifulSoup
from urllib.parse import parse_qs
import argparse
import time
import grequests
import requests
import re
from datetime import datetime
import threading
import logging
import aiohttp
import asyncio
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

session = requests.Session()

#========================Config variables===================
free_spots = ["146337", "147540"]
own_villages = ["13606"]
catapults = []
#=======================END Config variables ======================================

#=======================Configuring what to do and parsing parameters==============

loggedIn = False
doProduction = False
doCulturePoints = False
doNewVillage = False
doStorage = False
doSaP = False
doFarmOwnHH = False
doFarmOwnHL = False
doFarmOwnLL = False
doFarmOwnLH = False
doFarmOwnII = False
doFarmOwnLI = False
doFarmOwnLP = False
doFarmOwnIL = False
doFarmOwnLS = False
doFarmOwnB = False
printOasis = False
slow = False

doSendCatapults = False
maxLeg = False
once = False
ww = False
doUpgradeTroops = False
doBuildVillageBase = False

# Create an argument parser
parser = argparse.ArgumentParser(description="Script to process variables")

# Add arguments for each variable
parser.add_argument('--server', type=str, help='Specify server.', required=True)
parser.add_argument("--production", action="store_true", help="Buy Production.")
parser.add_argument("--culture", action="store_true", help="Generate culture points.")
parser.add_argument("--newvillage", action="store_true", help="Build new vilages.")
parser.add_argument("--storage", action="store_true", help="Buy storage.")
parser.add_argument("--SaP", action="store_true", help="Buy production and storage.")
parser.add_argument("--farmOwnHH", action="store_true", help="Farm own villages with horses, buy horses.")
parser.add_argument("--farmOwnHL", action="store_true", help="Farm own villages with horses, buy legionars.")
parser.add_argument("--farmOwnLL", action="store_true", help="Farm own villages with legionars buy legionars.")
parser.add_argument("--farmOwnLH", action="store_true", help="Farm own villages with legionars buy horses.")
parser.add_argument("--farmOwnLI", action="store_true", help="Farm own villages with legionars buy imperians.")
parser.add_argument("--farmOwnLP", action="store_true", help="Farm own villages with legionars buy praetorians.")
parser.add_argument("--farmOwnIL", action="store_true", help="Farm own villages with imperians buy legionars.")
parser.add_argument("--farmOwnII", action="store_true", help="Farm own villages with imperians buy imperians.")
parser.add_argument("--farmOwnLS", action="store_true", help="Farm own villages with imperians buy scouts.")
parser.add_argument("--slow", action="store_true", help="Slower the attacks to not break it.")
parser.add_argument("--farmOwnB", action="store_true", help="Break attack captcha.")
parser.add_argument("--oasis", action="store_true", help="Print all occupied oasis.")
parser.add_argument("--catapults", action="store_true", help="Send 20x catapults to each village.")
parser.add_argument('--farmOwnStart', type=int, help='Start index of ownFarm array.')
parser.add_argument('--farmId', type=int, help='Will replace own_villager array with player willages IDs.')
parser.add_argument('--catapultId', type=int, help='Will replace catapults array with player willages IDs.')
parser.add_argument("--maxLeg", action="store_true", help="Buy maximum number of legs instead of fixed.")
parser.add_argument("--once", action="store_true", help="Exit after reaching first end of while.")
parser.add_argument("--ww", action="store_true", help="Build ww.")
parser.add_argument("--upgradeTroops", action="store_true", help="Upgrade troops in smithy and armory.")
parser.add_argument("--base", action="store_true", help="Build village base.")
parser.add_argument('--wwId', type=str, help='Specify in which willage the ww is.')
parser.add_argument('--centerX', type=int, help='Spefify x coord of village to build around.')
parser.add_argument('--centerY', type=int, help='Spefify y coord of village to build around.')
parser.add_argument('--buildN', type=int, help='Number of villages to build.')


# Parse the command-line arguments
args = parser.parse_args()

# Update the variables based on the provided arguments
if args.production:
    doProduction = True
if args.culture:
    doCulturePoints = True
if args.newvillage:
    doNewVillage = True
if args.storage:
    doStorage = True
if args.SaP:
    doSaP = True
if args.farmOwnHH:
    doFarmOwnHH = True
if args.farmOwnHL:
    doFarmOwnHL = True
if args.farmOwnLL:
    doFarmOwnLL = True
if args.farmOwnLH:
    doFarmOwnLH = True
if args.farmOwnII:
    doFarmOwnII = True
if args.farmOwnLP:
    doFarmOwnLP = True
if args.farmOwnLI:
    doFarmOwnLI = True
if args.farmOwnIL:
    doFarmOwnIL = True
if args.farmOwnLS:
    doFarmOwnLS = True
if args.farmOwnB:
    doFarmOwnB = True
if args.catapults:
    doSendCatapults = True
if args.maxLeg:
    maxLeg = True
if args.once:
    once = True
if args.ww:
    ww = True
if args.upgradeTroops:
    doUpgradeTroops = True
if args.base:
    doBuildVillageBase = True
if args.oasis:
    printOasis = True
if args.slow:
    slow = True

with open(f'{args.server}/travCookies.txt', 'r') as f:
    for line in f:
        key, value = line.strip().split('=', 1)
        globals()[key] = value
cookiesValue = f"gotravspeed={gotravspeed}; _ga={_ga}; _gid={_gid}; _ga_PV587PPWQK={_ga_PV587PPWQK}"

with open(f'creds.txt', 'r') as f:
    for line in f:
        key, value = line.strip().split('=', 1)
        try:
            globals()[key] = int(value)
        except:
            globals()[key] = value

with open(f'{args.server}/travTroopsAmounts.txt', 'r') as f:
    for line in f:
        key, value = line.strip().split('=', 1)
        try:
            globals()[key] = int(value)
        except:
            globals()[key] = value

serverId = 0

if args.server == "fun":
    serverId = 9
elif (args.server == "s8"):
    serverId = 8
elif (args.server == "netus"):
    serverId = 32
else:
    print("WARNING: Possible problems with unknown server ID according to a provided name!!!!")

#Reduce number of needed arguments. If id for specific action is specified, enable the action.
if args.wwId is not None:
    ww = True
if args.catapultId is not None:
    doSendCatapults = True

#=======================END Configuring what to do and parsing parameters==============

#=======================Shared variables, edit with caution========================

#Id is id of the position where the building is standing

mainBuildingId = "26"
rallyPointId = "39"
residenceId = "31"
christmassTreeId = "34"
ironId = "36"
brickId = "38"
sawId = "37"
barracksId = "28"
academyId = "21"
custureId = "23"
stableId = "24"
townHallId = "23"
WWId = "25"
wallId = "40"
smithyId = "25"
armoryId = "30"
tournamentSquareId = "29"
siegeWorkshopId = "19"

#Number is identification when sending request to build a building
residenceNumber = "25"
christmassTreeNumber = "44"
ironNumber = "7"
brickNumber = "6"
sawNumber = "5"
barracksNumber = "19"
academyNumber = "22"
tournamentSquareNumber = "14"
smithyNumber = "12"
armoryNumber = "13"
stableNumber = "20"
siegeWorkshopNumber = "21"
townHallNumber = "24"


mainWeb = f"https://{args.server}.gotravspeed.com/"
urlProdGet = f"https://{args.server}.gotravspeed.com/buy2.php"
urlProdPost = f"https://{args.server}.gotravspeed.com/buy2.php?t=0&Shop=done"
urlStorPost = f"https://{args.server}.gotravspeed.com/buy2.php?t=2&Shop=done"

#urlCulturePoints = f"https://{args.server}.gotravspeed.com/build.php?id={townHallId}"
#urlStables = f"https://{args.server}.gotravspeed.com/build.php?id={stableId}"
#urlBarracks = f"https://{args.server}.gotravspeed.com/build.php?id={barracksId}"


#=======================END of shared variables====================================

class RomanArmy:

    def __init__(self, Legionars=0, Praetorians=0, Imperians=0, Scouts=0, Imperatoris=0, Ceasaris=0, Catapults=0):
        self.Legionars = Legionars
        self.Praetorians = Praetorians
        self.Imperians = Imperians
        self.Scouts = Scouts
        self.Imperatoris = Imperatoris
        self.Ceasaris = Ceasaris
        self.Catapults = Catapults

def printTimestamp(message):

    # returns current time
    now = datetime.now()

    # formats hours and minutes
    formatted_time = now.strftime("%H:%M:%S")

    # gets seconds and milliseconds
    seconds = now.second
    milliseconds = now.microsecond // 1000

    print(f"{message} - Time: {formatted_time}:{milliseconds}")

def logIn():
    url1 = "https://www.gotravspeed.com/"
    headers1 = {
        "POST": "https://www.gotravspeed.com/ HTTP/1.1",
        "host": "www.gotravspeed.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": "https://www.gotravspeed.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.gotravspeed.com",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    encoded_string1 = f"name={username}&password={password}"
    data1 = parse_qs(encoded_string1)

    url2 = "https://www.gotravspeed.com/game/servers"

    encoded_string2 = f"action=server&value={serverId}"
    data2 = parse_qs(encoded_string2)

    url3 = "https://www.gotravspeed.com/game/servers"

    encoded_string3 = f"action=serverLogin&value%5Bpid%5D={serverId}&value%5Bserver%5D={serverId}"
    data3 = parse_qs(encoded_string3)

    response1 = session.post(url1, headers=headers1, data=data1)
    response2 = session.post(url2, headers=headers1, data=data2)
    response3 = session.post(url3, headers=headers1, data=data3)

    print("Logged in!")

def getUpdateButtonHrefInBuilding(buildingId):
    url = getBuildingUrl(buildingId)
    headers = returnHeadersToUpgradeBuildingWithoutSecFetchUser(25)
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        update_link = soup.find('a', string='update')['href']
    except:
        return None
    return update_link

def getSearchButtonHrefInBuilding(buildingId):
    url = getBuildingUrl(buildingId)
    headers = returnHeadersToUpgradeBuildingWithoutSecFetchUser(25)
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        update_link = soup.find('a', string='Search')['href']
    except:
        return None
    return update_link

def upgradeTroops():
    headers = returnHeadersToUpgradeBuilding(0)
    print("Starting to upgrade in armory..")
    for i in range(200):
        print(f"Armory upgrade {i}.")
        href = getUpdateButtonHrefInBuilding(armoryId)
        if href is None:
            print("All already upgraded in armory.")
            break
        url = mainWeb + href
        session.get(url, headers=headers)
    print("Starting to upgrade in smithy..")
    for i in range(200):
        print(f"Smithy upgrade {i}.")
        href = getUpdateButtonHrefInBuilding(smithyId)
        if href is None:
            print("All already upgraded in smithy.")
            break
        url = mainWeb + href
        session.get(url, headers=headers)

def researchTroops():
    headers = returnHeadersToUpgradeBuilding(0)
    for i in range(15):
        print(f"Academy research {i}.")
        href = getSearchButtonHrefInBuilding(academyId)
        if href is None:
            print("All already researched.")
            break
        url = mainWeb + href
        session.get(url, headers=headers)

def getBuildingUrl(buildingId):
    return f"https://{args.server}.gotravspeed.com/build.php?id={buildingId}"

def generate_map_view_central_ids():
    view_central_ids = []
    for i in range(3, 398, 7):
        for j in range(3, 398, 7):
            id = i * 400 + j + 1
            view_central_ids.append(id)
    return view_central_ids

def print_all_occupied_oasis():
    all_center_grid_ids = generate_map_view_central_ids()
    for center_id in all_center_grid_ids:
        check_7x7_grid_for_ocupied_oasis(center_id)
def check_7x7_grid_for_ocupied_oasis(grid_center_id: str):
    url = f"https://{args.server}.gotravspeed.com/map.php?id={grid_center_id}&_a1_"
    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/map.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
    }

    response = session.get(url, headers=headers)
    content = response.content.decode()  # converts bytes to string

    # Look for the innermost array that contains 'oasis place owned':
    matches = re.findall(r'\[[^\[\]]*?oasis place owned[^\[\]]*?\]', content)

    for match in matches:
        print(match)

def print_all_occupied_oasis_batch_experimental():
    all_center_grid_ids = generate_map_view_central_ids()
    batch_size = 10  # Customize the batch size as needed

    # Divide the list into batches
    for i in range(0, len(all_center_grid_ids), batch_size):
        batch_ids = all_center_grid_ids[i:i + batch_size]
        check_7x7_grid_for_ocupied_oasis2(batch_ids)


def check_7x7_grid_for_ocupied_oasis_batch_experimental(grid_center_id_array: str):
    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/map.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
    }

    requests = []
    for grid_center_id in grid_center_id_array:
        url = f"https://{args.server}.gotravspeed.com/map.php?id={grid_center_id}&_a1_"
        request = grequests.AsyncRequest(
            method='GET',
            url=url,
            headers=headers
        )
        requests.append(request)

    # Send the requests and get the responses
    responses = grequests.map(requests)

    for response in responses:
        content = response.content.decode()  # Converts bytes to string

        # Look for the innermost array that contains 'oasis place owned':
        matches = re.findall(r'\[[^\[\]]*?oasis place owned[^\[\]]*?\]', content)

        for match in matches:
            print(match)

    print("Searched one batch.")



def replaceOwnVillagesWithPlayerVillages(playerId):
    global own_villages
    id_list = []
    url = f"https://{args.server}.gotravspeed.com/profile.php?uid={playerId}"

    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/village1.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
    }

    # Fetch the HTML content
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all <td> elements with class "nam"
    nam_cells = soup.find_all("td", class_="nam")

    # Extract the IDs from the <a> tags within each <td>
    for cell in nam_cells:
        link = cell.find("a")
        if link:
            href = link.get("href")
            # Extract the ID from the href attribute
            id_value = href.split("=")[-1]
            id_list.append(id_value)
    own_villages = id_list
    
def replaceCatapultsWithPlayerVillages(playerId):
    global catapults
    id_list = []
    url = f"https://{args.server}.gotravspeed.com/profile.php?uid={playerId}"

    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/village1.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
    }

    # Fetch the HTML content
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all <td> elements with class "nam"
    nam_cells = soup.find_all("td", class_="nam")

    # Extract the IDs from the <a> tags within each <td>
    for cell in nam_cells:
        population_cell = cell.find_next("td", class_="hab")
        population = int(population_cell.text.strip())  # Convert population to an integer
            
        # Check if population is greater than 0
        if population > 0:
            link = cell.find("a")
            if link:
                href = link.get("href")
                # Extract the ID from the href attribute
                id_value = href.split("=")[-1]
                id_list.append(id_value)
    catapults = id_list

headersProd = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/buy2.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

headersShop2Post = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/buy2.php",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": f"https://{args.server}.gotravspeed.com",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

dataProdPost = {
    "selected_res": "4",
    "g-recaptcha-response": "abcd",
    "xor": "100",
    "key": "9f6f3"
}

dataStorPost = {
    "selected_res": "4",
    "g-recaptcha-response": "abcd",
    "xor": "100",
    "key": "9f6f3"
}

headersCulturePointsGet = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/village2.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

trainTroopsHeaders = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/build.php?id=24",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": f"https://{args.server}.gotravspeed.com",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
 }

def checkLogin():
    global loggedIn
    responseProdGet = session.get(urlProdGet, headers=headersProd)
    soup = BeautifulSoup(responseProdGet.content, "html.parser")
    element = soup.find("input", {"name": "key"})
    if element is not None:
        loggedIn = True
        print("Login check OK.")
    else:
        loggedIn = False
        print("Logget out. Logging in..")
        logIn()

async def getCsrfForShop2(session: aiohttp.ClientSession) -> str:
    async with session.get(urlProdGet, headers=headersProd) as responseProdGet:
        soup = BeautifulSoup(await responseProdGet.text(), "html.parser")
        element = soup.find("input", {"name": "key"})
        if element is not None:
            loggedIn = True
            csrf_token = element["value"]
            return csrf_token

def getMaxNumOfLegs() -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'cs,sk;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': f'https://{args.server}.gotravspeed.com/build.php?id=28',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'https://{args.server}.gotravspeed.com',
        'Connection': 'keep-alive',
        "Cookie": cookiesValue,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }

    response = session.get(getBuildingUrl(barracksId), headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    max_tr = soup.find('td', class_='max')

    # Extract the number from the <a> element
    number_a = max_tr.find('a')
    number_text = number_a.get_text(strip=True)
    number = int(number_text.strip('()'))
    title = number_a['title']

    print(f"Maximum leg buy count is {title} - {number}")

    return number

def create_post_requests(url, headers, data, num_requests):
    return [grequests.post(url, headers=headers, data=data) for _ in range(num_requests)]

def buyLegionars(num_requests):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'cs,sk;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': f'https://{args.server}.gotravspeed.com/build.php?id=28',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'https://{args.server}.gotravspeed.com',
        'Connection': 'keep-alive',
        "Cookie": cookiesValue,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }

    if (maxLeg):
        encoded_string = f"tf%5B1%5D={getMaxNumOfLegs()}&s1.x=59&s1.y=10"
    else:
        encoded_string = f"tf%5B1%5D={legionarsBuyAmount}&s1.x=59&s1.y=10"
    data = parse_qs(encoded_string)

    rs = create_post_requests(getBuildingUrl(barracksId), headers, data, num_requests)
    grequests.map(rs)

    print(f"Bought legionars..")

def buyPraetors(num_requests):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'cs,sk;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': f'https://{args.server}.gotravspeed.com/build.php?id=28',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'https://{args.server}.gotravspeed.com',
        'Connection': 'keep-alive',
        "Cookie": cookiesValue,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }

    encoded_string = f"tf%5B1%5D=0&tf%5B2%5D={praetorsBuyAmount}&s1.x=59&s1.y=10"
    data = parse_qs(encoded_string)

    rs = create_post_requests(getBuildingUrl(barracksId), headers, data, num_requests)
    grequests.map(rs)

    print(f"Bought praets..")

def buyImperians(num_requests):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'cs,sk;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': f'https://{args.server}.gotravspeed.com/build.php?id=28',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'https://{args.server}.gotravspeed.com',
        'Connection': 'keep-alive',
        "Cookie": cookiesValue,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }

    encoded_string = f"tf%5B1%5D=0&tf%5B2%5D=0&tf%5B3%5D={legionarsBuyAmount}&s1.x=59&s1.y=10"
    data = parse_qs(encoded_string)

    rs = create_post_requests(getBuildingUrl(barracksId), headers, data, num_requests)
    grequests.map(rs)

    print(f"Bought imperians..")

async def buyTroopsSlow(session, num_requests, romanArmy: RomanArmy):
    async def sendTrainTroopsRequestBarracks(session, romanArmy: RomanArmy):
        url = getBuildingUrl(barracksId)

        data = f"tf%5B1%5D={romanArmy.Legionars}&tf%5B2%5D={romanArmy.Praetorians}&tf%5B3%5D={romanArmy.Imperians}&s1.x=63&s1.y=8"

        response = await session.post(url, headers=trainTroopsHeaders, data=data)

    async def sendTrainTroopsRequestStables(session, romanArmy: RomanArmy):
        url = getBuildingUrl(stableId)

        data = f"tf%5B4%5D={romanArmy.Scouts}&tf%5B5%5D={romanArmy.Imperatoris}&tf%5B6%5D={romanArmy.Ceasaris}&s1.x=63&s1.y=8"

        response = await session.post(url, headers=trainTroopsHeaders, data=data)

    async with aiohttp.ClientSession() as buyTroopsSession:
        logging.info(f"Started buying troops")
        if ((romanArmy.Legionars > 0) or (romanArmy.Praetorians > 0) or (romanArmy.Imperians > 0)):
            tasks = [sendTrainTroopsRequestBarracks(buyTroopsSession, romanArmy) for _ in range(num_requests)]
        else:
            print("Jdu sem")
            tasks = [sendTrainTroopsRequestStables(buyTroopsSession, romanArmy) for _ in range(num_requests)]
        await asyncio.gather(*tasks)
        logging.info(f"Finished buying troops.")

async def buyTroopsTasks(session, num_requests, romanArmy: RomanArmy):
    async def sendTrainTroopsRequestBarracks(session, romanArmy: RomanArmy):
        url = getBuildingUrl(barracksId)

        data = f"tf%5B1%5D={romanArmy.Legionars}&tf%5B2%5D={romanArmy.Praetorians}&tf%5B3%5D={romanArmy.Imperians}&s1.x=63&s1.y=8"

        asyncio.create_task(post_request(session, url, trainTroopsHeaders, data))

    async def sendTrainTroopsRequestStables(session, romanArmy: RomanArmy):
        url = getBuildingUrl(stableId)

        data = f"tf%5B4%5D={romanArmy.Scouts}&tf%5B5%5D={romanArmy.Imperatoris}&tf%5B6%5D={romanArmy.Ceasaris}&s1.x=63&s1.y=8"

        asyncio.create_task(post_request(session, url, trainTroopsHeaders, data))

    if ((romanArmy.Legionars > 0) or (romanArmy.Praetorians > 0) or (romanArmy.Imperians > 0)):
        for _ in range(num_requests):
            await sendTrainTroopsRequestBarracks(session, romanArmy)
    else:
        for _ in range(num_requests):
            await sendTrainTroopsRequestStables(session, romanArmy)

    logging.info(f"Bought troops.")

def buyScounts(num_requests):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/build.php?id=24",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"https://{args.server}.gotravspeed.com",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    encoded_string = f"tf%5B4%5D={horsesBuyAmount}&tf%5B6%5D=0&s1.x=63&s1.y=8"
    data = parse_qs(encoded_string)

    rs = create_post_requests(getBuildingUrl(stableId), headers, data, num_requests)
    grequests.map(rs)

    print("Bought scouts..")

def getAttackKeySync() -> str:
    url = f"https://{args.server}.gotravspeed.com/v2v.php?id=155183"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/build.php?id=39",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    response = session.get(url, headers=headers)

    soup = BeautifulSoup(response.content, "html.parser")
    element = soup.find("input", {"name": "key"})
    csrf_token = element["value"]

    return csrf_token

async def getAttackKey(session: aiohttp.ClientSession) -> str:
    url = f"https://{args.server}.gotravspeed.com/v2v.php?id=155183"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/build.php?id=39",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    async with session.get(url, headers=headers) as response:
        soup = BeautifulSoup(await response.text(), "html.parser")
        element = soup.find("input", {"name": "key"})
        if element is not None:
            csrf_token = element["value"]
            return csrf_token

async def attack(session: aiohttp.ClientSession, villageId: str, key: str, romanArmy: RomanArmy, attackType = 4):
    url = f"https://{args.server}.gotravspeed.com/v2v.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/v2v.php",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"https://{args.server}.gotravspeed.com",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    encoded_string = f"id={villageId}&c={attackType}&t%5B1%5D={romanArmy.Legionars}&t%5B2%5D={romanArmy.Praetorians}&t%5B3%5D={romanArmy.Imperians}&t%5B4%5D={romanArmy.Scouts}&t%5B5%5D={romanArmy.Imperatoris}&t%5B6%5D={romanArmy.Ceasaris}&t%5B7%5D=0&t%5B8%5D={romanArmy.Catapults}&t%5B9%5D=0&t%5B10%5D=0&key={key}&g-recaptcha-response=abcd"
    data = parse_qs(encoded_string)

    if (slow):
        await post_request(session, url, headers,data)
    else:
        asyncio.create_task(post_request(session, url, headers, data))
    logging.info(f"Sent attack to {villageId}")
    #await asyncio.sleep(0.01)

async def CP(session: aiohttp.ClientSession):
    k_value = "XXXXX"
    for i in range(2000):
        async with session.get(getBuildingUrl(townHallId), headers=headersCulturePointsGet) as responseCultureGet:

            soup = BeautifulSoup(await responseCultureGet.text(), "html.parser")
            k_value = False
            td_element = soup.find("td", {"class": "act"})
            if td_element is not None:
                a_element = td_element.find("a")
                if a_element is not None:
                    href_value = a_element["href"]
                    k_value = href_value.split("=")[-1]
                else:
                    print("No <a> element found")
                    break
            else:
                print("No <td> element with class 'act' found")

            urlCulturePointsWithKey = getBuildingUrl(townHallId) + "&a=2" f"&k={k_value}"
        
        asyncio.create_task(get_request(session, urlCulturePointsWithKey, headersCulturePointsGet))
        logging.info(f"CP request {k_value}")
        await asyncio.sleep(0.01)

#=====Village construction============

def returnHeadersToUpgradeBuilding(id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/build.php?vid=4058&id={id}",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }
    return headers

def returnHeadersToUpgradeBuildingWithoutSecFetchUser(id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/build.php?vid=4058&id={id}",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }
    return headers

def upgradeBuilding(placeId, villageId = None):
    if villageId is not None:
        buildingUrl = mainWeb + "build.php?vid=" + str(villageId) + "&id=" + placeId
    else:
        buildingUrl = mainWeb + "build.php?id=" + placeId
    headers = returnHeadersToUpgradeBuilding(placeId)
    responseBuilding = session.get(buildingUrl, headers=headers)

    soup = BeautifulSoup(responseBuilding.content, "html.parser")

    if "Fully" in responseBuilding.text:
        return "Max"

    k_value = False

    a_element = soup.find("a", {"class": "build"})
    if a_element is not None:
        href_value = a_element["href"]
        k_value = href_value.split("=")[-1]
    else:
        print("No <a> element with class 'build' found")

    if k_value:
        urlUpgradBuilding = mainWeb + href_value
        headers = returnHeadersToUpgradeBuildingWithoutSecFetchUser(placeId)
        responseBuilding2 = session.get(urlUpgradBuilding, headers=headers)
        print(f"Sent request to upgrade building on id {placeId} to: {a_element.text}.")
        words = a_element.text.split()
        last_number = None

        for word in words:
            if word.isdigit():
                last_number = int(word)
                break
        return last_number

def replace_b(original_string: str, new_b_value: str) -> str:
    start_index = original_string.find("b=")
    if start_index == -1:
        return "The original string does not contain 'b='"
    else:
        end_index = original_string.find("&", start_index)
        if end_index == -1:
            new_string = original_string[:start_index+2] + new_b_value
        else:
            new_string = original_string[:start_index+2] + new_b_value + original_string[end_index:]
        return new_string

def constructNewBuilding(placeId: str, buildingNumber: str):
    buildingUrl = mainWeb + "build.php?id=" + placeId

    headers = returnHeadersToUpgradeBuilding(placeId)
    responseBuilding = session.get(buildingUrl, headers=headers)

    soup = BeautifulSoup(responseBuilding.content, "html.parser")

    k_value = False

    a_element = soup.find("a", {"class": "build"})
    if a_element is not None:
        href_value = a_element["href"]
        k_value = href_value.split("=")[-1]
    else:
        print("No <a> element with class 'build' found")
        print("Already exists..")
        return

    new_href_value = replace_b(href_value, buildingNumber)

    if k_value:
        urlConstructBuilding = mainWeb + new_href_value
        headers = returnHeadersToUpgradeBuildingWithoutSecFetchUser(placeId)
        responseBuilding2 = session.get(urlConstructBuilding, headers=headers)
        print(f"Sent request to construct building {buildingNumber} on id {placeId}.")

def makeSettlers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/build.php?id={residenceId}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"https://{args.server}.gotravspeed.com",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }
    
    urlMakeSettlers = mainWeb + "build.php?id=" + residenceId

    encoded_string = "tf%5B10%5D=3&s1.x=57&s1.y=11"
    data = parse_qs(encoded_string)

    rs = create_post_requests(urlMakeSettlers, headers, data, 10)
    grequests.map(rs)

    print(f"Made settlers.")

def sendSettlersTo(id):
    url = mainWeb + "v2v.php?id=" + str(id)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/v2v.php?id={id}",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    for i in range (40):

        keyGetResponse = session.get(url, headers=headers)

        soup = BeautifulSoup(keyGetResponse.content, "html.parser")

        k_value = False

        input_element = soup.find('input', {'name': 'key'})
        if input_element is not None:
            k_value = input_element['value']
        else:
            print("No <input> element with key found - settlers were sent succesfully - probably.")
            return

        if k_value:
            encoded_string = f"id={id}&c=4&t%5B1%5D=0&t%5B2%5D=0&t%5B3%5D=0&t%5B4%5D=0&t%5B5%5D=0&t%5B6%5D=0&t%5B7%5D=0&t%5B8%5D=0&t%5B9%5D=0&t%5B10%5D=3&key={k_value}"
            data = parse_qs(encoded_string)

            session.post(url, headers=headers, data=data)

            print(f"Sent request to send settlers to {id}.")
    print("Exceeded limit for settlers send retry.")

def confirmVillageBuild():
    url = mainWeb + "shownvill.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/village1.php",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    for i in range(40):
        response = session.get(url, headers=headers)
        content = response.text
        if 'continue' in content:
            print(f"Confirmed village build.")
            return
        else: 
            print(f"Waiting for village build confirmation: {i}.")
    print("Exceeded waiting limit for village confirmation.")

#=====END Village Construction========

def getActualNumberOfVillages():

    url = f"https://{args.server}.gotravspeed.com/profile.php"

    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": f"https://{args.server}.gotravspeed.com/village1.php",
    "Connection": "keep-alive",
    "Cookie": cookiesValue,
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
    }

    # Fetch the HTML content
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all <td> elements with class "nam"
    nam_cells = soup.find_all("td", class_="nam")

    return len(nam_cells)

def attackWithCatapults(villageId: str, numberOfCatapults: str, numberOfLegionars: str, numberOfHorses: str, numberOfRam: str, key: str):
    url = f"https://{args.server}.gotravspeed.com/v2v.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": f"https://{args.server}.gotravspeed.com/v2v.php",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"https://{args.server}.gotravspeed.com",
        "Connection": "keep-alive",
        "Cookie": cookiesValue,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    encoded_string = f"dtg=99&dtg1=99&id={villageId}&c=3&t%5B1%5D={numberOfLegionars}&t%5B2%5D=0&t%5B3%5D=0&t%5B4%5D=0&t%5B5%5D=0&t%5B6%5D={numberOfHorses}&t%5B7%5D={numberOfRam}&t%5B8%5D={numberOfCatapults}&t%5B9%5D=0&t%5B10%5D=0&key={key}&g-recaptcha-response=abcd"
    data = parse_qs(encoded_string)

    response = session.post(url, headers=headers, data=data)
    print(f"Sent attack to {villageId} with response {response.status_code}.")

def spiral_out(cx, cy, n):
    # result to hold the cells
    result = []
    # starting cell
    result.append([cx, cy])
    # starting direction, 0-right, 1-down, 2-left, 3-up
    direction = 0
    # steps in current direction and max steps in current direction
    steps, max_steps = 0, 1
    # total steps so far
    total_steps = 1
    # current position
    x, y = cx, cy
    # looping until we reach required cells
    while total_steps < n:
        # moving according to current direction
        if direction == 0: x += 1
        elif direction == 1: y -= 1
        elif direction == 2: x -= 1
        elif direction == 3: y += 1
        # adding the cell
        result.append([x, y])
        # incrementing steps
        steps += 1
        total_steps += 1
        # if we have reached max, change direction
        if steps == max_steps:
            direction = (direction + 1) % 4
            steps = 0
            # increment max_steps if we are moving right or left
            if direction % 2 == 0:
                max_steps += 1
    return result

def get_cell_id(x,y):
    if x >= 0:
        #x 0..200
        x_part = x*401
    else:
        #x -200..-1
        x_part = (x+401)*401
    if y >= 0:
        #y 0..200
        y_part = y + 1
    else:
        #y -200..-1
        y_part = y + 402
    return x_part + y_part

def autoBuildVillages(list_of_ids):
    for count, spot in enumerate(list_of_ids):
        buildNewVillage(spot, count)
    print("All villages builded. Exiting..")

#print(f"(0,0) Shoud be 1 and is {get_cell_id(0,0)}")
#print(f"(0,1) Shoud be 2 and is {get_cell_id(0,1)}")
#print(f"(0,-1) Shoud be 401 and is {get_cell_id(0,-1)}")
#print(f"(-1,0) Shoud be 160401 and is {get_cell_id(-1,0)}")
#print(f"(1,0) Shoud be 402 and is {get_cell_id(1,0)}")
#print(f"(1,1) Shoud be 403 and is {get_cell_id(1,1)}")
#print(f"(-1,-1) Shoud be 160801 and is {get_cell_id(-1,-1)}")
#print(f"(-63,13) Shoud be 135552 and is {get_cell_id(-63,13)}")
#print(f"(-181,48) Shoud be 88269 and is {get_cell_id(-181,48)}")
#print(f"(164,-141) Shoud be 66025 and is {get_cell_id(164,-141)}")
#exit()

def upgradeBuildingToLevel_old(target_level, buildingId):
    for i in range(50):
        print(f"Upgrading building to level {target_level}..")
        current_level = upgradeBuilding(buildingId)
        if current_level is None:
            continue
        if current_level == "Max":
            print("Building already maxed.")
            break
        if current_level >= target_level:
            print(f"The building is now at level {current_level}. Target level reached!")
            break
    else:
        print(f"The building did not reach level {target_level} after 50 attempts.")

def upgradeBuildingToLevel(target_level, buildingId):
    buildingUrl = mainWeb + "build.php?id=" + buildingId
    headers = returnHeadersToUpgradeBuilding(buildingId)
    
    responseBuilding = session.get(buildingUrl, headers=headers)

    soup = BeautifulSoup(responseBuilding.content, "html.parser")

    # Find the span element with class "level"
    level_span = soup.find('span', class_='level')

    # Extract the full text (including "level")
    full_text = level_span.get_text()

    words = full_text.split()

    level = int(words[1])

    # Find the h1 element
    h1_element = soup.find('h1')

    # Extract the building name
    building_name = h1_element.get_text().strip()
    
    while(level < target_level):

        current_level = upgradeBuilding(buildingId)

        if current_level == "Max":
            print("Building already maxed.")
            break

        responseBuilding = session.get(buildingUrl, headers=headers)

        soup = BeautifulSoup(responseBuilding.content, "html.parser")

        # Find the span element with class "level"
        level_span = soup.find('span', class_='level')

        # Extract the full text (including "level")
        full_text = level_span.get_text()

        words = full_text.split()

        level = int(words[1])

        # Find the h1 element
        h1_element = soup.find('h1')

        # Extract the building name
        building_name = h1_element.get_text().strip()

        print(f"{building_name} has level {level}, upgrading to {target_level}.")   

    print(f"Building {building_name} reached the target level {target_level}.")


def checkIfSpotEmpty(spot):
    url = mainWeb + "village3.php?id=" + str(spot)
    headers = returnHeadersToUpgradeBuilding(42)

    response = session.get(url, headers=headers)
    content = response.text
    if 'Deserted valley' in content:
        print(f"Building new village on {spot}")
        return True
    else:
        print(f"There is no building spot on {spot}.")
        return False
        
def buildVillageBase():
    print("Upgrading Main Building.")
    upgradeBuildingToLevel(20, mainBuildingId)
    print("Upgrading Rally Point.")
    upgradeBuilding(rallyPointId)
    upgradeBuildingToLevel(20, rallyPointId)
    print("Upgrading Barracks.")
    constructNewBuilding(barracksId, barracksNumber)
    upgradeBuildingToLevel(20, barracksId)
    print("Upgrading Academy.")
    constructNewBuilding(academyId, academyNumber)
    upgradeBuildingToLevel(20, academyId)
    print("Upgrading Tournament square.")
    constructNewBuilding(tournamentSquareId, tournamentSquareNumber)
    upgradeBuildingToLevel(20, tournamentSquareId)
    print("Upgrading Smithy.")
    constructNewBuilding(smithyId, smithyNumber)
    upgradeBuildingToLevel(20, smithyId)
    print("Upgrading Armory.")
    constructNewBuilding(armoryId, armoryNumber)
    upgradeBuildingToLevel(20, armoryId)
    print("Upgrading Stables.")
    constructNewBuilding(stableId, stableNumber)
    upgradeBuildingToLevel(20, stableId)
    print("Upgrading Siege Workshop.")
    constructNewBuilding(siegeWorkshopId, siegeWorkshopNumber)
    upgradeBuildingToLevel(20, siegeWorkshopId)
    print("Upgrading Town Hall.")
    constructNewBuilding(townHallId, townHallNumber)
    print("Upgrading Residence.")
    constructNewBuilding(residenceId, residenceNumber)
    upgradeBuildingToLevel(20, residenceId)
    print("Upgrading Wall.")
    upgradeBuilding(wallId)
    upgradeBuildingToLevel(20, wallId)
    print("Researching troops.")
    researchTroops()
    print("Upgrading troops.")
    upgradeTroops()

def buildNewVillage(spot, count):
    sendSettlersTo(spot)
    time.sleep(2)
    print(f"Village {count} was build.")
    confirmVillageBuild()
    upgradeBuildingToLevel(5, mainBuildingId)
    print("Building rally point..")
    upgradeBuilding(rallyPointId, spot)
    upgradeBuilding(rallyPointId, spot)
    print("Constructing residence..")
    constructNewBuilding(residenceId, residenceNumber)
    upgradeBuildingToLevel(10, residenceId) 
    makeSettlers()
    print("Constructing saw..")
    constructNewBuilding(sawId, sawNumber)
    print("Constructiong iron foundry..")
    constructNewBuilding(ironId, ironNumber)
    print("Construction brickworks..")
    constructNewBuilding(brickId, brickNumber)
    print("Contructing christmass tree")
    constructNewBuilding(christmassTreeId, christmassTreeNumber)
    print("Upgrading bonus buildings..")
    upgradeBuildingToLevel(10, sawId)
    upgradeBuildingToLevel(10, ironId)
    upgradeBuildingToLevel(10, brickId)

if doNewVillage:
    for count, spot in enumerate(free_spots):
        try:
            buildNewVillage(spot, count)
        except:
            print("Error occuren when building village. Continue.")
            time.sleep(15)

    print("All villages builded. Exiting..")
    exit(0)

last_size = 1
if (args.farmOwnStart is not None):
    last_count = args.farmOwnStart
else:
    last_count = -1

if args.centerX is not None or args.centerY is not None or args.buildN is not None:
    if args.centerX is not None and args.centerY is not None and args.buildN is not None:
        print(f"I will build {args.buildN} villages around ({args.centerX},{args.centerY}).")

        numberOfMyVillages = getActualNumberOfVillages()

        coordinates = spiral_out(args.centerX, args.centerY, args.buildN + numberOfMyVillages)
        ids = [get_cell_id(x,y) for x,y in coordinates]
        for count, spot in enumerate(ids[numberOfMyVillages:]):
            try:
                if checkIfSpotEmpty(spot):
                    try:
                        buildNewVillage(spot, count)
                    except:
                        print("Error while building village, continue..")
            except:
                print("Checking if empty thrown error, continue..")
                time.sleep(2)


        print("All villages built. Exiting..")
        exit(1)
    else:
        print("You have to specify centerX, centerY and buildN together!")
        exit(-1)

if doBuildVillageBase:
    print("Building base requirements for village.")
    buildVillageBase()
    print("Village base builded, exiting..")
    exit(1)

if printOasis:
    print("Searching for occupied oasis..")
    print_all_occupied_oasis()
    print("That's all, exiting..")
    exit(1)

shoudExit = False

async def post_request(session: aiohttp.ClientSession, url, headers, data):
    await session.post(url, headers=headers, data=data)

async def get_request(session: aiohttp.ClientSession, url, headers):
    await session.get(url, headers=headers)

last_key = "xxx"

async def main():
    global last_key
    global shoudExit
    global last_count
    async with aiohttp.ClientSession() as aioSession:
        while True:
            try:
                checkLogin()
                if (loggedIn):
                    if ww:
                        if args.wwId is not None:
                            for i in range(20):
                                upgradeBuilding(wallId, args.wwId)
                            while True:
                                upgradeBuilding(WWId, args.wwId)
                        else:
                            for i in range(20):
                                upgradeBuilding(wallId)
                            while True:
                                upgradeBuilding(WWId)
                    if doUpgradeTroops:
                        upgradeTroops()
                        print("Upgraded troops 100 times in armory and 100 times in smithy.")
                    
                    if (args.farmId is not None):
                        replaceOwnVillagesWithPlayerVillages(args.farmId)
                    if ((args.catapultId is not None) and doSendCatapults):
                        replaceCatapultsWithPlayerVillages(args.catapultId)
                    if doProduction:
                        requestsPause = 0.001
                        for i in range(200):
                            csrf_token = await getCsrfForShop2(aioSession)
                            dataProdPost["key"] = csrf_token
                            if last_key == csrf_token:
                                logging.info(f"Prod request - duplicate")
                                requestsPause = requestsPause + requestsPause
                            else:
                                asyncio.create_task(post_request(aioSession, urlProdPost, headersProd, dataProdPost))
                                await asyncio.sleep(requestsPause)
                                last_key = csrf_token
                                logging.info(f"Prod request")
                    if doStorage:
                        requestsPause = 0.001
                        for i in range(200):
                            csrf_token = await getCsrfForShop2(aioSession)
                            dataStorPost["key"] = csrf_token
                            if last_key == csrf_token:
                                logging.info(f"Prod request - duplicate")
                                requestsPause = requestsPause + requestsPause
                            else:
                                asyncio.create_task(post_request(aioSession, urlStorPost, headersProd, dataStorPost))
                                await asyncio.sleep(requestsPause)
                                last_key = csrf_token
                                logging.info(f"Prod request")
                    if doSaP:
                        for i in range(45):
                                csrf_token = getCsrfForShop2()
                                dataProdPost["key"] = csrf_token
                                responseProdPost = session.post(urlProdPost, headers=headersShop2Post, data=dataProdPost)
                                print(f"{i} - Called PROD request.")
                        for i in range(15):
                                csrf_token = getCsrfForShop2()
                                dataStorPost["key"] = csrf_token
                                responseProdPost = session.post(urlStorPost, headers=headersShop2Post, data=dataStorPost)
                                print(f"{i} - Called STORAGE request")
                    if doCulturePoints:
                        await CP(aioSession)

                    if (doFarmOwnHH or doFarmOwnHL or doFarmOwnLH or doFarmOwnLL or doFarmOwnII or doFarmOwnLI or doFarmOwnLP or doFarmOwnIL or doFarmOwnLS or doFarmOwnB):
                        last_size = len(own_villages[last_count+1:])
                        async with aiohttp.ClientSession() as attackSession:
                            for count, villageId in enumerate(own_villages[last_count+1:], start=last_count+1):
                                key = await getAttackKey(aioSession)
                                #key = getAttackKeySync()

                                if doFarmOwnB:
                                    await attack(aioSession, villageId, key, RomanArmy(Legionars = legionarsAttackAmount))
                                if doFarmOwnHH:
                                    await attack(attackSession, villageId, key, RomanArmy(Ceasaris = horsesAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Ceasaris = horsesBuyAmount))
                                if doFarmOwnHL:
                                    await attack(attackSession, villageId, key, RomanArmy(Ceasaris = horsesAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Legionars = legionarsBuyAmount))
                                if doFarmOwnLL:
                                    await attack(attackSession, villageId, key, RomanArmy(Legionars = legionarsAttackAmount))
                                    await buyTroopsTasks(aioSession, 3, RomanArmy(Legionars = legionarsBuyAmount))
                                if doFarmOwnLH:
                                    await attack(attackSession, villageId, key, RomanArmy(Legionars = legionarsAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Ceasaris = horsesBuyAmount))
                                if doFarmOwnII:
                                    await attack(attackSession, villageId, key, RomanArmy(Imperians = imperiansAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Imperians = imperiansAttackAmount))
                                if doFarmOwnLI:
                                    await attack(attackSession, villageId, key, RomanArmy(Legionars = legionarsAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Imperians = imperiansAttackAmount))
                                if doFarmOwnLP:
                                    await attack(attackSession, villageId, key, RomanArmy(Legionars = legionarsAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Praetorians = praetorians))
                                if doFarmOwnIL:
                                    await attack(attackSession, villageId, key, RomanArmy(Imperians = imperiansAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Legionars = legionarsBuyAmount))
                                if doFarmOwnLS:
                                    await attack(attackSession, villageId, key, RomanArmy(Legionars = legionarsAttackAmount))
                                    await buyTroopsTasks(attackSession, 10, RomanArmy(Scouts = scoutsBuyAmount))

                                if (ownAttacksTimeoutMs > 0):
                                    time.sleep(ownAttacksTimeoutMs/1000)
                                last_count = count
                                if (last_count > last_size):
                                    last_count = -1
                        last_count = -1
                        if once:
                            print("Exiting..")
                            shoudExit = True
                            exit(0)

                    if doSendCatapults:
                        for count, villageId in enumerate(catapults):
                            #for i in range(5):
                            key = getAttackKeySync()
                            attackWithCatapults(villageId, catapultsAmount, catapultsLegionarsCompanion, catapultsHorsesCompanion, numberOfRam, key)
                            print(f"{count} - Send catapults to {villageId}.")
                            if (catapultAttacksTimeoutMs > 0):
                                time.sleep(catapultAttacksTimeoutMs/1000)
            except:
                if shoudExit:
                    exit(1)
                print("An error occurred. Restarting...")
                time.sleep(15)
            print("Begining new cycle.")

#start async event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(main())