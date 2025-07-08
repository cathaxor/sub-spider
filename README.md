# SubSpider

**SubSpider** is an all-in-one fast and efficient tool to:

* 🔍 Discover live subdomains
* 📎 Detect URL parameters (for testing fuzzing/bypass)
* 🔄 Self-update from GitHub

Created by: **Abdulla Rahaman**

---

## 🚀 Features

* Fast DNS resolution with `aiodns`
* Asynchronous and multithreaded performance
* Parameter discovery using SecLists
* Easy update system from GitHub
* Clean CLI menu with color support

---
## 🛠️ INSTALL
```bash
git clone https://github.com/cathaxor/param-finder.git
cd param-finder
```
## 🛠️ Requirements

```bash
pip install --break-system-packages -r requirements.txt
```

**requirements.txt**

```
aiohttp
aiodns
colorama
bs4
requests
```

---

## 📦 Usage

```bash
python3 sub-spider.py
```

### Menu Options:

```
1. Subdomain Discover
2. Parameter Finder
3. Update Tool
0. Exit
```

---

## 🔍 Subdomain Discover

Enter a domain (or multiple separated by commas). Example:

```
canva.com, google.com
```

Subdomains are resolved via DNS and checked over HTTP/HTTPS.

Results are saved to `found.txt`.

---

## 📎 Parameter Finder

Provide a base URL like:

```
https://site.com/page.php
```

Tool will fuzz parameters from SecLists.

Results are saved to `params_found.txt`.

---

## 🔄 Update

To update the script from GitHub (if changes are pushed):

```
Select option 3 from menu.
```

---

## 📁 Project Structure

```
sub-spider.py        # Main script
found.txt            # Live subdomains output
params_found.txt     # Discovered parameters output
requirements.txt     # Dependencies
README.md            # You are here
```

---

## 🧠 Credits

* [SecLists](https://github.com/danielmiessler/SecLists)
* [ProjectDiscovery subfinder](https://github.com/projectdiscovery/subfinder) (inspiration)

---

## 🧪 Disclaimer

Use responsibly. Only scan domains you own or are authorized to test.

---

## 🌐 GitHub

GitHub Repository: [https://github.com/cathaxor/sub-spider](https://github.com/cathaxor/sub-spider)
