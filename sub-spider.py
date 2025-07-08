#!/usr/bin/env python3

import asyncio
import aiohttp
import sys
import aiodns
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings
from colorama import Fore, Style, init
import requests
import os
from urllib.parse import urlparse, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
init(autoreset=True)

TIMEOUT = 5
CONCURRENT_REQUESTS = 300
HEADERS = {'User-Agent': 'CatHaxor-Tool/1.2'}
sem_http = asyncio.Semaphore(CONCURRENT_REQUESTS)
sem_dns = asyncio.Semaphore(CONCURRENT_REQUESTS)

OUTPUT_SUB_FILE = "found.txt"
OUTPUT_PARAM_FILE = "params_found.txt"
found_subdomains = []

SEC_SUBDOMAIN_LIST_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-5000.txt"
SEC_PARAM_LIST_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/burp-parameter-names.txt"

SCRIPT_URL = "https://raw.githubusercontent.com/cathaxor/sub-spider/main/sub-spider.py"
SCRIPT_LOCAL = os.path.abspath(__file__)

def print_banner():
    banner = f"""
{Style.BRIGHT + Fore.CYAN}
░█▀▀▀█ ░█─░█ ░█▀▀█ ── ░█▀▀▀█ ░█▀▀█ ▀█▀ ░█▀▀▄ ░█▀▀▀ ░█▀▀█ 
─▀▀▀▄▄ ░█─░█ ░█▀▀▄ ▀▀ ─▀▀▀▄▄ ░█▄▄█ ░█─ ░█─░█ ░█▀▀▀ ░█▄▄▀ 
░█▄▄▄█ ─▀▄▄▀ ░█▄▄█ ── ░█▄▄▄█ ░█─── ▄█▄ ░█▄▄▀ ░█▄▄▄ ░█─░█
{Style.RESET_ALL}
{Style.BRIGHT + Fore.CYAN}🔍 SUB-SPIDER Subdomain & Parameter Finder | Created by: Abdulla Rahaman{Style.RESET_ALL}
"""
    print(banner)

def get_title(html):
    try:
        soup = BeautifulSoup(html, "xml")
        return soup.title.string.strip() if soup.title else "No Title"
    except:
        return "No Title"

async def dns_resolves(resolver, host):
    try:
        async with sem_dns:
            await resolver.gethostbyname(host, family=aiodns.socket.AF_INET)
            return True
    except:
        return False

async def fetch(session, url):
    try:
        async with sem_http:
            async with session.get(url, timeout=ClientTimeout(total=TIMEOUT), allow_redirects=True) as resp:
                if resp.status < 400:
                    found_subdomains.append(url)
                    print(f"{Fore.GREEN}{url}")
    except:
        pass

async def download_wordlist(url):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                text = await resp.text()
                return [line.strip() for line in text.splitlines() if line.strip()]
            return []

async def run_subdomain_scan():
    domains_input = input(f"{Style.BRIGHT + Fore.CYAN}Enter domain(s) (comma separated): {Style.RESET_ALL}").strip()
    if not domains_input:
        return
    base_domains = [d.strip() for d in domains_input.split(",") if d.strip()]
    sub_prefixes = await download_wordlist(SEC_SUBDOMAIN_LIST_URL)

    subdomains = [f"{prefix}.{domain}" for domain in base_domains for prefix in sub_prefixes]

    resolver = aiodns.DNSResolver()
    resolved = []

    async def check(sub):
        if await dns_resolves(resolver, sub):
            resolved.append(sub)

    await asyncio.gather(*[check(s) for s in subdomains])

    urls = [f"http://{s}" for s in resolved] + [f"https://{s}" for s in resolved]

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        await asyncio.gather(*[fetch(session, u) for u in urls])

    if found_subdomains:
        with open(OUTPUT_SUB_FILE, 'w') as f:
            for sub in found_subdomains:
                f.write(sub + '\n')

def run_param_finder():
    base_url = input(f"{Style.BRIGHT + Fore.CYAN}Enter base URL (e.g. https://site.com/page.php): {Style.RESET_ALL}").strip()
    if not base_url:
        return

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        print(f"{Fore.RED}Invalid URL format.")
        return

    param_list = requests.get(SEC_PARAM_LIST_URL).text.splitlines()
    valid_urls = []

    def test_param(param):
        try:
            full_url = base_url + ("&" if "?" in base_url else "?") + urlencode({param: '2'})
            resp = requests.get(full_url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code < 400:
                print(f"{Fore.GREEN}{full_url}")
                return full_url
        except:
            return None

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(test_param, param) for param in param_list]
        for future in as_completed(futures):
            result = future.result()
            if result:
                valid_urls.append(result)

    if valid_urls:
        with open(OUTPUT_PARAM_FILE, 'w') as f:
            for url in valid_urls:
                f.write(url + '\n')

def self_update():
    print(f"{Fore.CYAN}Updating script from GitHub...")
    try:
        r = requests.get(SCRIPT_URL)
        if r.status_code == 200:
            with open(SCRIPT_LOCAL, 'w') as f:
                f.write(r.text)
            print(f"{Fore.GREEN}Update successful. Please rerun the script.")
        else:
            print(f"{Fore.RED}Failed to update script.")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")

def main_menu():
    options = [
        ("1. Subdomain Discover", Fore.CYAN),
        ("2. Parameter Finder", Fore.YELLOW),
        ("3. Update Tool", Fore.GREEN),
        ("0. Exit", Fore.RED)
    ]
    while True:
        print(f"\n{Style.BRIGHT + Fore.MAGENTA}Select a Tool:{Style.RESET_ALL}")
        for text, color in options:
            print(color + text + Style.RESET_ALL)
        choice = input(f"{Style.BRIGHT + Fore.CYAN}Enter choice: {Style.RESET_ALL}").strip()

        if choice == '1':
            asyncio.run(run_subdomain_scan())
        elif choice == '2':
            run_param_finder()
        elif choice == '3':
            self_update()
        elif choice == '0':
            sys.exit()
        else:
            print(f"{Fore.RED}Invalid option.")

if __name__ == "__main__":
    print_banner()
    main_menu()
