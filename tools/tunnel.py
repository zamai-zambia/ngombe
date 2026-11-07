"""Open the Cloudflare quick tunnel to the self-hosted Supabase on this machine and tell the app where it is.
   python tools/cattle-demo/tunnel.py            runs until stopped; restarts the tunnel if it dies
Reads DESK_KEY from zamai-pro/.env.local (the Beelink status page key) and the anon key from ZamaiPort/.env.local.
Posts the address to https://ngombe.zamai.pro/api-url (netlify/functions/ngombe-api-url.mjs).
"""
import os, re, subprocess, sys, time, json, urllib.request
CLOUDFLARED = r"C:/Users/Chris/tools/cloudflared.exe"
LOCAL = "http://localhost:8000"
POST = "https://ngombe.zamai.pro/api-url"
env = {}
for f in (r"C:/Users/Chris/projects/ZamaiPort/.env.local", r"C:/Users/Chris/projects/zamai-pro/.env.local"):
    for l in open(f, encoding="utf-8").read().splitlines():
        if "=" in l and not l.startswith("#"): k, v = l.split("=", 1); env.setdefault(k.strip(), v.strip())
KEY = env.get("DESK_KEY"); ANON = env.get("NGOMBE_SUPABASE_ANON_KEY")
if not KEY: sys.exit("DESK_KEY missing in .env.local")

def publish(url):
    req = urllib.request.Request(POST, data=json.dumps({"url": url, "anon": ANON}).encode(), headers={"Content-Type": "application/json", "x-desk-key": KEY}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r: print("published", url, r.status, flush=True)

while True:
    p = subprocess.Popen([CLOUDFLARED, "tunnel", "--url", LOCAL, "--no-autoupdate"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    url = None
    for line in p.stdout:
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m and not url:
            url = m.group(0)
            try: publish(url)
            except Exception as e: print("publish failed", e, flush=True)
    print("tunnel ended; restarting in 10 s", flush=True); time.sleep(10)
