# -*- coding: utf-8 -*-
import json
import os
import re
import time
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

# Configure stdout for Windows UTF-8 encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_DIR = os.path.join(BASE_DIR, "german_vocab")
CACHE_FILE = os.path.join(BASE_DIR, "reverso_cache.json")

# User agents rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
]

def clean_word(word):
    # 'der Projektauftrag, die Projektaufträge' -> 'Projektauftrag'
    clean = word.split(',')[0].strip()
    clean = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(.*\)', '', clean).strip()
    return clean

# Load cache
cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} words from cache.")
    except Exception as e:
        print(f"Error loading cache: {e}")

# Save cache helper
def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def fetch_reverso_sentences(word):
    cleaned = clean_word(word)
    if not cleaned:
        return []
        
    # Check cache first
    if cleaned in cache:
        return cache[cleaned]

    url = f"https://context.reverso.net/translation/german-russian/{requests.utils.quote(cleaned)}"
    
    retries = 3
    for attempt in range(retries):
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3'
        }
        
        try:
            # Random delay before request to prevent rate limiting
            time.sleep(random.uniform(1.0, 3.0))
            
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                examples_divs = soup.find_all('div', class_='example')
                
                results = []
                for ex in examples_divs:
                    src = ex.find('div', class_='src')
                    trg = ex.find('div', class_='trg')
                    if src and trg:
                        de_text = src.text.strip()
                        ru_text = trg.text.strip()
                        
                        # Remove excessive whitespace/newlines
                        de_text = re.sub(r'\s+', ' ', de_text)
                        ru_text = re.sub(r'\s+', ' ', ru_text)
                        
                        # Clean up formatting issues
                        de_text = de_text.replace(" \n", "").strip()
                        ru_text = ru_text.replace(" \n", "").strip()
                        
                        if de_text and ru_text:
                            results.append({"de": de_text, "ru": ru_text})
                            
                if len(results) >= 3:
                    # Successfully parsed at least 3 sentences
                    # Cache and return (up to 5)
                    cache[cleaned] = results[:5]
                    return results[:5]
                else:
                    # Reverso has no/few examples for this specific term
                    return []
            elif r.status_code == 429:
                # Too Many Requests
                print(f"Rate limited (429) on '{cleaned}'. Sleeping 20s (attempt {attempt+1}/{retries})...")
                time.sleep(20)
            elif r.status_code == 403 or r.status_code == 404:
                # 403 Forbidden or 404 Not Found
                return []
            else:
                print(f"Failed to fetch '{cleaned}' (HTTP {r.status_code}, attempt {attempt+1}/{retries})")
                time.sleep(5)
        except Exception as e:
            print(f"Exception on '{cleaned}': {e} (attempt {attempt+1}/{retries})")
            time.sleep(5)
            
    # If all retries failed, return empty list (will keep the original template examples)
    return []

def main():
    print("Starting Reverso Context vocabulary enrichment...")
    
    # 1. Gather all words from category files (8 to 27)
    words_to_enrich = [] # list of (file_path, word_idx, word_string, original_examples)
    
    category_files = sorted(
        [f for f in os.listdir(VOCAB_DIR) if f.startswith("category_") and f.endswith(".json")],
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    
    for file_name in category_files:
        cat_id = int(re.search(r'\d+', file_name).group())
        if cat_id < 8 or cat_id > 27:
            continue
            
        file_path = os.path.join(VOCAB_DIR, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                category_name = data.get("category", "")
                words = data.get("words", [])
                for idx, w in enumerate(words):
                    words_to_enrich.append((file_path, idx, w["word"], w.get("examples", [])))
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    total_words = len(words_to_enrich)
    print(f"Found {total_words} words across categories 8-27 to check.")
    
    # 2. Filter out words already present in cache
    pending_words = []
    for item in words_to_enrich:
        file_path, idx, word, orig_examples = item
        cleaned = clean_word(word)
        if cleaned not in cache:
            pending_words.append(item)
            
    print(f"{total_words - len(pending_words)} words are already cached. {len(pending_words)} words need fetching.")
    
    # 3. Fetch in parallel using ThreadPoolExecutor
    max_threads = 4  # Keep it moderate to prevent IP bans
    processed_count = 0
    save_counter = 0
    
    if pending_words:
        print(f"Fetching sentences using {max_threads} parallel threads...")
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_word = {executor.submit(fetch_reverso_sentences, item[2]): item for item in pending_words}
            
            for future in as_completed(future_to_word):
                item = future_to_word[future]
                word = item[2]
                processed_count += 1
                save_counter += 1
                
                try:
                    res = future.result()
                    if res:
                        print(f"[{processed_count}/{len(pending_words)}] Successfully fetched '{clean_word(word)}' ({len(res)} sentences)")
                    else:
                        print(f"[{processed_count}/{len(pending_words)}] No sentences found for '{clean_word(word)}' (using templates fallback)")
                except Exception as e:
                    print(f"Error processing future for '{word}': {e}")
                    
                # Save cache incrementally
                if save_counter >= 15:
                    save_cache()
                    save_counter = 0
        
        # Save final cache
        save_cache()
        print("All HTTP fetching completed.")
    else:
        print("No new words to fetch from Reverso Context.")

    # 4. Update the JSON files with fetched sentences
    print("Updating category files with real example sentences...")
    
    # Group the gathered word items by file_path
    files_to_update = {}
    for item in words_to_enrich:
        file_path, idx, word, orig_examples = item
        if file_path not in files_to_update:
            files_to_update[file_path] = []
        files_to_update[file_path].append(item)
        
    for file_path, items in files_to_update.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            words = data.get("words", [])
            updated_count = 0
            
            for item in items:
                file_path, idx, word, orig_examples = item
                cleaned = clean_word(word)
                
                # If we have scraped sentences in the cache, replace them
                if cleaned in cache and cache[cleaned]:
                    words[idx]["examples"] = cache[cleaned]
                    updated_count += 1
                    
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"Updated {updated_count}/{len(items)} words in {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error updating file {file_path}: {e}")
            
    print("Reverso Context enrichment phase complete!")

if __name__ == "__main__":
    main()
