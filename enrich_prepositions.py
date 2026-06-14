import os
import json
import re

# Dictionary mapping German verbs to their common prepositions in project management context
verb_prepositions = {
    'abnehmen': ['von + Dativ (у кого-то / от кого-то)'],
    'abrechnen': ['mit + Dativ (с кем-то)', 'über + Akkusativ (через что-то / по чему-то)'],
    'absagen': ['(Dativ) (кому-то / отказаться от чего-то)'],
    'abschließen': ['mit + Dativ (с чем-то)'],
    'abstimmen': ['mit + Dativ (с кем-то)', 'über + Akkusativ (о чём-то)'],
    'abweichen': ['von + Dativ (от чего-то)'],
    'auslasten': ['mit + Dativ (чем-то)'],
    'beitragen': ['zu + Dativ (к чему-то)'],
    'berichten': ['über + Akkusativ (о чём-то)', 'an + Akkusativ (кому-то)'],
    'besprechen': ['mit + Dativ (с кем-то)'],
    'delegieren': ['an + Akkusativ (кому-то)'],
    'einplanen': ['für + Akkusativ (для чего-то)', 'in + Akkusativ (в состав чего-то)'],
    'einsparen': ['an + Dativ (на чём-то)'],
    'einteilen': ['in + Akkusativ (на части/фазы)', 'für + Akkusativ (для выполнения чего-то)'],
    'erarbeiten': ['mit + Dativ (с кем-то)'],
    'eskalieren': ['an + Akkusativ (кому-то / на уровень кого-то)'],
    'festlegen': ['auf + Akkusativ (на чём-то / sich festlegen auf)'],
    'freigeben': ['für + Akkusativ (для чего-то)'],
    'gliedern': ['in + Akkusativ (на части/фазы)'],
    'hinterherhinken': ['mit + Dativ (в чём-то / отставать с чем-то)'],
    'kalkulieren': ['mit + Dativ (с чем-то / рассчитывать на что-то)'],
    'klären': ['mit + Dativ (с кем-то)'],
    'kommunizieren': ['mit + Dativ (с кем-то)', 'über + Akkusativ (о чём-то)'],
    'kooperieren': ['mit + Dativ (с кем-то)'],
    'koordinieren': ['mit + Dativ (с кем-то)'],
    'planen': ['für + Akkusativ (на какой-то период)', 'mit + Dativ (планировать с учётом чего-то)'],
    'scheitern': ['an + Dativ (на чём-то / из-за чего-то)'],
    'schätzen': ['auf + Akkusativ (во сколько-то)'],
    'testen': ['auf + Akkusativ (на предмет чего-то)'],
    'unterstützen': ['bei + Dativ (в чём-то)'],
    'vereinbaren': ['mit + Dativ (с кем-то)'],
    'verschieben': ['auf + Akkusativ (на какой-то срок)'],
    'verteilen': ['an + Akkusativ (кому-то)', 'auf + Akkusativ (между кем-то / на какой-то срок)'],
    'verzögern': ['durch + Akkusativ (из-за чего-то / sich verzögern durch)'],
    'zusammenarbeiten': ['mit + Dativ (с кем-то)', 'an + Dativ (над чем-то)'],
    'zuteilen': ['an + Akkusativ (кому-то)'],
    'zuweisen': ['an + Akkusativ (кому-то)', 'zu + Dativ (к чему-то)'],
    'übergeben': ['an + Akkusativ (кому-то)'],
    'überprüfen': ['auf + Akkusativ (на предмет чего-то)'],
    'übertragen': ['an + Akkusativ (кому-то)', 'auf + Akkusativ (на кого-то / что-то)'],
    'überziehen': ['um + Akkusativ (на сколько-то / превысить на сколько-то)']
}

def clean_word(word):
    clean = word.split(',')[0].strip()
    clean = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(.*\)', '', clean).strip()
    return clean

def main():
    base_dir = r"c:\Users\MMonakhov\Documents\ChatAI\Deutch"
    vocab_dir = os.path.join(base_dir, "german_vocab")
    
    for i in range(1, 8):
        file_path = os.path.join(vocab_dir, f"category_{i}.json")
        if not os.path.exists(file_path):
            continue
            
        print(f"Adding prepositions to file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        words = data.get("words", [])
        for w in words:
            pos = w.get("part_of_speech", "")
            if pos == "Verb":
                cleaned_verb = clean_word(w.get("word", ""))
                preps = verb_prepositions.get(cleaned_verb, [])
                w["prepositions"] = preps
                
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    print("Prepositions enrichment complete!")

if __name__ == "__main__":
    main()
