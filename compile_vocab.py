import json
import os
import re
import csv
import unicodedata
import sys

def main():
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vocab_dir = os.path.join(base_dir, "german_vocab")
    
    words_by_category = {}
    all_words = []
    seen_words = set()
    duplicates_count = 0
    
    # 1. Read the JSON files dynamically
    category_files = sorted(
        [f for f in os.listdir(vocab_dir) if f.startswith("category_") and f.endswith(".json")],
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    for file_name in category_files:
        file_path = os.path.join(vocab_dir, file_name)
        cat_id = re.search(r'\d+', file_name).group()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                category_name = data.get("category", f"Kategorie {cat_id}")
                words_in_cat = data.get("words", [])
                
                unique_words_in_cat = []
                for w in words_in_cat:
                    # Normalize word for duplicate check (remove articles like 'der ', 'die ', 'das ', and leading/trailing whitespace)
                    raw_word = w.get("word", "").strip()
                    norm_word = re.sub(r'^(der|die|das|den|dem|des)\s+', '', raw_word, flags=re.IGNORECASE).lower()
                    
                    if norm_word in seen_words:
                        print(f"Duplicate word found and skipped: {raw_word} (Category: {category_name})")
                        duplicates_count += 1
                        continue
                    
                    seen_words.add(norm_word)
                    unique_words_in_cat.append(w)
                    all_words.append({**w, "category_name": category_name})
                
                words_by_category[category_name] = unique_words_in_cat
                print(f"Loaded {len(unique_words_in_cat)} unique words from Category {cat_id}: '{category_name}'")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    total_words = len(all_words)
    print(f"\nTotal unique words loaded: {total_words} (Skipped {duplicates_count} duplicates)")
    
    if total_words == 0:
        print("No words found! Exiting.")
        return

    # 2. Generate Markdown File
    md_path = os.path.join(base_dir, "projektmanagement_wortschatz.md")
    generate_markdown(words_by_category, md_path)
    print(f"Markdown file generated at: {md_path}")
    
    # 3. Generate Interactive HTML File
    html_path = os.path.join(base_dir, "projektmanagement_wortschatz.html")
    generate_html(all_words, list(words_by_category.keys()), html_path)
    print(f"HTML file generated at: {html_path}")

    # 4. Generate Anki Cards File
    anki_path = os.path.join(base_dir, "projektmanagement_anki.txt")
    generate_anki(all_words, anki_path)
    print(f"Anki cards file generated at: {anki_path}")

def generate_markdown(words_by_category, md_path):
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# B1-B2 Deutsch Wortschatz (Projektmanagement, Finanzen, Bewerbung, Ämter & Alltag)\n\n")
        f.write("Этот список содержит ключевые слова и выражения на немецком языке по четырем темам: управление проектами, финансы и бухгалтерия, собеседование при приеме на работу, а также общение в ведомствах и повседневной жизни (уровни B1-B2). ")
        f.write("Слова разбиты по категориям, для каждого слова приводится перевод на русский и английский языки, а также 5 примеров использования в контексте.\n\n")
        
        # Table of Contents
        f.write("## Содержание\n\n")
        for i, category in enumerate(words_by_category.keys(), 1):
            anchor = category.lower().replace(" ", "-").replace(",", "").replace("&", "").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
            # Clean anchor from special chars
            anchor = re.sub(r'[^a-z0-9\-]', '', anchor)
            f.write(f"{i}. [{category}](#{anchor})\n")
        f.write("\n---\n\n")
        
        # Categories and Words
        word_index = 1
        for category, words in words_by_category.items():
            anchor = category.lower().replace(" ", "-").replace(",", "").replace("&", "").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
            anchor = re.sub(r'[^a-z0-9\-]', '', anchor)
            
            f.write(f"## <a name=\"{anchor}\"></a>{category}\n\n")
            
            for w in words:
                import urllib.parse
                word = w.get("word", "")
                pos = w.get("part_of_speech", "")
                level = w.get("level", "")
                ru = w.get("translation_ru", "")
                en = w.get("translation_en", "")
                examples = w.get("examples", [])
                synonyms = w.get("synonyms", [])
                
                clean_w = word.split(',')[0].strip()
                clean_w = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean_w, flags=re.IGNORECASE).strip()
                yg_link = f"https://de.youglish.com/pronounce/{urllib.parse.quote(clean_w)}/german"
                
                f.write(f"### {word_index}. {word} [🎥 YouGlish]({yg_link})\n")
                f.write(f"- **Часть речи (Part of Speech):** {pos}\n")
                f.write(f"- **Уровень (Level):** {level}\n")
                f.write(f"- **Перевод (RU):** {ru}\n")
                if en:
                    f.write(f"- **Translation (EN):** {en}\n")
                if synonyms:
                    f.write(f"- **Синонимы (Synonyme):** {', '.join(synonyms)}\n")
                antonyms = w.get("antonyms", [])
                if antonyms:
                    f.write(f"- **Антонимы (Antonyme):** {', '.join(antonyms)}\n")
                    
                if pos == "Verb":
                    partizip_2 = w.get("partizip_2", "")
                    imperative = w.get("imperative", "")
                    prepositions = w.get("prepositions", [])
                    conj = w.get("conjugations", {})
                    if partizip_2:
                        f.write(f"- **Partizip II:** {partizip_2}\n")
                    if imperative:
                        f.write(f"- **Императив (Imperativ):** {imperative}\n")
                    if prepositions:
                        f.write(f"- **Управление / Предлоги (Prepositionen):** {', '.join(prepositions)}\n")
                    if conj:
                        conj_str = f"ich *{conj.get('ich', '')}*, du *{conj.get('du', '')}*, er/sie/es *{conj.get('er/sie/es', '')}*, wir *{conj.get('wir', '')}*, ihr *{conj.get('ihr', '')}*, sie/Sie *{conj.get('sie/Sie', '')}*"
                        f.write(f"- **Спряжение (Konjugation - Präsens):** {conj_str}\n")
                
                f.write("- **Примеры использования (Beispiele):**\n")
                for j, ex in enumerate(examples, 1):
                    de_ex = ex.get("de", "")
                    ru_ex = ex.get("ru", "")
                    f.write(f"  {j}. *{de_ex}*\n")
                    f.write(f"     ➔ {ru_ex}\n")
                f.write("\n")
                word_index += 1
            f.write("\n---\n\n")

