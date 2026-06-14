# -*- coding: utf-8 -*-
import json
import os
import re
import sys

# Reconfigure console encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_DIR = os.path.join(BASE_DIR, "german_vocab")
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")

def clean_word(word):
    clean = word.split(',')[0].strip()
    clean = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(.*\)', '', clean).strip()
    return clean

def main():
    res1_path = os.path.join(SCRATCH_DIR, "results1.json")
    res2_path = os.path.join(SCRATCH_DIR, "results2.json")
    
    if not os.path.exists(res1_path) or not os.path.exists(res2_path):
        print("Error: results1.json or results2.json is missing.")
        return
        
    with open(res1_path, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    with open(res2_path, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
        
    # Merge results
    merged_results = {}
    for k, v in data1.items():
        merged_results[clean_word(k)] = v
    for k, v in data2.items():
        merged_results[clean_word(k)] = v
        
    print(f"Loaded {len(merged_results)} fallback word definitions.")
    
    category_files = sorted(
        [f for f in os.listdir(VOCAB_DIR) if f.startswith("category_") and f.endswith(".json")],
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    
    total_updated = 0
    
    for file_name in category_files:
        cat_id = int(re.search(r'\d+', file_name).group())
        if cat_id < 8 or cat_id > 27:
            continue
            
        file_path = os.path.join(VOCAB_DIR, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            cat_data = json.load(f)
            
        words = cat_data.get("words", [])
        updated = False
        
        for w in words:
            cleaned = clean_word(w["word"])
            if cleaned in merged_results:
                w["examples"] = merged_results[cleaned]
                updated = True
                total_updated += 1
                
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cat_data, f, ensure_ascii=False, indent=2)
            print(f"Updated category file: {file_name}")
            
    print(f"Finished updating JSONs. Total words updated: {total_updated}")

if __name__ == "__main__":
    main()
