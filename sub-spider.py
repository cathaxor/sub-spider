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

# Suppress XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

init(autoreset=True)

TIMEOUT = 5
CONCURRENT_REQUESTS = 150
HEADERS = {'User-Agent': 'CatHaxor-SubdomainFinder/1.2'}
sem_http = asyncio.Semaphore(CONCURRENT_REQUESTS)
sem_dns = asyncio.Semaphore(CONCURRENT_REQUESTS)
OUTPUT_FILE = "found.txt"
found_subdomains = []

SEC_LISTS_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-5000.txt"

# *** UPDATE SETTINGS ***
SCRIPT_URL = "https://raw.githubusercontent.com/cathaxor/sub-spider/main/sub-spider.py"
SCRIPT_LOCAL = os.path.abspath(__file__)  # Current script path

def print_banner():
    banner = f"""{Fore.CYAN}
░█▀▀█ ─█▀▀█ ▀▀█▀▀ ░█─░█ ─█▀▀█ ▀▄░▄▀ ░█▀▀▀█ ░█▀▀█
░█─── ░█▄▄█ ─░█── ░█▀▀█ ░█▄▄█ ─░█── ░█──░█ ░█▄▄▀
░█▄▄█ ░█─░█ ─░█── ░█─░█ ░█─░█ ▄▀░▀▄ ░█▄▄▄█ ░█─░█
{Style.RESET_ALL}
🔍 CatHaxor Subdomain Finder | Created by: Cathaxor
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
    except aiodns.error.DNSError:
        return False

async def fetch(session, url):
    try:
        async with sem_http:
            async with session.get(url, timeout=ClientTimeout(total=TIMEOUT), allow_redirects=True) as resp:
                raw_bytes = await resp.read()
                encoding = resp.charset or 'utf-8'
                try:
                    text = raw_bytes.decode(encoding)
                except UnicodeDecodeError:
                    text = raw_bytes.decode('latin-1', errors='ignore')

                title = get_title(text)

                if resp.status < 400:
                    found_subdomains.append(url)
                    print(f"{Fore.GREEN}[{resp.status}] {url} - {title}")
                else:
                    print(f"{Fore.YELLOW}[{resp.status}] {url} - {title}")
    except Exception as e:
        print(f"{Fore.RED}[-] Failed: {url} - {e}")

async def download_wordlist(url):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            async with session.get(url, timeout=ClientTimeout(total=TIMEOUT)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return [line.strip() for line in text.splitlines() if line.strip()]
                else:
                    print(f"{Fore.RED}[!] Failed to download wordlist from {url} (Status: {resp.status})")
                    return []
        except Exception as e:
            print(f"{Fore.RED}[!] Exception while downloading wordlist: {e}")
            return []

async def run(domains_file):
    urls = []

    # Read base domains from file
    with open(domains_file, 'r') as f:
        base_domains = [line.strip() for line in f if line.strip()]

    # Download subdomain prefixes from SecLists
    print(f"{Fore.CYAN}[i] Downloading subdomain wordlist from SecLists...")
    sub_prefixes = await download_wordlist(SEC_LISTS_URL)
    if not sub_prefixes:
        print(f"{Fore.RED}[!] Could not get subdomain wordlist. Exiting.")
        return

    # Generate full subdomains
    subdomains = []
    for domain in base_domains:
        for prefix in sub_prefixes:
            subdomains.append(f"{prefix}.{domain}")

    print(f"{Fore.CYAN}[i] Checking DNS resolution of {len(subdomains)} subdomains...")

    resolver = aiodns.DNSResolver()
    resolved_subdomains = []

    async def check_dns(sub):
        if await dns_resolves(resolver, sub):
            resolved_subdomains.append(sub)

    dns_tasks = [check_dns(sub) for sub in subdomains]
    await asyncio.gather(*dns_tasks)

    print(f"{Fore.CYAN}[i] {len(resolved_subdomains)} subdomains resolved. Starting HTTP checks...")

    # Build urls list for HTTP/HTTPS
    for sub in resolved_subdomains:
        urls.append(f"http://{sub}")
        urls.append(f"https://{sub}")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = [fetch(session, url) for url in urls]
        await asyncio.gather(*tasks)

    if found_subdomains:
        with open(OUTPUT_FILE, 'w') as f:
            for sub in found_subdomains:
                f.write(sub + '\n')
        print(f"\n{Fore.CYAN}[✓] Saved live subdomains to {OUTPUT_FILE}\n")
    else:
        print(f"\n{Fore.RED}[!] No live subdomains found.\n")

def self_update():
    print("🛠️ Updating main script from remote source...")
    try:
        resp = requests.get(SCRIPT_URL, timeout=10)
        resp.raise_for_status()
        script_code = resp.text

        # Backup current script before overwrite
        backup_path = SCRIPT_LOCAL + ".backup"
        with open(SCRIPT_LOCAL, 'r', encoding='utf-8') as f:
            current_code = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_code)
        print(f"📦 Backup of current script saved as {backup_path}")

        # Write new script code
        with open(SCRIPT_LOCAL, 'w', encoding='utf-8') as f:
            f.write(script_code)

        print("✅ Script updated successfully! Please re-run the script.")
    except Exception as e:
        print(f"❌ Update failed: {e}")

if __name__ == "__main__":
    print_banner()

    if len(sys.argv) == 2 and sys.argv[1].lower() == "update":
        self_update()
        sys.exit(0)

    if len(sys.argv) != 2:
        print(f"{Fore.YELLOW}Usage: python3 {sys.argv[0]} domains.txt")
        print(f"{Fore.YELLOW}Or to update: python3 {sys.argv[0]} update")
        sys.exit(1)

    domains_file = sys.argv[1]
    asyncio.run(run(domains_file))
