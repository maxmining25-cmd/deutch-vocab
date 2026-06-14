# -*- coding: utf-8 -*-
import json
import os
import re
import time
import urllib.parse
import sys
import requests
import codecs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_DIR = os.path.join(BASE_DIR, "german_vocab")
CACHE_FILE = os.path.join(BASE_DIR, "youglish_sap_cache.json")

# Thread safety lock
cache_lock = threading.Lock()
file_lock = threading.Lock()

# Load Cache
cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except Exception as e:
        print(f"Error loading cache: {e}")

def save_cache():
    with cache_lock:
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

def clean_word(word):
    clean = word.split(',')[0].strip()
    clean = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(.*\)', '', clean).strip()
    return clean

def translate_to_russian(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=de&tl=ru&dt=t&q={urllib.parse.quote(text)}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                res = r.json()
                translation = ""
                for part in res[0]:
                    if part[0]:
                        translation += part[0]
                return translation.strip()
        except Exception as e:
            pass
        time.sleep(0.5 + random.random())
    return ""

def fetch_youglish_sentence(word):
    clean = clean_word(word)
    url = f"https://de.youglish.com/pronounce/{urllib.parse.quote(clean)}/german"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            match = re.search(r"params\.jsonData\s*=\s*'(.*?)';", r.text, re.DOTALL)
            if match:
                json_str_raw = match.group(1).replace("\\'", "'")
                try:
                    json_str = codecs.escape_decode(json_str_raw.encode('utf-8'))[0].decode('utf-8')
                    data = json.loads(json_str)
                    results = data.get("results", [])
                    for item in results:
                        display_text = item.get("display")
                        if display_text:
                            display_text = re.sub(r'\s+', ' ', display_text).strip()
                            if re.search(r'\b' + re.escape(clean) + r'\w*\b', display_text, re.IGNORECASE):
                                if 20 < len(display_text) < 250:
                                    return display_text
                except Exception as je:
                    pass
    except Exception as e:
        print(f"YouGlish scrape error for {clean}: {e}")
    return None

def process_word(w, file_path):
    word_val = w.get("word", "")
    clean_w = clean_word(word_val)
    
    # Check cache first
    with cache_lock:
        cached = cache.get(clean_w)
        
    if cached:
        if cached.get("status") == "success":
            ex_de = cached.get("de")
            ex_ru = cached.get("ru")
            with file_lock:
                exists = any(ex.get("de") == ex_de for ex in w.get("examples", []))
                if not exists and ex_de and ex_ru:
                    w["examples"].append({
                        "de": ex_de,
                        "ru": ex_ru,
                        "source": "YouGlish"
                    })
                    return True
        return False
        
    # Not cached, fetch from YouGlish
    sentence_de = fetch_youglish_sentence(word_val)
    
    # Random sleep to prevent blocking
    time.sleep(0.5 + random.random() * 1.5)
    
    if sentence_de:
        sentence_ru = translate_to_russian(sentence_de)
        if sentence_ru:
            # Add to cache
            with cache_lock:
                cache[clean_w] = {
                    "status": "success",
                    "de": sentence_de,
                    "ru": sentence_ru,
                    "source": "YouGlish"
                }
            # Add to examples
            with file_lock:
                w["examples"].append({
                    "de": sentence_de,
                    "ru": sentence_ru,
                    "source": "YouGlish"
                })
            return True
            
    with cache_lock:
        cache[clean_w] = {"status": "not_found"}
    return False

def main():
    category_files = sorted(
        [f for f in os.listdir(VOCAB_DIR) if f.startswith("category_") and f.endswith(".json")],
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    
    print("Starting Optimized Concurrent YouGlish Example Enrichment...")
    
    # Process files sequentially, but words inside each file concurrently
    for file_name in category_files:
        cat_id = int(re.search(r'\d+', file_name).group())
        
        # Categories 1-22 are general words
        if cat_id < 1 or cat_id > 22:
            continue
            
        file_path = os.path.join(VOCAB_DIR, file_name)
        print(f"\nProcessing {file_name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        words = data.get("words", [])
        
        # Run words concurrently with 6 threads
        updated = False
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(process_word, w, file_path): w for w in words}
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        updated = True
                except Exception as exc:
                    print(f"Exception during word process: {exc}")
                    
        # Save cache and updated JSON
        save_cache()
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved updates to {file_name}")
            
    print("\nYouGlish enrichment completed successfully!")

if __name__ == "__main__":
    main()