def generate_anki(all_words, anki_path):
    with open(anki_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        for w in all_words:
            word = w.get("word", "")
            pos = w.get("part_of_speech", "")
            level = w.get("level", "")
            cat = w.get("category_name", "")
            ru = w.get("translation_ru", "")
            en = w.get("translation_en", "")
            examples = w.get("examples", [])
            synonyms = w.get("synonyms", [])
            
            clean_word_val = word.split(',')[0].strip()
            clean_word_val = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean_word_val, flags=re.IGNORECASE).strip()
            
            # Level color
            lvl_color = "#10b981" if level.upper() == "B1" else "#f59e0b"
            
            # Front HTML
            front_html = (
                f'<div style="font-family: \'Plus Jakarta Sans\', Arial, sans-serif; text-align: center; padding: 25px; '
                f'background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">'
                f'<div style="font-size: 0.9em; color: #6366f1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">{cat}</div>'
                f'<div style="margin-bottom: 15px; display: flex; align-items: center; justify-content: center; gap: 8px;">'
                f'<span style="font-size: 2.2em; font-weight: 800; color: #0f172a; font-family: \'Outfit\', sans-serif; vertical-align: middle;">{word}</span>'
                f'<button onclick="var u=new SpeechSynthesisUtterance(\'{clean_word_val}\'); u.lang=\'de-DE\'; speechSynthesis.speak(u); event.stopPropagation();" style="cursor: pointer; background: transparent; border: none; font-size: 1.5em; vertical-align: middle; color: #6366f1;" title="Прослушать">🔊</button>'
                f'</div>'
                f'<div style="display: flex; justify-content: center; gap: 8px;">'
                f'<span style="background: #e2e8f0; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">{pos}</span>'
                f'<span style="background: {lvl_color}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">{level}</span>'
                f'</div>'
                f'</div>'
            )
            
            # Examples list HTML
            examples_html = ""
            for ex in examples:
                de_ex = ex.get("de", "")
                ru_ex = ex.get("ru", "")
                examples_html += (
                    f'<li style="margin-bottom: 10px; padding-left: 8px; border-left: 3px solid #a855f7;">'
                    f'<div style="font-style: italic; color: #0f172a; font-weight: 600;">{de_ex}</div>'
                    f'<div style="color: #475569; font-size: 0.95em;">➔ {ru_ex}</div>'
                    f'</li>'
                )
            
            en_html = f'<div style="font-size: 1.15em; color: #475569; font-weight: 500; margin-bottom: 20px;">{en}</div>' if en else ""
            
            # Synonyms HTML
            synonyms_html = ""
            if synonyms:
                synonyms_html = f'<div style="font-size: 0.95em; color: #475569; margin-bottom: 15px; text-align: center;"><strong>Synonyme:</strong> {", ".join(synonyms)}</div>'
            
            # Antonyms HTML
            antonyms = w.get("antonyms", [])
            antonyms_html = ""
            if antonyms:
                antonyms_html = f'<div style="font-size: 0.95em; color: #e74c3c; margin-bottom: 15px; text-align: center;"><strong>Antonyme:</strong> {", ".join(antonyms)}</div>'
                
            # Verb details HTML
            verb_details_html = ""
            if pos == "Verb":
                partizip_2 = w.get("partizip_2", "")
                imperative = w.get("imperative", "")
                prepositions = w.get("prepositions", [])
                conj = w.get("conjugations", {})
                
                preps_html = f'<div style="margin-bottom: 5px;"><strong>Управление (Prepositionen):</strong> {", ".join(prepositions)}</div>' if prepositions else ""
                
                verb_details_html = (
                    f'<div style="text-align: left; max-width: 500px; margin: 15px auto 15px; background: #f1f5f9; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 0.85em;">'
                    f'<div style="margin-bottom: 3px;"><strong>Partizip II:</strong> {partizip_2}</div>'
                    f'<div style="margin-bottom: 3px;"><strong>Imperativ:</strong> {imperative}</div>'
                    f'{preps_html}'
                    f'<div style="font-weight: 700; margin-top: 8px; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.03em; font-size: 0.8em; color: #64748b;">Konjugation (Präsens):</div>'
                    f'<table style="width: 100%; border-collapse: collapse; text-align: left; border: 1px solid #cbd5e1;">'
                    f'<tr style="background: #e2e8f0;"><td style="padding: 3px 6px; border: 1px solid #cbd5e1; font-weight: 600; width: 20%;">ich</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1; width: 30%;">{conj.get("ich", "")}</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1; font-weight: 600; width: 20%;">wir</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1; width: 30%;">{conj.get("wir", "")}</td></tr>'
                    f'<tr><td style="padding: 3px 6px; border: 1px solid #cbd5e1; font-weight: 600;">du</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1;">{conj.get("du", "")}</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1; font-weight: 600;">ihr</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1;">{conj.get("ihr", "")}</td></tr>'
                    f'<tr style="background: #e2e8f0;"><td style="padding: 3px 6px; border: 1px solid #cbd5e1; font-weight: 600;">er/sie/es</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1;">{conj.get("er/sie/es", "")}</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1; font-weight: 600;">sie/Sie</td><td style="padding: 3px 6px; border: 1px solid #cbd5e1;">{conj.get("sie/Sie", "")}</td></tr>'
                    f'</table>'
                    f'</div>'
                )
            
            # Back HTML
            back_html = (
                f'<div style="font-family: \'Plus Jakarta Sans\', Arial, sans-serif; text-align: center; padding: 25px; '
                f'background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">'
                f'<div style="font-size: 0.9em; color: #6366f1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">{cat}</div>'
                f'<div style="margin-bottom: 15px; display: flex; align-items: center; justify-content: center; gap: 8px;">'
                f'<span style="font-size: 2.2em; font-weight: 800; color: #0f172a; font-family: \'Outfit\', sans-serif; vertical-align: middle;">{word}</span>'
                f'<button onclick="var u=new SpeechSynthesisUtterance(\'{clean_word_val}\'); u.lang=\'de-DE\'; speechSynthesis.speak(u); event.stopPropagation();" style="cursor: pointer; background: transparent; border: none; font-size: 1.5em; vertical-align: middle; color: #6366f1;" title="Прослушать">🔊</button>'
                f'</div>'
                f'<div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 20px;">'
                f'<span style="background: #e2e8f0; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">{pos}</span>'
                f'<span style="background: {lvl_color}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">{level}</span>'
                f'<a href="https://de.youglish.com/pronounce/{clean_word_val}/german" target="_blank" style="background: #ff0000; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;" title="Смотреть произношение в видео">🎥 YouGlish</a>'
                f'</div>'
                f'<hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 20px 0;">'
                f'<div style="font-size: 1.7em; font-weight: 700; color: #a855f7; margin-bottom: 8px;">{ru}</div>'
                f'{en_html}'
                f'{synonyms_html}'
                f'{antonyms_html}'
                f'{verb_details_html}'
                f'<div style="text-align: left; max-width: 500px; margin: 20px auto 0; background: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;">'
                f'<div style="font-weight: 700; color: #0f172a; margin-bottom: 10px; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.05em;">Beispiele:</div>'
                f'<ul style="margin: 0; padding: 0; list-style: none;">'
                f'{examples_html}'
                f'</ul>'
                f'</div>'
                f'</div>'
            )
            
            # Create slugs for tags
            def slugify(text):
                text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
                text = text.lower()
                text = re.sub(r'[^a-z0-9]+', '_', text)
                return text.strip('_')
            
            # Map categories to their respective group slugs for Anki tags
            group_mapping = {
                "Finanzgrundlagen & Geld": "finanzen",
                "Buchhaltung & Bilanz": "finanzen",
                "Banken & Kredite": "finanzen",
                "Steuern & Finanzamt": "finanzen",
                "Investition & Börse": "finanzen",
                "Bewerbung & Lebenslauf": "bewerbung",
                "Gesprächsablauf & Fragen": "bewerbung",
                "Stärken & Kompetenzen": "bewerbung",
                "Arbeitsbedingungen & Gehalt": "bewerbung",
                "Karriere & Weiterbildung": "bewerbung",
                "Behörden & Formulare": "aemter_alltag",
                "Wohnung & Anmeldung": "aemter_alltag",
                "Gesundheit & Kassen": "aemter_alltag",
                "ÖPNV & Reisen": "aemter_alltag",
                "Alltag & Dienste": "aemter_alltag"
            }
            grp_slug = group_mapping.get(cat, "projektmanagement")
            
            tag_cat = slugify(cat)
            tag_lvl = level.lower()
            tags = f"{grp_slug} {tag_cat} {tag_lvl}"
            
            writer.writerow([front_html, back_html, tags])

