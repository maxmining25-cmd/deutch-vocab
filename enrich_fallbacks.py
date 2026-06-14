# -*- coding: utf-8 -*-
import json
import os
import re
import time
import random
import urllib.parse
import sys
import requests
from bs4 import BeautifulSoup

# Reconfigure console encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_DIR = os.path.join(BASE_DIR, "german_vocab")
CACHE_FILE = os.path.join(BASE_DIR, "reverso_cache.json")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

# Load cache
cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except Exception as e:
        print(f"Error loading cache: {e}")

def save_cache():
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
            time.sleep(2)
        except Exception as e:
            print(f"Translation exception: {e}")
            time.sleep(2)
    return None

def fetch_dwds_sentences(word):
    cleaned = clean_word(word)
    if not cleaned:
        return []
        
    url = f"https://www.dwds.de/wb/{urllib.parse.quote(cleaned)}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS)
    }
    
    try:
        time.sleep(random.uniform(1.0, 2.0))
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            divs = soup.find_all(class_='dwdswb-belegtext')
            
            sentences = []
            seen = set()
            for div in divs:
                text = div.text.strip()
                text = re.sub(r'\s+', ' ', text)
                if text and text not in seen and len(text) > 15:
                    seen.add(text)
                    sentences.append(text)
            return sentences[:5]
    except Exception as e:
        print(f"DWDS exception for '{cleaned}': {e}")
    return []

def fetch_reverso_sentences(word):
    cleaned = clean_word(word)
    if not cleaned:
        return []
        
    url = f"https://context.reverso.net/translation/german-russian/{urllib.parse.quote(cleaned)}"
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3'
    }
    
    try:
        time.sleep(random.uniform(2.0, 4.0))
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            examples_divs = soup.find_all('div', class_='example')
            
            results = []
            for ex in examples_divs:
                src = ex.find('div', class_='src')
                trg = ex.find('div', class_='trg')
                if src and trg:
                    de_text = re.sub(r'\s+', ' ', src.text.strip())
                    ru_text = re.sub(r'\s+', ' ', trg.text.strip())
                    if de_text and ru_text:
                        results.append({"de": de_text, "ru": ru_text})
            if len(results) >= 3:
                return results[:5]
    except Exception as e:
        print(f"Reverso exception for '{cleaned}': {e}")
    return []

def is_template(examples):
    if not examples:
        return True
        
    template_indicators = [
        "проанализировать следующий объект:",
        "согласны с тем, что касается понятия:",
        "концентрируемся на теме:",
        "решающую роль в успехе",
        "этот вопрос непосредственно в команде.",
        "необходимые документы незамедлительно.",
        "всё это очень профессионально.",
        "(в прошедшем времени) эту тему.",
        "выполните действие:",
        "Этот процесс действительно",
        "Очень важно, чтобы всё оставалось",
        "работаем особенно",
        "Полученный результат очень",
        "Я лично нахожу этот стиль работы"
    ]
    
    for ex in examples:
        ru = ex.get("ru", "")
        de = ex.get("de", "")
        for indicator in template_indicators:
            if indicator in ru:
                return True
        if de.strip().startswith("Hier ist ") and len(de.strip().split()) <= 4:
            return True
            
    return False

def get_real_sentences(word):
    cleaned = clean_word(word)
    
    # 1. Try Reverso first (it might succeed if we query slowly or retry)
    sentences = fetch_reverso_sentences(word)
    if sentences:
        print(f"  [Reverso] Successfully fetched {len(sentences)} sentences.")
        return sentences
        
    # 2. Try DWDS + Google Translate
    de_sentences = fetch_dwds_sentences(word)
    if de_sentences:
        sentences = []
        for de_s in de_sentences:
            ru_s = translate_to_russian(de_s)
            if ru_s:
                sentences.append({"de": de_s, "ru": ru_s})
        if len(sentences) >= 2:
            print(f"  [DWDS+Translate] Successfully fetched {len(sentences)} sentences.")
            return sentences
            
    # 3. Try simplified query on Reverso (e.g. if it is a compound like "physische Bestand", search "Bestand")
    if " " in cleaned:
        parts = cleaned.split()
        for part in reversed(parts):
            if len(part) > 3:
                sentences = fetch_reverso_sentences(part)
                if sentences:
                    print(f"  [Reverso Simplified '{part}'] Successfully fetched {len(sentences)} sentences.")
                    return sentences
                    
    return []

def main():
    category_files = sorted(
        [f for f in os.listdir(VOCAB_DIR) if f.startswith("category_") and f.endswith(".json")],
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    
    total_enriched = 0
    
    for file_name in category_files:
        cat_id = int(re.search(r'\d+', file_name).group())
        if cat_id < 8 or cat_id > 27:
            continue
            
        file_path = os.path.join(VOCAB_DIR, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        category_name = data.get("category", "")
        words = data.get("words", [])
        
        updated = False
        print(f"\nProcessing {file_name} ({category_name})...")
        
        for idx, w in enumerate(words):
            if is_template(w.get("examples", [])):
                word_str = w["word"]
                print(f"Enriching fallback word: '{word_str}'")
                
                # Check cache first
                cleaned = clean_word(word_str)
                if cleaned in cache and cache[cleaned]:
                    w["examples"] = cache[cleaned]
                    updated = True
                    total_enriched += 1
                    print(f"  [Cache] Loaded from cache.")
                    continue
                    
                sentences = get_real_sentences(word_str)
                if sentences:
                    w["examples"] = sentences
                    cache[cleaned] = sentences
                    updated = True
                    total_enriched += 1
                    # Save cache incrementally
                    save_cache()
                else:
                    print(f"  [Failed] Could not find real sentences for '{word_str}'.")
                    
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved changes to {file_name}")
            
    print(f"\nEnrichment finished. Total words enriched: {total_enriched}")

if __name__ == "__main__":
    main()