def generate_html(all_words, categories, html_path):
    words_json = json.dumps(all_words, ensure_ascii=False)
    categories_json = json.dumps(categories, ensure_ascii=False)
    
    html_template = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learny B1-B2 German Vocabulary</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-secondary: #161c2d;
            --bg-tertiary: #1f273d;
            --accent-primary: #6366f1; /* Indigo */
            --accent-secondary: #a855f7; /* Purple */
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: rgba(255, 255, 255, 0.08);
            --gradient-accent: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            --glass-bg: rgba(22, 28, 45, 0.7);
            --glass-border: rgba(255, 255, 255, 0.05);
            --card-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            
            --level-b1: #10b981; /* Emerald */
            --level-b2: #f59e0b; /* Amber */
        }}
        
        [data-theme="light"] {{
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f1f5f9;
            --accent-primary: #4f46e5;
            --accent-secondary: #9333ea;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border-color: rgba(0, 0, 0, 0.08);
            --gradient-accent: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
            --glass-bg: rgba(255, 255, 255, 0.7);
            --glass-border: rgba(0, 0, 0, 0.05);
            --card-shadow: 0 10px 30px -15px rgba(0, 0, 0, 0.1);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            transition: background-color 0.3s, border-color 0.3s, color 0.3s;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            padding-bottom: 50px;
            overflow-x: hidden;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
        }}

        /* Header Layout */
        header {{
            position: relative;
            padding: 80px 20px 40px;
            text-align: center;
            background: radial-gradient(circle at top, rgba(99, 102, 241, 0.15) 0%, rgba(0,0,0,0) 60%);
            border-bottom: 1px solid var(--border-color);
        }}

        header h1 {{
            font-size: 3rem;
            margin-bottom: 15px;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }}

        header p {{
            color: var(--text-secondary);
            font-size: 1.15rem;
            max-width: 700px;
            margin: 0 auto 20px;
        }}

        /* Theme Toggle & Stats Button */
        .header-actions {{
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 25px;
        }}

        .btn-action {{
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 10px 20px;
            border-radius: 50px;
            cursor: pointer;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--card-shadow);
        }}

        .btn-action:hover {{
            background: var(--bg-tertiary);
            border-color: var(--accent-primary);
        }}
        
        .btn-action.primary {{
            background: var(--gradient-accent);
            color: #ffffff;
            border: none;
        }}
        .btn-action.primary:hover {{
            opacity: 0.9;
        }}

        /* Search & Controls Container */
        .controls-container {{
            max-width: 1200px;
            margin: -30px auto 40px;
            padding: 30px;
            border-radius: 24px;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            box-shadow: var(--card-shadow);
            position: relative;
            z-index: 10;
        }}

        .search-row {{
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
        }}

        .search-box {{
            flex: 1;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 16px 20px 16px 50px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 1.05rem;
            outline: none;
        }}

        .search-box input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        }}

        .search-box i {{
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 1.2rem;
        }}

        .filter-row {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .filter-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}

        .filter-label {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-right: 10px;
            min-width: 90px;
        }}

        .filter-badge {{
            padding: 8px 16px;
            border-radius: 50px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.88rem;
            font-weight: 500;
            cursor: pointer;
            user-select: none;
        }}

        .filter-badge:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        .filter-badge.active {{
            background: var(--accent-primary);
            border-color: var(--accent-primary);
            color: #ffffff;
        }}

        .filter-badge.active.purple {{
            background: var(--accent-secondary);
            border-color: var(--accent-secondary);
        }}

        /* Group Selector Styles */
        .group-selector-row {{
            margin-bottom: 25px;
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            padding: 5px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
        }}

        .group-btn {{
            padding: 12px 24px;
            border-radius: 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--card-shadow);
            transition: all 0.2s ease;
        }}

        .group-btn:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            transform: translateY(-2px);
        }}

        .group-btn.active {{
            background: var(--gradient-accent);
            border-color: transparent;
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}

        /* Main Workspace Grid */
        main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        .view-mode-tabs {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }}

        .tab-group {{
            display: flex;
            gap: 10px;
            background: var(--bg-secondary);
            padding: 5px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}

        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .tab-btn.active {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            box-shadow: 0 4px 12px -2px rgba(0,0,0,0.2);
        }}

        .stats-summary {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        /* Cards Layout */
        .vocab-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }}

        .vocab-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 25px;
            display: flex;
            flex-direction: column;
            box-shadow: var(--card-shadow);
            position: relative;
            overflow: hidden;
        }}

        .vocab-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--gradient-accent);
            opacity: 0;
            transition: opacity 0.3s;
        }}

        .vocab-card:hover::before {{
            opacity: 1;
        }}

        .vocab-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 15px 35px -10px rgba(99, 102, 241, 0.15);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }}

        .word-badges {{
            display: flex;
            gap: 8px;
        }}

        .badge {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .badge-pos {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }}

        .badge-level {{
            color: #ffffff;
        }}

        .badge-b1 {{
            background: var(--level-b1);
        }}

        .badge-b2 {{
            background: var(--level-b2);
        }}

        .btn-favorite {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.15rem;
        }}

        .btn-favorite.active {{
            color: #f43f5e; /* Rose */
        }}

        .vocab-card h3 {{
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 4px;
            color: var(--text-primary);
        }}

        .category-tag {{
            font-size: 0.8rem;
            color: var(--accent-primary);
            font-weight: 600;
            margin-bottom: 12px;
            display: inline-block;
        }}

        .card-body {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .translations {{
            background: var(--bg-tertiary);
            padding: 12px 15px;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .translation-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.95rem;
        }}

        .translation-row span {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        .translation-row img {{
            width: 16px;
            height: 12px;
            object-fit: cover;
            border-radius: 2px;
        }}

        /* Star Rating & Status Badge Styles */
        .star-rating {{
            display: inline-flex;
            gap: 4px;
        }}
        .star-icon {{
            font-size: 1.1rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: color 0.2s, transform 0.1s;
        }}
        .star-icon:hover {{
            transform: scale(1.2);
        }}
        .star-icon.filled {{
            color: #f59e0b; /* Amber */
        }}
        [data-theme="light"] .star-icon {{
            color: #cbd5e1;
        }}
        [data-theme="light"] .star-icon.filled {{
            color: #f59e0b;
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 50px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .status-badge.memorized {{
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
        }}
        .status-badge.dont_know {{
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
        }}
        .status-badge.unseen {{
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
        }}

        /* Examples Section */
        .examples-section {{
            margin-top: 10px;
        }}

        .examples-toggle {{
            width: 100%;
            background: transparent;
            border: none;
            color: var(--accent-primary);
            font-weight: 600;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            cursor: pointer;
            border-top: 1px dashed var(--border-color);
        }}

        .examples-list {{
            display: none;
            flex-direction: column;
            gap: 12px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
            animation: slideDown 0.3s ease-out;
        }}

        .examples-list.show {{
            display: flex;
        }}

        .example-item {{
            font-size: 0.88rem;
            padding-left: 10px;
            border-left: 2px solid var(--accent-secondary);
        }}

        .example-de {{
            font-style: italic;
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 4px;
        }}

        .example-ru {{
            color: var(--text-secondary);
        }}

        /* Flashcard Mode (Overlay / View) */
        .flashcard-view {{
            display: none;
            max-width: 600px;
            margin: 40px auto;
            perspective: 1000px;
        }}

        .flashcard-container {{
            width: 100%;
            height: 440px;
            position: relative;
            transform-style: preserve-3d;
            transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }}

        .flashcard-container.flipped {{
            transform: rotateY(180deg);
        }}

        .flashcard-side {{
            position: absolute;
            width: 100%;
            height: 100%;
            backface-visibility: hidden;
            border-radius: 24px;
            padding: 55px 35px 35px 35px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--glass-border);
            background: var(--bg-secondary);
            overflow-y: auto;
        }}

        .flashcard-front {{
            background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.1) 0%, var(--bg-secondary) 90%);
        }}

        .flashcard-back {{
            background: radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.1) 0%, var(--bg-secondary) 90%);
            transform: rotateY(180deg);
        }}

        /* Flashcard Top Meta */
        .fc-card-top-meta {{
            position: absolute;
            top: 20px;
            left: 25px;
            right: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .fc-status-icon {{
            font-size: 1.35rem;
        }}
        .fc-status-icon.memorized {{
            color: #10b981;
        }}
        .fc-status-icon.dont_know {{
            color: #ef4444;
        }}
        .fc-status-icon.unseen {{
            color: var(--text-muted);
        }}
        .fc-stars {{
            display: flex;
            gap: 2px;
        }}

        .flashcard-card-label {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 15px;
            font-weight: 600;
        }}

        .flashcard-word {{
            font-size: 2.2rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 15px;
            color: var(--text-primary);
        }}

        .flashcard-translation {{
            font-size: 1.6rem;
            font-weight: 600;
            color: var(--accent-secondary);
            text-align: center;
            margin-bottom: 15px;
        }}

        .flashcard-hint {{
            font-size: 0.85rem;
            color: var(--text-muted);
            position: absolute;
            bottom: 20px;
        }}

        .flashcard-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 25px;
            gap: 20px;
        }}

        /* Flashcard Actions */
        .flashcard-actions {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 25px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }}
        .flashcard-actions.show {{
            opacity: 1;
            pointer-events: auto;
        }}
        .btn-fc-action {{
            padding: 12px 24px;
            border-radius: 14px;
            border: none;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s, background-color 0.2s;
        }}
        .btn-fc-action:active {{
            transform: scale(0.95);
        }}
        .btn-dont-know {{
            background: rgba(239, 68, 68, 0.12);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.25);
        }}
        .btn-dont-know:hover {{
            background: #ef4444;
            color: #ffffff;
        }}
        .btn-know {{
            background: rgba(16, 185, 129, 0.12);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.25);
        }}
        .btn-know:hover {{
            background: #10b981;
            color: #ffffff;
        }}

        /* Progress Bar */
        .progress-bar-container {{
            width: 100%;
            background: var(--bg-tertiary);
            height: 6px;
            border-radius: 3px;
            margin-top: 20px;
        }}
        .progress-bar-fill {{
            width: 0%;
            height: 100%;
            background: var(--gradient-accent);
            border-radius: 3px;
            transition: width 0.3s;
        }}

        .btn-nav {{
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}

        .btn-nav:hover {{
            background: var(--bg-tertiary);
            border-color: var(--accent-primary);
        }}

        .flashcard-stats {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-secondary);
        }}

        /* Animations */
        @keyframes slideDown {{
            from {{ opacity: 0; transform: translateY(-10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
            animation: fadeIn 0.5s ease;
        }}

        .empty-state i {{
            font-size: 3rem;
            margin-bottom: 20px;
            color: var(--text-muted);
        }}

        /* Responsive Layout */
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 2.2rem;
            }}
            .search-row {{
                flex-direction: column;
            }}
            .vocab-grid {{
                grid-template-columns: 1fr;
            }}
            .controls-container {{
                margin: -20px 10px 30px;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>

    <header>
        <h1>Learny German</h1>
        <p>Learny B1-B2 words for German life. Изучайте терминологию, просматривайте примеры и тренируйтесь с флеш-картами.</p>
        
        <div class="header-actions">
            <button class="btn-action" id="theme-toggle">
                <i class="fa-solid fa-moon"></i> Theme
            </button>
            <button class="btn-action" id="btn-quiz" onclick="startFlashcardMode()">
                <i class="fa-solid fa-graduation-cap"></i> Карточки для запоминания
            </button>
            <button class="btn-action primary" id="btn-daily-review" onclick="startDailyReview()">
                <i class="fa-solid fa-calendar-day"></i> Ежедневное ревью (50)
            </button>
            <button class="btn-action" id="btn-stats-dashboard" onclick="openStatsDashboard()" style="background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white;">
                <i class="fa-solid fa-chart-line"></i> Статистика
            </button>
        </div>
    </header>

    <div class="controls-container" id="controls">
        <!-- Group Selector Bar -->
        <div class="group-selector-row">
            <button class="group-btn active" data-group="Projektmanagement" onclick="selectGroup('Projektmanagement')">
                <i class="fa-solid fa-briefcase"></i> Projektmanagement
            </button>
            <button class="group-btn" data-group="Finanzen & Buchhaltung" onclick="selectGroup('Finanzen & Buchhaltung')">
                <i class="fa-solid fa-calculator"></i> Finanzen & Buchhaltung
            </button>
            <button class="group-btn" data-group="Bewerbung & Vorstellungsgespräch" onclick="selectGroup('Bewerbung & Vorstellungsgespräch')">
                <i class="fa-solid fa-id-card"></i> Jobinterview
            </button>
            <button class="group-btn" data-group="Ämter & Alltag" onclick="selectGroup('Ämter & Alltag')">
                <i class="fa-solid fa-building-columns"></i> Ämter & Alltag
            </button>
            <button class="group-btn" data-group="SAP-Consulting" onclick="selectGroup('SAP-Consulting')">
                <i class="fa-solid fa-gears"></i> SAP-Consulting
            </button>
            <button class="group-btn" data-group="Legal-Laws" onclick="selectGroup('Legal-Laws')">
                <i class="fa-solid fa-scale-balanced"></i> Legal-Laws
            </button>
        </div>

        <div class="search-row">
            <div class="search-box">
                <i class="fa-solid fa-magnifying-glass"></i>
                <input type="text" id="search-input" placeholder="Поиск слова, перевода или примера...">
            </div>
        </div>
        
        <div class="filter-row">
            <div class="filter-group">
                <div class="filter-label">Категория:</div>
                <div class="filter-badge active" data-filter="cat-all" onclick="filterCategory('all')">Все</div>
                <!-- Categories will be generated dynamically -->
                <div id="category-filters" style="display:contents;"></div>
            </div>
            
            <div class="filter-group">
                <div class="filter-label">Уровень:</div>
                <div class="filter-badge active" data-filter="level-all" onclick="filterLevel('all')">Все</div>
                <div class="filter-badge" data-filter="level-a2" onclick="filterLevel('A2')">A2</div>
                <div class="filter-badge" data-filter="level-b1" onclick="filterLevel('B1')">B1</div>
                <div class="filter-badge" data-filter="level-b2" onclick="filterLevel('B2')">B2</div>
                <div class="filter-badge" data-filter="level-c1" onclick="filterLevel('C1')">C1</div>
            </div>
            
            <div class="filter-group">
                <div class="filter-label">Звезды:</div>
                <div class="filter-badge active" data-filter="stars-all" onclick="filterStars('all')">Все</div>
                <div class="filter-badge" data-filter="stars-0" onclick="filterStars(0)">Новые (0 ★)</div>
                <div class="filter-badge" data-filter="stars-1" onclick="filterStars(1)">1 ★</div>
                <div class="filter-badge" data-filter="stars-2" onclick="filterStars(2)">2 ★</div>
                <div class="filter-badge" data-filter="stars-3" onclick="filterStars(3)">3 ★</div>
                <div class="filter-badge" data-filter="stars-4" onclick="filterStars(4)">4 ★</div>
                <div class="filter-badge" data-filter="stars-5" onclick="filterStars(5)">5 ★</div>
            </div>
            
            <div class="filter-group">
                <div class="filter-label">Другое:</div>
                <div class="filter-badge" id="filter-favorites" onclick="toggleFavoritesFilter()">★ Только избранное</div>
            </div>
        </div>
    </div>

    <main>
        <!-- Card Grid View -->
        <div id="grid-view-container">
            <div class="view-mode-tabs">
                <div class="stats-summary" id="stats-summary">
                    Показано: 0 из 0 слов
                </div>
                <div class="tab-group">
                    <button class="tab-btn active" id="tab-grid" onclick="setViewMode('grid')">
                        <i class="fa-solid fa-grip"></i> Сетка
                    </button>
                </div>
            </div>
            
            <div class="vocab-grid" id="vocab-grid">
                <!-- Cards will be dynamically inserted here -->
            </div>
        </div>

        <!-- Flashcard View -->
        <div class="flashcard-view" id="flashcard-view-container">
            <div class="view-mode-tabs">
                <div class="stats-summary" id="flashcard-category-label">
                    Режим карточек
                </div>
                <button class="tab-btn" onclick="setViewMode('grid')">
                    <i class="fa-solid fa-arrow-left"></i> Назад к списку
                </button>
            </div>
            
            <!-- Progress Bar -->
            <div class="progress-bar-container" id="fc-progress-bar-container" style="display: none;">
                <div class="progress-bar-fill" id="fc-progress-bar-fill"></div>
            </div>
            
            <div class="flashcard-container" id="flashcard" onclick="flipCard()">
                <!-- Front -->
                <div class="flashcard-side flashcard-front">
                    <div class="fc-card-top-meta">
                        <span class="fc-status-icon" id="fc-front-status-icon"></span>
                        <span class="fc-stars" id="fc-front-stars"></span>
                    </div>
                    <div class="flashcard-card-label" id="fc-front-label">DEUTSCH</div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; margin-bottom: 15px;">
                        <div class="flashcard-word" id="fc-word" style="margin-bottom: 0;">Wort</div>
                        <button class="btn-tts-speak" id="fc-front-speak" onclick="speakCurrentWord(event)" title="Прослушать произношение" style="background: transparent; border: none; color: var(--accent-primary); cursor: pointer; font-size: 1.8rem; display: inline-flex; align-items: center; justify-content: center; padding: 6px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform='scale(1)'">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                    </div>
                    <div class="badge badge-level" id="fc-level-badge">B1</div>
                    <div class="flashcard-hint"><i class="fa-solid fa-rotate"></i> Кликните, чтобы перевернуть</div>
                </div>
                <!-- Back -->
                <div class="flashcard-side flashcard-back">
                    <div class="fc-card-top-meta">
                        <span class="fc-status-icon" id="fc-back-status-icon"></span>
                        <span class="fc-stars" id="fc-back-stars"></span>
                    </div>
                    <div class="flashcard-card-label">ПЕРЕВОД</div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
                        <span id="fc-back-word" style="font-size: 1.4rem; font-weight: 700; color: var(--text-primary);">Wort</span>
                        <button class="btn-tts-speak" onclick="speakCurrentWord(event)" title="Прослушать произношение" style="background: transparent; border: none; color: var(--accent-primary); cursor: pointer; font-size: 1.15rem; display: inline-flex; align-items: center; justify-content: center; padding: 4px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform='scale(1)'">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                        <a id="fc-back-youglish" href="#" target="_blank" onclick="event.stopPropagation()" style="background: #ff0000; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;" title="Смотреть произношение в видео">
                            <i class="fa-solid fa-video"></i> YouGlish
                        </a>
                    </div>
                    <div class="flashcard-translation" id="fc-translation">Перевод</div>
                    <div style="font-size:0.95rem; color:var(--text-secondary); text-align:center; width:95%; margin-bottom: 20px; display: flex; flex-direction: column; align-items: center;" id="fc-examples-box">
                        <!-- Example will be inserted here -->
                    </div>
                    <div class="flashcard-hint"><i class="fa-solid fa-rotate"></i> Кликните, чтобы вернуть</div>
                </div>
            </div>
            
            <!-- Rating Action Buttons (Memorized / Don't Know) -->
            <div class="flashcard-actions" id="fc-actions">
                <button class="btn-fc-action btn-dont-know" onclick="rateFlashcard('dont_know')">
                    <i class="fa-solid fa-circle-xmark"></i> Не знаю
                </button>
                <button class="btn-fc-action btn-know" onclick="rateFlashcard('memorized')">
                    <i class="fa-solid fa-circle-check"></i> Запомнил
                </button>
            </div>
            
            <div class="flashcard-nav">
                <button class="btn-nav" id="btn-fc-prev" onclick="prevCard()"><i class="fa-solid fa-chevron-left"></i> Назад</button>
                <div class="flashcard-stats" id="fc-progress">1 / 300</div>
                <button class="btn-nav" id="btn-fc-next" onclick="nextCard()">Вперед <i class="fa-solid fa-chevron-right"></i></button>
            </div>
        </div>
        
        <!-- Completion Screen -->
        <div id="fc-completion-screen" style="display: none; flex-direction: column; align-items: center; justify-content: center; gap: 20px; padding: 40px 20px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 24px; box-shadow: var(--card-shadow); max-width: 600px; margin: 40px auto; animation: fadeIn 0.5s ease;">
            <div style="font-size: 4rem; color: #f59e0b;"><i class="fa-solid fa-trophy"></i></div>
            <h2 style="font-size: 2rem; background: var(--gradient-accent); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Ревью завершено!</h2>
            <p style="color: var(--text-secondary); font-size: 1.1rem; max-width: 400px; text-align: center;">Вы успешно повторили 50 случайных карточек сегодня. Отличная работа!</p>
            <div style="display: flex; gap: 20px; margin: 10px 0;">
                <div style="background: rgba(16, 185, 129, 0.1); padding: 15px 25px; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2); text-align: center; min-width: 120px;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: #10b981;" id="completion-know-count">0</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 5px;">Запомнил</div>
                </div>
                <div style="background: rgba(239, 68, 68, 0.1); padding: 15px 25px; border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.2); text-align: center; min-width: 120px;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: #ef4444;" id="completion-dontknow-count">0</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 5px;">Не знаю</div>
                </div>
            </div>
            <button class="btn-action primary" style="margin-top: 15px; padding: 12px 30px;" onclick="setViewMode('grid')">
                <i class="fa-solid fa-arrow-left"></i> Вернуться к списку
            </button>
        </div>

        <!-- Stats Dashboard -->
        <div id="stats-dashboard" style="display: none; max-width: 700px; margin: 30px auto; padding: 25px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 20px; box-shadow: var(--card-shadow);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="font-size: 1.5rem; background: var(--gradient-accent); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;"><i class="fa-solid fa-chart-line"></i> Статистика обучения</h2>
                <button class="btn-action" style="padding: 8px 18px; font-size: 0.85rem;" onclick="closeStatsDashboard()"><i class="fa-solid fa-xmark"></i> Закрыть</button>
            </div>
            <div id="stats-summary-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px;"></div>
            <div id="stats-chart-area" style="width: 100%; overflow-x: auto;"></div>
        </div>
    </main>

    <script>
        const words = {words_json};
        const categories = {categories_json};
        
        // Map category names to their respective vocab groups
        const groupMapping = {{
            "Projektinitiierung, Planung & Ziele": "Projektmanagement",
            "Rollen, Team & Zuständigkeiten": "Projektmanagement",
            "Termine, Fristen & Meilensteine": "Projektmanagement",
            "Ressourcen, Budget & Verträge": "Projektmanagement",
            "Risikomanagement & Qualitätssicherung": "Projektmanagement",
            "Projektsteuerung, Meetings & Berichte": "Projektmanagement",
            "Projektabschluss & Lessons Learned": "Projektmanagement",
            "Finanzgrundlagen & Geld": "Finanzen & Buchhaltung",
            "Buchhaltung & Bilanz": "Finanzen & Buchhaltung",
            "Banken & Kredite": "Finanzen & Buchhaltung",
            "Steuern & Finanzamt": "Finanzen & Buchhaltung",
            "Investition & Börse": "Finanzen & Buchhaltung",
            "Bewerbung & Lebenslauf": "Bewerbung & Vorstellungsgespräch",
            "Gesprächsablauf & Fragen": "Bewerbung & Vorstellungsgespräch",
            "Stärken & Kompetenzen": "Bewerbung & Vorstellungsgespräch",
            "Arbeitsbedingungen & Gehalt": "Bewerbung & Vorstellungsgespräch",
            "Karriere & Weiterbildung": "Bewerbung & Vorstellungsgespräch",
            "Behörden & Formulare": "Ämter & Alltag",
            "Wohnung & Anmeldung": "Ämter & Alltag",
            "Gesundheit & Kassen": "Ämter & Alltag",
            "ÖPNV & Reisen": "Ämter & Alltag",
            "Alltag & Dienste": "Ämter & Alltag",
            "SAP FI/CO (Finanzwesen & Controlling)": "SAP-Consulting",
            "Materialwirtschaft & Bestandsbewertung (MM/ML)": "SAP-Consulting",
            "Vertrieb & Kundenmanagement (SD)": "SAP-Consulting",
            "S4 HANA & Fiori Benutzeroberfläche": "SAP-Consulting",
            "SAP-Einführung & Customizing": "SAP-Consulting",
            "Verfassungsrecht & Staatsorganisation": "Legal-Laws",
            "Zivilrecht & Vertragsrecht": "Legal-Laws",
            "Strafrecht & Ordnungswidrigkeiten": "Legal-Laws",
            "Verwaltungsrecht & Behördenverfahren": "Legal-Laws",
            "Arbeitsrecht & Sozialrecht": "Legal-Laws"
        }};
        
        let activeGroup = localStorage.getItem('vocab_active_group') || 'Projektmanagement';
        
        let currentFilter = {{
            category: 'all',
            level: 'all',
            stars: 'all',
            favoritesOnly: false,
            search: ''
        }};
        
        let favorites = JSON.parse(localStorage.getItem('vocab_favorites') || '[]');
        
        // Vocabulary rating stats: {{ word: {{ stars: N, status: 'memorized'|'dont_know'|'unseen' }} }}
        let vocabStats = JSON.parse(localStorage.getItem('vocab_stats') || '{{}}');
        
        let currentFlashcardIndex = 0;
        let filteredWordsForFlashcards = [];
        let isDailyReview = false;
        let sessionStats = {{ know: 0, dontKnow: 0 }};

        function speakWord(event, word) {{
            if (event) event.stopPropagation();
            const cleanWord = word.split(',')[0].replace(/^(der|die|das)\\s+/i, '').trim();
            const utterance = new SpeechSynthesisUtterance(cleanWord);
            utterance.lang = 'de-DE';
            if (typeof speechSynthesis !== 'undefined') {{
                const voices = speechSynthesis.getVoices();
                const deVoice = voices.find(v => v.lang.startsWith('de'));
                if (deVoice) utterance.voice = deVoice;
                speechSynthesis.speak(utterance);
            }}
        }}
        
        function speakCurrentWord(event) {{
            if (event) event.stopPropagation();
            const w = filteredWordsForFlashcards[currentFlashcardIndex];
            if (w) {{
                speakWord(null, w.word);
            }}
        }}

        // Initialize App
        document.addEventListener('DOMContentLoaded', () => {{
            activeGroup = localStorage.getItem('vocab_active_group') || 'Projektmanagement';
            
            // Set active class on restored group button
            document.querySelectorAll('.group-btn').forEach(btn => {{
                if (btn.getAttribute('data-group') === activeGroup) {{
                    btn.classList.add('active');
                }} else {{
                    btn.classList.remove('active');
                }}
            }});
            
            setupCategoryFilters();
            renderCards();
            setupTheme();
            updateStats();
        }});

        // Setup Dark/Light Theme
        function setupTheme() {{
            const themeToggle = document.getElementById('theme-toggle');
            const storedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', storedTheme);
            updateThemeButton(storedTheme);
            
            themeToggle.addEventListener('click', () => {{
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateThemeButton(newTheme);
            }});
        }}

        function updateThemeButton(theme) {{
            const themeToggle = document.getElementById('theme-toggle');
            if (theme === 'dark') {{
                themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i> Light';
            }} else {{
                themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i> Dark';
            }}
        }}

        // Helper stats functions
        function getWordStats(word) {{
            if (!vocabStats[word]) {{
                vocabStats[word] = {{
                    stars: 0,
                    status: 'unseen'
                }};
            }}
            return vocabStats[word];
        }}

        function saveWordStats() {{
            localStorage.setItem('vocab_stats', JSON.stringify(vocabStats));
        }}

        function setWordStars(word, stars) {{
            let stats = getWordStats(word);
            stats.stars = Math.min(5, Math.max(0, stars));
            saveWordStats();
        }}

        function setWordStatus(word, status) {{
            let stats = getWordStats(word);
            stats.status = status;
            saveWordStats();
        }}

        function getStatusIconHtml(status) {{
            if (status === 'memorized') {{
                return '<i class="fa-solid fa-circle-check" style="color: #10b981;"></i>';
            }} else if (status === 'dont_know') {{
                return '<i class="fa-solid fa-circle-xmark" style="color: #ef4444;"></i>';
            }} else {{
                return '<i class="fa-regular fa-circle-question" style="color: var(--text-muted);"></i>';
            }}
        }}

        function getStatusText(status) {{
            if (status === 'memorized') {{
                return 'Запомнил';
            }} else if (status === 'dont_know') {{
                return 'Не знаю';
            }} else {{
                return 'Новое';
            }}
        }}

        function renderStarsHtml(word) {{
            const stats = getWordStats(word);
            let html = '';
            for (let i = 1; i <= 5; i++) {{
                const isFilled = i <= stats.stars;
                html += `<i class="fa-star star-icon ${{isFilled ? 'fa-solid filled' : 'fa-regular'}}" onclick="handleStarClick(event, '${{word.replace(/'/g, "\\'")}}', ${{i}})"></i>`;
            }}
            return html;
        }}
        
        function renderStarsDisplayHtml(stars) {{
            let html = '';
            for (let i = 1; i <= 5; i++) {{
                const isFilled = i <= stars;
                html += `<i class="fa-star ${{isFilled ? 'fa-solid filled' : 'fa-regular'}} star-icon" style="font-size: 0.9rem; cursor: default; margin-left: 2px;"></i>`;
            }}
            return html;
        }}

        function handleStarClick(event, word, rating) {{
            event.stopPropagation();
            const stats = getWordStats(word);
            let newRating = rating;
            
            // Toggle rating if clicking same rating when it's 1 star
            if (stats.stars === rating && rating === 1) {{
                newRating = 0;
            }}
            
            setWordStars(word, newRating);
            if (newRating > 0) {{
                setWordStatus(word, 'memorized');
            }} else {{
                setWordStatus(word, 'unseen');
            }}
            
            // Re-render card stats locally
            const cardEl = event.target.closest('.vocab-card');
            if (cardEl) {{
                const starContainer = cardEl.querySelector('.star-rating');
                if (starContainer) starContainer.innerHTML = renderStarsHtml(word);
                
                const badgeContainer = cardEl.querySelector('.status-badge');
                if (badgeContainer) {{
                    const updatedStats = getWordStats(word);
                    badgeContainer.className = `status-badge ${{updatedStats.status}}`;
                    badgeContainer.innerHTML = `${{getStatusIconHtml(updatedStats.status)}} ${{getStatusText(updatedStats.status)}}`;
                }}
            }}
        }}

        // Category Filters
        function setupCategoryFilters() {{
            const container = document.getElementById('category-filters');
            container.innerHTML = ''; // Clear existing filters
            
            categories.forEach((cat, idx) => {{
                const grp = groupMapping[cat] || 'Projektmanagement';
                if (grp === activeGroup) {{
                    const badge = document.createElement('div');
                    badge.className = 'filter-badge';
                    badge.setAttribute('data-filter', `cat-${{idx}}`);
                    badge.textContent = cat;
                    badge.onclick = () => filterCategory(cat, `cat-${{idx}}`);
                    container.appendChild(badge);
                }}
            }});
            
            // Reset active category filter UI to 'All'
            document.querySelectorAll('[data-filter^="cat-"]').forEach(btn => btn.classList.remove('active'));
            const allBtn = document.querySelector('[data-filter="cat-all"]');
            if (allBtn) allBtn.classList.add('active');
        }}

        // Group Selector Action
        function selectGroup(newGroup) {{
            activeGroup = newGroup;
            localStorage.setItem('vocab_active_group', activeGroup);
            
            // Update active state on group buttons
            document.querySelectorAll('.group-btn').forEach(btn => {{
                if (btn.getAttribute('data-group') === activeGroup) {{
                    btn.classList.add('active');
                }} else {{
                    btn.classList.remove('active');
                }}
            }});
            
            // Reset category and stars filters
            currentFilter.category = 'all';
            currentFilter.stars = 'all';
            
            // Reset stars filter UI to 'All'
            document.querySelectorAll('[data-filter^="stars-"]').forEach(btn => btn.classList.remove('active'));
            const allStarsBtn = document.querySelector('[data-filter="stars-all"]');
            if (allStarsBtn) allStarsBtn.classList.add('active');
            
            // Re-setup category filters and render
            setupCategoryFilters();
            renderCards();
        }}

        // Filter Logic
        function filterCategory(cat, filterId = 'cat-all') {{
            currentFilter.category = cat;
            document.querySelectorAll('[data-filter^="cat-"]').forEach(btn => btn.classList.remove('active'));
            const targetBtn = document.querySelector(`[data-filter="${{filterId}}"]`);
            if (targetBtn) targetBtn.classList.add('active');
            renderCards();
        }}

        // Level Filter
        function filterLevel(level) {{
            currentFilter.level = level;
            document.querySelectorAll('[data-filter^="level-"]').forEach(btn => btn.classList.remove('active'));
            const filterId = level === 'all' ? 'level-all' : `level-${{level.toLowerCase()}}`;
            document.querySelector(`[data-filter="${{filterId}}"]`).classList.add('active');
            renderCards();
        }}

        // Stars Filter
        function filterStars(starsVal) {{
            currentFilter.stars = starsVal;
            document.querySelectorAll('[data-filter^="stars-"]').forEach(btn => btn.classList.remove('active'));
            const filterId = starsVal === 'all' ? 'stars-all' : `stars-${{starsVal}}`;
            const targetBtn = document.querySelector(`[data-filter="${{filterId}}"]`);
            if (targetBtn) targetBtn.classList.add('active');
            renderCards();
        }}

        // Favorites Filter
        function toggleFavoritesFilter() {{
            currentFilter.favoritesOnly = !currentFilter.favoritesOnly;
            const favBtn = document.getElementById('filter-favorites');
            if (currentFilter.favoritesOnly) {{
                favBtn.classList.add('active', 'purple');
            }} else {{
                favBtn.classList.remove('active', 'purple');
            }}
            renderCards();
        }}

        // Search event listener
        document.getElementById('search-input').addEventListener('input', (e) => {{
            currentFilter.search = e.target.value.toLowerCase().trim();
            renderCards();
        }});

        // Render Vocabulary Cards
        function renderCards() {{
            const grid = document.getElementById('vocab-grid');
            grid.innerHTML = '';
            
            const filtered = getFilteredWords();
            
            if (filtered.length === 0) {{
                grid.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1;">
                        <i class="fa-solid fa-folder-open"></i>
                        <p>Ничего не найдено по выбранным фильтрам</p>
                    </div>
                `;
                const total = getGroupTotal();
                document.getElementById('stats-summary').textContent = `Показано: 0 из ${{total}} слов`;
                return;
            }}
            
            filtered.forEach(w => {{
                const isFav = favorites.includes(w.word);
                const stats = getWordStats(w.word);
                const card = document.createElement('div');
                card.className = 'vocab-card';
                
                // Synonyms rendering
                let synonymsHtml = '';
                if (w.synonyms && w.synonyms.length > 0) {{
                    synonymsHtml = `
                        <div class="synonyms-container" style="font-size:0.85rem; color:var(--text-secondary); margin-bottom: 5px;">
                            <span style="font-weight:600; color:var(--accent-secondary);">Синонимы:</span> ${{w.synonyms.join(', ')}}
                        </div>
                    `;
                }}
                // Antonyms rendering
                let antonymsHtml = '';
                if (w.antonyms && w.antonyms.length > 0) {{
                    antonymsHtml = `
                        <div class="antonyms-container" style="font-size:0.85rem; color:var(--text-secondary); margin-bottom: 5px;">
                            <span style="font-weight:600; color:#ef4444;">Антонимы:</span> ${{w.antonyms.join(', ')}}
                        </div>
                    `;
                }}
                
                // Verb details rendering
                let verbDetailsHtml = '';
                if (w.part_of_speech === 'Verb' && w.conjugations) {{
                    verbDetailsHtml = `
                        <div class="verb-details-section" style="margin-top: 5px;">
                            <button class="verb-details-toggle" onclick="toggleVerbDetails(this)" style="width: 100%; background: transparent; border: none; color: var(--accent-secondary); font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-top: 1px dashed var(--border-color); cursor: pointer;">
                                <span>Формы глагола (Partizip II, Konjugation)</span>
                                <i class="fa-solid fa-chevron-down"></i>
                            </button>
                            <div class="verb-details-list" style="display: none; flex-direction: column; gap: 8px; margin-top: 10px; padding: 12px; background: var(--bg-tertiary); border-radius: 12px; border: 1px solid var(--border-color); font-size: 0.85rem;">
                                <div><strong>Partizip II:</strong> ${{w.partizip_2}}</div>
                                <div><strong>Imperativ:</strong> ${{w.imperative}}</div>
                                ${{w.prepositions && w.prepositions.length > 0 ? '<div><strong>Управление (Prepositionen):</strong> ' + w.prepositions.join(', ') + '</div>' : ''}}
                                <div style="font-weight: 600; color: var(--text-muted); margin: 5px 0 3px 0; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.03em;">Спряжение (Präsens):</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                                    <div><span style="color:var(--text-muted)">ich:</span> ${{w.conjugations.ich}}</div>
                                    <div><span style="color:var(--text-muted)">wir:</span> ${{w.conjugations.wir}}</div>
                                    <div><span style="color:var(--text-muted)">du:</span> ${{w.conjugations.du}}</div>
                                    <div><span style="color:var(--text-muted)">ihr:</span> ${{w.conjugations.ihr}}</div>
                                    <div><span style="color:var(--text-muted)">er/sie/es:</span> ${{w.conjugations['er/sie/es']}}</div>
                                    <div><span style="color:var(--text-muted)">sie/Sie:</span> ${{w.conjugations['sie/Sie']}}</div>
                                </div>
                            </div>
                        </div>
                    `;
                }}
                
                // Examples rendering (First example shown by default, others collapsible)
                const firstExampleHtml = w.examples && w.examples.length > 0 ? `
                    <div class="example-item">
                        <div class="example-de">${{w.examples[0].de}}</div>
                        <div class="example-ru">${{w.examples[0].ru}}</div>
                    </div>
                ` : '';

                let remainingExamplesHtml = '';
                if (w.examples && w.examples.length > 1) {{
                    const rest = w.examples.slice(1).map(ex => `
                        <div class="example-item">
                            <div class="example-de">${{ex.de}}</div>
                            <div class="example-ru">${{ex.ru}}</div>
                        </div>
                    `).join('');
                    remainingExamplesHtml = `
                        <div class="remaining-examples" style="display: none; flex-direction: column; gap: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--border-color);">
                            ${{rest}}
                        </div>
                        <button class="btn-show-more-examples" onclick="toggleMoreExamples(this)" style="background: transparent; border: none; color: var(--accent-primary); font-size: 0.8rem; font-weight: 600; cursor: pointer; text-align: left; margin-top: 8px; display: inline-flex; align-items: center; gap: 4px; padding: 4px 0;">
                            <span>Показать еще примеры (${{w.examples.length - 1}})</span>
                            <i class="fa-solid fa-chevron-down"></i>
                        </button>
                    `;
                }}
                
                card.innerHTML = `
                    <div class="card-header">
                        <div class="word-badges" style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <span class="badge badge-pos">${{w.part_of_speech}}</span>
                            <span class="badge badge-level badge-${{w.level.toLowerCase()}}">${{w.level}}</span>
                            <a class="badge" href="https://de.youglish.com/pronounce/${{encodeURIComponent(w.word.split(',')[0].replace(/^(der|die|das)\\s+/i, '').trim())}}/german" target="_blank" onclick="event.stopPropagation()" style="background: #ff0000; color: white; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;" title="Смотреть произношение в видео">
                                <i class="fa-solid fa-video"></i> YouGlish
                            </a>
                        </div>
                        <button class="btn-favorite ${{isFav ? 'active' : ''}}" onclick="toggleFavorite(event, '${{w.word.replace(/'/g, "\\'")}}')">
                            <i class="${{isFav ? 'fa-solid' : 'fa-regular'}} fa-star"></i>
                        </button>
                    </div>
                    <h3 style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span>${{w.word}}</span>
                        <button class="btn-tts-speak" onclick="speakWord(event, '${{w.word.replace(/'/g, "\\'")}}')" title="Прослушать произношение" style="background: transparent; border: none; color: var(--accent-primary); cursor: pointer; font-size: 1.15rem; display: inline-flex; align-items: center; justify-content: center; padding: 4px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform='scale(1)'">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                    </h3>
                    
                    <div class="card-meta-row" style="display: flex; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                        <div class="star-rating" data-word="${{w.word}}">
                            ${{renderStarsHtml(w.word)}}
                        </div>
                        <span class="status-badge ${{stats.status}}" id="status-badge-${{w.word}}">
                            ${{getStatusIconHtml(stats.status)}} ${{getStatusText(stats.status)}}
                        </span>
                    </div>

                    ${{synonymsHtml}}
                    ${{antonymsHtml}}
                    
                    <div class="category-tag">${{w.category_name}}</div>
                    <div class="card-body">
                        <div class="translations">
                            <div class="translation-row">
                                <span style="font-size:0.8rem; color:var(--text-muted); width:30px;">RU</span>
                                <span>${{w.translation_ru}}</span>
                            </div>
                            ${{w.translation_en ? `
                            <div class="translation-row">
                                <span style="font-size:0.8rem; color:var(--text-muted); width:30px;">EN</span>
                                <span style="font-weight:400; color:var(--text-secondary);">${{w.translation_en}}</span>
                            </div>` : ''}}
                        </div>
                        
                        ${{verbDetailsHtml}}
                        
                        <div class="examples-section">
                            <div class="examples-list show" style="border-top: none; margin-top: 0; padding-top: 0;">
                                ${{firstExampleHtml}}
                                ${{remainingExamplesHtml}}
                            </div>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            }});
            
            const total = getGroupTotal();
            document.getElementById('stats-summary').textContent = `Показано: ${{filtered.length}} из ${{total}} слов`;
        }}

        function toggleVerbDetails(btn) {{
            const list = btn.nextElementSibling;
            const icon = btn.querySelector('i');
            list.style.display = list.style.display === 'none' ? 'flex' : 'none';
            icon.style.transform = list.style.display === 'flex' ? 'rotate(180deg)' : 'rotate(0deg)';
        }}

        function toggleMoreExamples(btn) {{
            const remainingDiv = btn.previousElementSibling;
            const icon = btn.querySelector('i');
            const textSpan = btn.querySelector('span');
            const totalCount = remainingDiv.children.length;
            
            if (remainingDiv.style.display === 'none') {{
                remainingDiv.style.display = 'flex';
                icon.className = 'fa-solid fa-chevron-up';
                textSpan.textContent = 'Скрыть примеры';
            }} else {{
                remainingDiv.style.display = 'none';
                icon.className = 'fa-solid fa-chevron-down';
                textSpan.textContent = `Показать еще примеры (${{totalCount}})`;
            }}
        }}

        function toggleFcMoreExamples(event) {{
            event.stopPropagation(); // prevent card flip
            const btn = event.currentTarget;
            const moreDiv = document.getElementById('fc-more-examples');
            const icon = btn.querySelector('i');
            const textSpan = btn.querySelector('span');
            const totalCount = moreDiv.children.length;
            
            if (moreDiv.style.display === 'none') {{
                moreDiv.style.display = 'flex';
                icon.className = 'fa-solid fa-chevron-up';
                textSpan.textContent = 'Скрыть примеры';
            }} else {{
                moreDiv.style.display = 'none';
                icon.className = 'fa-solid fa-chevron-down';
                textSpan.textContent = `Показать еще примеры (${{totalCount}})`;
            }}
        }}

        function getFilteredWords() {{
            return words.filter(w => {{
                // Group Filter
                const grp = groupMapping[w.category_name] || 'Projektmanagement';
                if (grp !== activeGroup) {{
                    return false;
                }}
                // Category Filter
                if (currentFilter.category !== 'all' && w.category_name !== currentFilter.category) {{
                    return false;
                }}
                // Level Filter
                if (currentFilter.level !== 'all' && w.level !== currentFilter.level) {{
                    return false;
                }}
                // Stars Filter
                if (currentFilter.stars !== 'all') {{
                    const stats = getWordStats(w.word);
                    if (stats.stars !== currentFilter.stars) {{
                        return false;
                    }}
                }}
                // Favorites Filter
                if (currentFilter.favoritesOnly && !favorites.includes(w.word)) {{
                    return false;
                }}
                // Search Filter
                if (currentFilter.search) {{
                    const search = currentFilter.search;
                    const matchesWord = w.word.toLowerCase().includes(search);
                    const matchesRu = w.translation_ru.toLowerCase().includes(search);
                    const matchesEn = w.translation_en && w.translation_en.toLowerCase().includes(search);
                    const matchesExamples = w.examples.some(ex => 
                        ex.de.toLowerCase().includes(search) || ex.ru.toLowerCase().includes(search)
                    );
                    return matchesWord || matchesRu || matchesEn || matchesExamples;
                }}
                return true;
            }});
        }}

        function getGroupTotal() {{
            return words.filter(w => (groupMapping[w.category_name] || 'Projektmanagement') === activeGroup).length;
        }}

        function updateStats() {{
            const count = getFilteredWords().length;
            const total = getGroupTotal();
            document.getElementById('stats-summary').textContent = `Показано: ${{count}} из ${{total}} слов`;
        }}

        // Favorites Logic
        function toggleFavorite(event, word) {{
            event.stopPropagation();
            const idx = favorites.indexOf(word);
            if (idx > -1) {{
                favorites.splice(idx, 1);
            }} else {{
                favorites.push(word);
            }}
            localStorage.setItem('vocab_favorites', JSON.stringify(favorites));
            
            // Re-render favorite button locally
            const btn = event.currentTarget;
            const icon = btn.querySelector('i');
            if (favorites.includes(word)) {{
                btn.classList.add('active');
                icon.className = 'fa-solid fa-star';
            }} else {{
                btn.classList.remove('active');
                icon.className = 'fa-regular fa-star';
            }}
            
            if (currentFilter.favoritesOnly) {{
                renderCards();
            }}
        }}

        // View Mode Switcher
        function setViewMode(mode) {{
            const gridView = document.getElementById('grid-view-container');
            const flashcardView = document.getElementById('flashcard-view-container');
            const controls = document.getElementById('controls');
            const completionScreen = document.getElementById('fc-completion-screen');
            const flashcard = document.getElementById('flashcard');
            const fcActions = document.getElementById('fc-actions');
            const fcProgressBar = document.getElementById('fc-progress-bar-container');
            const fcNav = document.querySelector('.flashcard-nav');
            
            if (mode === 'grid') {{
                gridView.style.display = 'block';
                flashcardView.style.display = 'none';
                controls.style.display = 'block';
                completionScreen.style.display = 'none';
                isDailyReview = false;
                renderCards();
                updateStats();
            }} else if (mode === 'flashcard') {{
                gridView.style.display = 'none';
                flashcardView.style.display = 'block';
                controls.style.display = 'none';
                completionScreen.style.display = 'none';
                flashcard.style.display = 'block';
                fcActions.style.display = 'flex';
                fcNav.style.display = 'flex';
                if (isDailyReview) {{
                    fcProgressBar.style.display = 'block';
                    document.getElementById('btn-fc-prev').style.display = 'none'; // No manual nav in review
                    document.getElementById('btn-fc-next').style.display = 'none';
                }} else {{
                    fcProgressBar.style.display = 'none';
                    document.getElementById('btn-fc-prev').style.display = 'inline-flex';
                    document.getElementById('btn-fc-next').style.display = 'inline-flex';
                }}
            }}
        }}

        // Flashcards Logic
        function startFlashcardMode() {{
            filteredWordsForFlashcards = getFilteredWords();
            if (filteredWordsForFlashcards.length === 0) {{
                alert('Нет слов для отображения! Измените фильтры в списке.');
                return;
            }}
            currentFlashcardIndex = 0;
            isDailyReview = false;
            setViewMode('flashcard');
            showFlashcard();
        }}

        // Daily Review Mode
        function startDailyReview() {{
            const activeGroupWords = words.filter(w => (groupMapping[w.category_name] || 'Projektmanagement') === activeGroup);
            if (activeGroupWords.length === 0) {{
                alert('Словарь пуст!');
                return;
            }}
            
            // Select 50 random words from the active group
            let shuffled = shuffleArray([...activeGroupWords]);
            filteredWordsForFlashcards = shuffled.slice(0, 50);
            
            currentFlashcardIndex = 0;
            isDailyReview = true;
            sessionStats.know = 0;
            sessionStats.dontKnow = 0;
            
            setViewMode('flashcard');
            showFlashcard();
        }}

        function shuffleArray(array) {{
            for (let i = array.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }}
            return array;
        }}

        function showFlashcard() {{
            const card = document.getElementById('flashcard');
            card.classList.remove('flipped');
            
            const fcActions = document.getElementById('fc-actions');
            fcActions.classList.remove('show'); // Hide until card is flipped
            
            const w = filteredWordsForFlashcards[currentFlashcardIndex];
            if (!w) return;
            
            document.getElementById('fc-word').textContent = w.word;
            document.getElementById('fc-translation').textContent = w.translation_ru;
            
            // Synonyms rendering
            let synonymsHtml = '';
            if (w.synonyms && w.synonyms.length > 0) {{
                synonymsHtml = `
                    <div style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 15px; text-align: center;">
                        <span style="font-weight: 600; color: var(--accent-secondary);">Синонимы:</span> ${{w.synonyms.join(', ')}}
                    </div>
                `;
            }}
            // Antonyms rendering
            let antonymsHtml = '';
            if (w.antonyms && w.antonyms.length > 0) {{
                antonymsHtml = `
                    <div style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 10px; text-align: center;">
                        <span style="font-weight: 600; color: #ef4444;">Антонимы:</span> ${{w.antonyms.join(', ')}}
                    </div>
                `;
            }}
            
            // Verb details rendering
            let verbDetailsHtml = '';
            if (w.part_of_speech === 'Verb' && w.conjugations) {{
                verbDetailsHtml = `
                    <div style="text-align: left; background: var(--bg-tertiary); padding: 12px; border-radius: 12px; border: 1px solid var(--border-color); font-size: 0.8rem; width: 100%; margin-bottom: 15px; max-width: 90%;">
                        <div style="margin-bottom: 3px;"><strong>Partizip II:</strong> ${{w.partizip_2}}</div>
                        <div style="margin-bottom: 5px;"><strong>Imperativ:</strong> ${{w.imperative}}</div>
                        ${{w.prepositions && w.prepositions.length > 0 ? '<div><strong>Управление (Prepositionen):</strong> ' + w.prepositions.join(', ') + '</div>' : ''}}
                        <div style="font-weight: 600; color: var(--text-muted); text-transform: uppercase; font-size: 0.7rem; margin-bottom: 3px;">Спряжение (Präsens):</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                            <div><span style="color:var(--text-muted)">ich:</span> ${{w.conjugations.ich}}</div>
                            <div><span style="color:var(--text-muted)">wir:</span> ${{w.conjugations.wir}}</div>
                            <div><span style="color:var(--text-muted)">du:</span> ${{w.conjugations.du}}</div>
                            <div><span style="color:var(--text-muted)">ihr:</span> ${{w.conjugations.ihr}}</div>
                            <div><span style="color:var(--text-muted)">er/sie/es:</span> ${{w.conjugations['er/sie/es']}}</div>
                            <div><span style="color:var(--text-muted)">sie/Sie:</span> ${{w.conjugations['sie/Sie']}}</div>
                        </div>
                    </div>
                `;
            }}
            
            // Examples rendering (First example shown by default, others collapsible)
            const firstExample = w.examples[0] || {{de: '', ru: ''}};
            let examplesHtml = `
                <div style="text-align: left; width: 100%; max-width: 90%; font-size: 0.85rem; border-top: 1px solid var(--border-color); padding-top: 12px;">
                    <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">Примеры использования:</div>
                    <div class="fc-example-item" style="border-left: 2px solid var(--accent-secondary); padding-left: 8px; margin-bottom: 8px;">
                        <div style="font-style: italic; color: var(--text-primary); font-weight: 500;">"${{firstExample.de}}"</div>
                        <div style="color: var(--text-muted); font-size: 0.8rem;">${{firstExample.ru}}</div>
                    </div>
            `;
            
            if (w.examples.length > 1) {{
                const restExamples = w.examples.slice(1).map(ex => `
                    <div class="fc-example-item" style="border-left: 2px solid var(--accent-secondary); padding-left: 8px; margin-bottom: 8px;">
                        <div style="font-style: italic; color: var(--text-primary); font-weight: 500;">"${{ex.de}}"</div>
                        <div style="color: var(--text-muted); font-size: 0.8rem;">${{ex.ru}}</div>
                    </div>
                `).join('');
                
                examplesHtml += `
                    <div id="fc-more-examples" style="display: none; flex-direction: column; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border-color);">
                        ${{restExamples}}
                    </div>
                    <button id="btn-fc-show-more" onclick="toggleFcMoreExamples(event)" style="background: transparent; border: none; color: var(--accent-primary); font-size: 0.78rem; font-weight: 600; cursor: pointer; padding: 4px 0; display: inline-flex; align-items: center; gap: 4px;">
                        <span>Показать еще примеры (${{w.examples.length - 1}})</span>
                        <i class="fa-solid fa-chevron-down"></i>
                    </button>
                `;
            }}
            examplesHtml += `</div>`;
            
            // Set translation and inner box HTML
            document.getElementById('fc-translation').textContent = w.translation_ru;
            
            // Set word on the back of the card too
            document.getElementById('fc-back-word').textContent = w.word;
            
            // Set YouGlish link on the back
            const cleanW = w.word.split(',')[0].replace(/^(der|die|das)\\s+/i, '').trim();
            document.getElementById('fc-back-youglish').href = `https://de.youglish.com/pronounce/${{encodeURIComponent(cleanW)}}/german`;

            document.getElementById('fc-examples-box').innerHTML = `
                ${{synonymsHtml}}
                ${{antonymsHtml}}
                ${{verbDetailsHtml}}
                ${{examplesHtml}}
            `;
            
            // Set level badge
            const lvlBadge = document.getElementById('fc-level-badge');
            lvlBadge.textContent = w.level;
            lvlBadge.className = `badge badge-level badge-${{w.level.toLowerCase()}}`;
            
            // Get stats and update meta
            const stats = getWordStats(w.word);
            document.getElementById('fc-front-status-icon').innerHTML = getStatusIconHtml(stats.status);
            document.getElementById('fc-front-status-icon').className = `fc-status-icon ${{stats.status}}`;
            document.getElementById('fc-front-stars').innerHTML = renderStarsDisplayHtml(stats.stars);
            
            document.getElementById('fc-back-status-icon').innerHTML = getStatusIconHtml(stats.status);
            document.getElementById('fc-back-status-icon').className = `fc-status-icon ${{stats.status}}`;
            document.getElementById('fc-back-stars').innerHTML = renderStarsDisplayHtml(stats.stars);
            
            if (isDailyReview) {{
                document.getElementById('fc-progress').textContent = `${{currentFlashcardIndex + 1}} / 50`;
                const percent = (currentFlashcardIndex / 50) * 100;
                document.getElementById('fc-progress-bar-fill').style.width = `${{percent}}%`;
            }} else {{
                document.getElementById('fc-progress').textContent = `${{currentFlashcardIndex + 1}} / ${{filteredWordsForFlashcards.length}}`;
            }}
            
            document.getElementById('flashcard-category-label').textContent = isDailyReview ? `Ежедневное ревью` : `Карточки: ${{w.category_name}}`;
        }}

        function flipCard() {{
            const card = document.getElementById('flashcard');
            card.classList.toggle('flipped');
            const fcActions = document.getElementById('fc-actions');
            if (card.classList.contains('flipped')) {{
                fcActions.classList.add('show');
            }} else {{
                fcActions.classList.remove('show');
            }}
        }}

        // Daily stats tracking
        function getDailyStats() {{
            return JSON.parse(localStorage.getItem('vocab_daily_stats') || '{{}}');
        }}
        function saveDailyStats(data) {{
            localStorage.setItem('vocab_daily_stats', JSON.stringify(data));
        }}
        function recordDailyAction(action) {{
            const today = new Date().toISOString().split('T')[0];
            const daily = getDailyStats();
            if (!daily[today]) daily[today] = {{ reviewed: 0, memorized: 0 }};
            daily[today].reviewed++;
            if (action === 'memorized') daily[today].memorized++;
            saveDailyStats(daily);
        }}

        function rateFlashcard(status) {{
            const w = filteredWordsForFlashcards[currentFlashcardIndex];
            if (!w) return;
            
            const stats = getWordStats(w.word);
            if (status === 'memorized') {{
                setWordStars(w.word, stats.stars + 1);
                setWordStatus(w.word, 'memorized');
                sessionStats.know++;
                recordDailyAction('memorized');
            }} else if (status === 'dont_know') {{
                setWordStars(w.word, 0); // Reset stars to 0 on "don't know"
                setWordStatus(w.word, 'dont_know');
                sessionStats.dontKnow++;
                recordDailyAction('dont_know');
            }}
            
            // Visual feedback animation
            const cardContainer = document.getElementById('flashcard');
            cardContainer.style.transform = 'scale(0.97)';
            
            setTimeout(() => {{
                cardContainer.style.transform = '';
                
                if (isDailyReview && currentFlashcardIndex === filteredWordsForFlashcards.length - 1) {{
                    // Finished review
                    document.getElementById('fc-progress-bar-fill').style.width = '100%';
                    document.getElementById('completion-know-count').textContent = sessionStats.know;
                    document.getElementById('completion-dontknow-count').textContent = sessionStats.dontKnow;
                    
                    document.getElementById('flashcard').style.display = 'none';
                    document.getElementById('fc-actions').style.display = 'none';
                    document.getElementById('fc-progress-bar-container').style.display = 'none';
                    document.querySelector('.flashcard-nav').style.display = 'none';
                    document.getElementById('fc-completion-screen').style.display = 'flex';
                }} else {{
                    nextCard();
                }}
            }}, 180);
        }}

        function nextCard() {{
            if (filteredWordsForFlashcards.length === 0) return;
            currentFlashcardIndex = (currentFlashcardIndex + 1) % filteredWordsForFlashcards.length;
            showFlashcard();
        }}

        function prevCard() {{
            if (filteredWordsForFlashcards.length === 0) return;
            currentFlashcardIndex = (currentFlashcardIndex - 1 + filteredWordsForFlashcards.length) % filteredWordsForFlashcards.length;
            showFlashcard();
        }}

        // ============= STATS DASHBOARD =============
        function openStatsDashboard() {{
            document.getElementById('grid-view-container').style.display = 'none';
            document.getElementById('flashcard-view-container').style.display = 'none';
            document.getElementById('fc-completion-screen').style.display = 'none';
            document.getElementById('stats-dashboard').style.display = 'block';
            renderStatsDashboard();
        }}

        function closeStatsDashboard() {{
            document.getElementById('stats-dashboard').style.display = 'none';
            document.getElementById('grid-view-container').style.display = 'block';
        }}

        function renderStatsDashboard() {{
            const daily = getDailyStats();
            const allStats = vocabStats;

            // Summary cards
            let totalReviewed = 0, totalMemorized = 0;
            Object.values(daily).forEach(d => {{ totalReviewed += d.reviewed; totalMemorized += d.memorized; }});

            const totalWordsInGroup = words.filter(w => (groupMapping[w.category_name] || 'Projektmanagement') === activeGroup).length;
            const learnedInGroup = words.filter(w => {{
                const grp = groupMapping[w.category_name] || 'Projektmanagement';
                if (grp !== activeGroup) return false;
                const s = allStats[w.word];
                return s && s.status === 'memorized' && s.stars >= 3;
            }}).length;

            document.getElementById('stats-summary-cards').innerHTML = `
                <div style="background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15)); padding: 18px; border-radius: 16px; border: 1px solid rgba(99,102,241,0.2); text-align: center;">
                    <div style="font-size: 2rem; font-weight: 800; color: #6366f1;">${{totalReviewed}}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 4px;">Всего просмотрено</div>
                </div>
                <div style="background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.15)); padding: 18px; border-radius: 16px; border: 1px solid rgba(16,185,129,0.2); text-align: center;">
                    <div style="font-size: 2rem; font-weight: 800; color: #10b981;">${{totalMemorized}}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 4px;">Запомнено</div>
                </div>
                <div style="background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(217,119,6,0.15)); padding: 18px; border-radius: 16px; border: 1px solid rgba(245,158,11,0.2); text-align: center;">
                    <div style="font-size: 2rem; font-weight: 800; color: #f59e0b;">${{learnedInGroup}} / ${{totalWordsInGroup}}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 4px;">Выучено (группа)</div>
                </div>
                <div style="background: linear-gradient(135deg, rgba(236,72,153,0.15), rgba(219,39,119,0.15)); padding: 18px; border-radius: 16px; border: 1px solid rgba(236,72,153,0.2); text-align: center;">
                    <div style="font-size: 2rem; font-weight: 800; color: #ec4899;">${{Object.keys(daily).length}}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 4px;">Дней обучения</div>
                </div>
            `;

            // Render Contribution Heatmap Grid (past 53 weeks)
            const today = new Date();
            const startDay = new Date(today);
            startDay.setDate(today.getDate() - 365); // Go back ~1 year
            const dayOfWeek = startDay.getDay();
            const shift = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
            startDay.setDate(startDay.getDate() - shift);

            const datesList = [];
            const currDate = new Date(startDay);
            while (currDate <= today) {{
                datesList.push(new Date(currDate));
                currDate.setDate(currDate.getDate() + 1);
            }}

            const weeks = [];
            let currentWeek = [];
            datesList.forEach((date, index) => {{
                currentWeek.push(date);
                if (date.getDay() === 0 || index === datesList.length - 1) {{
                    weeks.push(currentWeek);
                    currentWeek = [];
                }}
            }});

            const monthLabels = [];
            let lastMonthStr = '';
            const monthNames = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"];

            weeks.forEach((week, colIndex) => {{
                const firstDayOfWeek = week[0];
                const monthStr = monthNames[firstDayOfWeek.getMonth()];
                if (monthStr !== lastMonthStr) {{
                    monthLabels.push({{ name: monthStr, colIndex: colIndex }});
                    lastMonthStr = monthStr;
                }}
            }});

            const visibleMonthLabels = [];
            let lastCol = -5;
            monthLabels.forEach(lbl => {{
                if (lbl.colIndex - lastCol >= 3) {{
                    visibleMonthLabels.push(lbl);
                    lastCol = lbl.colIndex;
                }}
            }});

            const isDark = document.body.classList.contains('dark-theme');
            const bgEmpty = isDark ? '#161b22' : '#ebedf0';
            const colors = isDark 
                ? ['#0e4429', '#006d32', '#26a641', '#39d353'] 
                : ['#9be9a8', '#40c463', '#30a14e', '#216e39'];

            function getCellColor(count) {{
                if (!count || count === 0) return bgEmpty;
                if (count <= 10) return colors[0];
                if (count <= 30) return colors[1];
                if (count <= 50) return colors[2];
                return colors[3];
            }}

            let gridHtml = '<div style="display: grid; grid-template-rows: repeat(7, 10px); grid-auto-flow: column; gap: 3px; position: relative;">';
            
            let monthHeaderHtml = '<div style="display: flex; position: relative; height: 18px; margin-bottom: 5px; font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">';
            visibleMonthLabels.forEach(lbl => {{
                const leftPos = lbl.colIndex * 13;
                monthHeaderHtml += `<span style="position: absolute; left: ${{leftPos}}px;">${{lbl.name}}</span>`;
            }});
            monthHeaderHtml += '</div>';

            weeks.forEach(week => {{
                for (let dayIndex = 1; dayIndex <= 7; dayIndex++) {{
                    const targetDayNum = dayIndex === 7 ? 0 : dayIndex;
                    const dayDate = week.find(d => d.getDay() === targetDayNum);
                    
                    if (!dayDate) {{
                        gridHtml += `<div style="width: 10px; height: 10px; border-radius: 2px; background: transparent;"></div>`;
                    }} else {{
                        const dateStr = dayDate.toISOString().split('T')[0];
                        const stats = daily[dateStr] || {{ reviewed: 0, memorized: 0 }};
                        const totalCount = stats.reviewed;
                        const cellColor = getCellColor(totalCount);
                        
                        const dateOptions = {{ month: 'short', day: 'numeric' }};
                        const formattedDate = dayDate.toLocaleDateString('ru-RU', dateOptions);
                        const tooltipText = `${{totalCount}} слов пройдено на ${{formattedDate}}`;
                        
                        gridHtml += `
                            <div class="contrib-cell" 
                                 style="width: 10px; height: 10px; border-radius: 2px; background: ${{cellColor}}; cursor: pointer; position: relative;"
                                 data-tooltip="${{tooltipText}}">
                            </div>`;
                    }}
                }}
            }});
            gridHtml += '</div>';

            const heatmapHtml = `
                <div style="display: flex; flex-direction: column; margin-top: 15px; background: var(--bg-card); padding: 20px; border-radius: 16px; border: 1px solid var(--border-color); overflow-x: auto; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                    <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 15px; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
                        <i class="fa-solid fa-calendar-check" style="color: #6366f1;"></i> Календарь активности
                    </div>
                    <div style="display: flex; gap: 8px; min-width: 720px; align-self: flex-start; padding-bottom: 10px;">
                        <div style="display: flex; flex-direction: column; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); width: 25px; height: 88px; padding-top: 18px; font-weight: 500; line-height: 10px;">
                            <span>Пн</span>
                            <span>Ср</span>
                            <span>Пт</span>
                        </div>
                        
                        <div style="display: flex; flex-direction: column; flex-grow: 1;">
                            ${{monthHeaderHtml}}
                            ${{gridHtml}}
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; font-size: 0.72rem; color: var(--text-muted);">
                                <div>Всего за год: ${{totalReviewed}} просмотрено, ${{totalMemorized}} запомнено</div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <span>Меньше</span>
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: ${{bgEmpty}};"></div>
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: ${{colors[0]}};"></div>
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: ${{colors[1]}};"></div>
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: ${{colors[2]}};"></div>
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: ${{colors[3]}};"></div>
                                    <span>Больше</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <style>
                    .contrib-cell:hover::after {{
                        content: attr(data-tooltip);
                        position: absolute;
                        bottom: 15px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: #333;
                        color: #fff;
                        padding: 4px 8px;
                        font-size: 0.7rem;
                        border-radius: 4px;
                        white-space: nowrap;
                        z-index: 100;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        pointer-events: none;
                    }}
                </style>
            `;

            document.getElementById('stats-chart-area').innerHTML = heatmapHtml;
        }}
    </script>
</body>
</html>
"""
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

if __name__ == "__main__":
    main()
