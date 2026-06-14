import json
import os
import re
import urllib.request
import urllib.parse
import time
import shutil

# 1. Conjugator Logic
def conjugate_verb(verb):
    separable_prefixes = ['ab', 'an', 'auf', 'aus', 'bei', 'ein', 'mit', 'vor', 'zu', 'zusammen', 'hinterher']
    inseparable_prefixes = ['be', 'emp', 'ent', 'er', 'ge', 'miss', 'ver', 'zer', 'über', 'unter', 'gewähr']
    
    irregular_verbs = {
        'übernehmen': {
            'partizip_2': 'übernommen',
            'imperative': 'übernimm! / übernehmt! / übernehmen Sie!',
            'conjugations': {
                'ich': 'übernehme', 'du': 'übernimmst', 'er/sie/es': 'übernimmt',
                'wir': 'übernehmen', 'ihr': 'übernehmt', 'sie/Sie': 'übernehmen'
            }
        },
        'entwerfen': {
            'partizip_2': 'entworfen',
            'imperative': 'entwirf! / entwerft! / entwerfen Sie!',
            'conjugations': {
                'ich': 'entwerfe', 'du': 'entwirfst', 'er/sie/es': 'entwirft',
                'wir': 'entwerfen', 'ihr': 'entwerft', 'sie/Sie': 'entwerfen'
            }
        },
        'zuweisen': {
            'partizip_2': 'zugewiesen',
            'imperative': 'weise zu! / weist zu! / weisen Sie zu!',
            'conjugations': {
                'ich': 'weise zu', 'du': 'weist zu', 'er/sie/es': 'weist zu',
                'wir': 'weisen zu', 'ihr': 'weist zu', 'sie/Sie': 'weisen zu'
            }
        },
        'abschließen': {
            'partizip_2': 'abgeschlossen',
            'imperative': 'schließ ab! / schließt ab! / schließen Sie ab!',
            'conjugations': {
                'ich': 'schließe ab', 'du': 'schließt ab', 'er/sie/es': 'schließt ab',
                'wir': 'schließen ab', 'ihr': 'schließt ab', 'sie/Sie': 'schließen ab'
            }
        },
        'beitragen': {
            'partizip_2': 'beigetragen',
            'imperative': 'trage bei! / tragt bei! / tragen Sie bei!',
            'conjugations': {
                'ich': 'trage bei', 'du': 'trägst bei', 'er/sie/es': 'trägt bei',
                'wir': 'tragen bei', 'ihr': 'tragt bei', 'sie/Sie': 'tragen bei'
            }
        },
        'übertragen': {
            'partizip_2': 'übertragen',
            'imperative': 'übertrage! / übertragt! / übertragen Sie!',
            'conjugations': {
                'ich': 'übertrage', 'du': 'überträgst', 'er/sie/es': 'überträgt',
                'wir': 'übertragen', 'ihr': 'übertragt', 'sie/Sie': 'übertragen'
            }
        },
        'verschieben': {
            'partizip_2': 'verschoben',
            'imperative': 'verschiebe! / verschiebt! / verschieben Sie!',
            'conjugations': {
                'ich': 'verschiebe', 'du': 'verschiebst', 'er/sie/es': 'verschiebt',
                'wir': 'verschieben', 'ihr': 'verschiebt', 'sie/Sie': 'verschieben'
            }
        },
        'überziehen': {
            'partizip_2': 'überzogen',
            'imperative': 'überziehe! / überzieht! / überziehen Sie!',
            'conjugations': {
                'ich': 'überziehe', 'du': 'überziehst', 'er/sie/es': 'überzieht',
                'wir': 'überziehen', 'ihr': 'überzieht', 'sie/Sie': 'überziehen'
            }
        },
        'überschreiten': {
            'partizip_2': 'überschritten',
            'imperative': 'überschreite! / überschreitet! / überschreiten Sie!',
            'conjugations': {
                'ich': 'überschreite', 'du': 'überschreitest', 'er/sie/es': 'überschreitet',
                'wir': 'überschreiten', 'ihr': 'überschreitet', 'sie/Sie': 'überschreiten'
            }
        },
        'unterschreiten': {
            'partizip_2': 'unterschritten',
            'imperative': 'unterschreite! / unterschreitet! / unterschreiten Sie!',
            'conjugations': {
                'ich': 'unterschreite', 'du': 'unterschreitest', 'er/sie/es': 'unterschreitet',
                'wir': 'unterschreiten', 'ihr': 'unterschreitet', 'sie/Sie': 'unterschreiten'
            }
        },
        'freigeben': {
            'partizip_2': 'freigegeben',
            'imperative': 'gib frei! / gebt frei! / geben Sie frei!',
            'conjugations': {
                'ich': 'gebe frei', 'du': 'gibst frei', 'er/sie/es': 'gibt frei',
                'wir': 'geben frei', 'ihr': 'gebt frei', 'sie/Sie': 'geben frei'
            }
        },
        'besprechen': {
            'partizip_2': 'besprochen',
            'imperative': 'besprich! / besprecht! / besprechen Sie!',
            'conjugations': {
                'ich': 'bespreche', 'du': 'besprichst', 'er/sie/es': 'bespricht',
                'wir': 'besprechen', 'ihr': 'besprecht', 'sie/Sie': 'besprechen'
            }
        },
        'vermeiden': {
            'partizip_2': 'vermieden',
            'imperative': 'vermeide! / vermeidet! / vermeiden Sie!',
            'conjugations': {
                'ich': 'vermeide', 'du': 'vermeidest', 'er/sie/es': 'vermeidet',
                'wir': 'vermeiden', 'ihr': 'vermeidet', 'sie/Sie': 'vermeiden'
            }
        },
        'ergreifen': {
            'partizip_2': 'ergriffen',
            'imperative': 'ergreife! / ergreift! / ergreifen Sie!',
            'conjugations': {
                'ich': 'ergreife', 'du': 'ergreifst', 'er/sie/es': 'ergreift',
                'wir': 'ergreifen', 'ihr': 'ergreift', 'sie/Sie': 'ergreifen'
            }
        },
        'abnehmen': {
            'partizip_2': 'abgenommen',
            'imperative': 'nimm ab! / nehmt ab! / nehmen Sie ab!',
            'conjugations': {
                'ich': 'nehme ab', 'du': 'nimmst ab', 'er/sie/es': 'nimmt ab',
                'wir': 'nehmen ab', 'ihr': 'nehmt ab', 'sie/Sie': 'nehmen ab'
            }
        },
        'übergeben': {
            'partizip_2': 'übergeben',
            'imperative': 'übergib! / übergebt! / übergeben Sie!',
            'conjugations': {
                'ich': 'übergebe', 'du': 'übergibst', 'er/sie/es': 'übergibt',
                'wir': 'übergeben', 'ihr': 'übergebt', 'sie/Sie': 'übergeben'
            }
        },
        'abweichen': {
            'partizip_2': 'abgewichen',
            'imperative': 'weiche ab! / weicht ab! / weichen Sie ab!',
            'conjugations': {
                'ich': 'weiche ab', 'du': 'weichst ab', 'er/sie/es': 'weicht ab',
                'wir': 'weichen ab', 'ihr': 'weicht ab', 'sie/Sie': 'weichen ab'
            }
        },
        'einhalten': {
            'partizip_2': 'eingehalten',
            'imperative': 'halte ein! / haltet ein! / halten Sie ein!',
            'conjugations': {
                'ich': 'halte ein', 'du': 'hältst ein', 'er/sie/es': 'hält ein',
                'wir': 'halten ein', 'ihr': 'haltet ein', 'sie/Sie': 'halten ein'
            }
        },
        'scheitern': {
            'partizip_2': 'gescheitert',
            'imperative': 'scheitere! / scheitert! / scheitern Sie!',
            'conjugations': {
                'ich': 'scheitere', 'du': 'scheiterst', 'er/sie/es': 'scheitert',
                'wir': 'scheitern', 'ihr': 'scheitert', 'sie/Sie': 'scheitern'
            }
        }
    }
    
    if verb in irregular_verbs:
        return irregular_verbs[verb]
        
    prefix = ""
    base = verb
    is_separable = False
    
    for sep in sorted(separable_prefixes, key=len, reverse=True):
        if verb.startswith(sep) and verb != sep:
            prefix = sep
            base = verb[len(sep):]
            is_separable = True
            break
            
    if not base.endswith("en"):
        # Fallback for simple stem verbs
        stem = base[:-1]
    else:
        stem = base[:-2]
        
    insert_e = False
    if stem.endswith(('d', 't')) or (stem.endswith(('n', 'm')) and not stem.endswith(('rn', 'rm', 'ln', 'lm', 'ch', 'sch')) and len(stem) > 1 and stem[-2] not in ('a','e','i','o','u')):
        insert_e = True
        
    s_sound = stem.endswith(('s', 'ss', 'z', 'x', 'ß'))
    
    ich = stem + "e"
    du = stem + ("est" if insert_e else ("t" if s_sound else "st"))
    er = stem + ("et" if insert_e else "t")
    wir = base
    ihr = stem + ("et" if insert_e else "t")
    sie = base
    
    if is_separable:
        conj = {
            'ich': f"{ich} {prefix}",
            'du': f"{du} {prefix}",
            'er/sie/es': f"{er} {prefix}",
            'wir': f"{wir} {prefix}",
            'ihr': f"{ihr} {prefix}",
            'sie/Sie': f"{sie} {prefix}"
        }
        if base.endswith("ieren"):
            partizip_2 = f"{prefix}{stem}t"
        else:
            partizip_2 = f"{prefix}ge{stem}t"
            if insert_e:
                partizip_2 = f"{prefix}ge{stem}et"
                
        imp_du = f"{ich} {prefix}!"
        imp_ihr = f"{ihr} {prefix}!"
        imp_sie = f"{sie} Sie {prefix}!"
    else:
        conj = {
            'ich': ich,
            'du': du,
            'er/sie/es': er,
            'wir': wir,
            'ihr': ihr,
            'sie/Sie': sie
        }
        if verb.endswith("ieren"):
            partizip_2 = f"{stem}t"
        elif any(verb.startswith(p) for p in inseparable_prefixes):
            partizip_2 = f"{stem}t"
            if insert_e:
                partizip_2 = f"{stem}et"
        else:
            partizip_2 = f"ge{stem}t"
            if insert_e:
                partizip_2 = f"ge{stem}et"
                
        imp_du = f"{ich}!"
        imp_ihr = f"{ihr}!"
        imp_sie = f"{sie} Sie!"
        
    return {
        'partizip_2': partizip_2,
        'imperative': f"{imp_du} / {imp_ihr} / {imp_sie}",
        'conjugations': conj
    }

# 2. Synonyms Logic
def clean_word_for_synonyms(word):
    clean = word.split(',')[0].strip()
    clean = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(.*\)', '', clean).strip()
    return clean

manual_synonyms = {
    'Projektauftrag': ['Projektvereinbarung', 'Projektbriefing', 'Projektauftragsschreiben'],
    'Projektziel': ['Zielsetzung', 'Vorgabe', 'Soll-Vorgabe'],
    'Stakeholder': ['Interessengruppe', 'Beteiligte', 'Anspruchsgruppe'],
    'Planungsphase': ['Entwurfsphase', 'Konzeptionsphase'],
    'Projektplan': ['Ablaufplan', 'Terminplan', 'Meilensteinplan'],
    'Projektstart': ['Projektbeginn', 'Kick-off', 'Starttermin'],
    'Machbarkeitsstudie': ['Machbarkeitsanalyse', 'Durchführbarkeitsprüfung'],
    'Projektumfang': ['Scope', 'Leistungsumfang', 'Projektvolumen'],
    'Kick-off-Meeting': ['Starttreffen', 'Auftaktveranstaltung', 'Kick-off'],
    'Budgetplanung': ['Kostenplanung', 'Finanzplanung'],
    'Risikoanalyse': ['Risikobewertung', 'Risikoprüfung', 'Gefahrenanalyse'],
    'Stakeholder-Analyse': ['Umfeldanalyse', 'Beteiligtenanalyse'],
    'Lastenheft': ['Anforderungskatalog', 'Nutzeranforderungen'],
    'Pflichtenheft': ['Fachspezifikation', 'Realisierungskonzept'],
    'Projektleiter': ['Projektmanager', 'Projektführung', 'Projektleitung'],
    'Meilensteinplanung': ['Etappenplanung', 'Phasenplanung'],
    'Projektsteckbrief': ['Projektskizze', 'Projektübersicht'],
    'Zuständigkeit': ['Verantwortlichkeit', 'Kompetenzbereich'],
    'Aufgabenbereich': ['Zuständigkeitsbereich', 'Arbeitsbereich'],
    'Aufgabenteilung': ['Arbeitsteilung', 'Rollenverteilung'],
    'Fachexperte': ['Spezialist', 'Experte', 'Fachkraft'],
    'Zusammenarbeit': ['Kooperation', 'Kollaboration', 'Gemeinschaftsarbeit'],
    'Verantwortungsbereich': ['Zuständigkeitsbereich', 'Verantwortlichkeit'],
    'Mitarbeiter': ['Teammitglied', 'Personal', 'Beschäftigter'],
    'Ist-Zustand': ['Ausgangslage', 'Ist-Situation', 'Status quo'],
    'Soll-Zustand': ['Zielzustand', 'Soll-Situation', 'Soll-Vorgabe'],
    'Budget': ['Etat', 'Finanzmittel', 'Budgetierung'],
    'Ressource': ['Betriebsmittel', 'Hilfsmittel', 'Kapazitäten'],
    'Meilenstein': ['Etappenziel', 'Zwischenziel', 'Kontrollpunkt'],
    'Zeitplan': ['Terminkalender', 'Ablaufplan', 'Terminplan'],
    'Vorgabe': ['Richtlinie', 'Vorschrift', 'Anweisung'],
    'Priorität': ['Vorrang', 'Dringlichkeit'],
    'Entwurf': ['Konzept', 'Skizze', 'Vorlage'],
    'Erwartung': ['Anforderung', 'Hoffnung', 'Aussicht'],
    'Zielgruppe': ['Zielkreis', 'Käuferkreis'],
    'Genehmigung': ['Erlaubnis', 'Freigabe', 'Zulassung'],
    'Mandat': ['Auftrag', 'Vollmacht', 'Befugnis'],
    'Strategie': ['Konzept', 'Vorgehensweise', 'Plan'],
    'Strukturierung': ['Gliederung', 'Organisation', 'Systematisierung'],
    'Zielvereinbarung': ['Zielabkommen', 'Leistungsvereinbarung'],
    'Aufgabe': ['Arbeit', 'Tätigkeit', 'Verpflichtung'],
    'Rolle': ['Funktion', 'Position'],
    'Verantwortung': ['Haftung', 'Zuständigkeit'],
    'Teammitglied': ['Kollege', 'Mitarbeiter'],
    'Auftraggeber': ['Kunde', 'Besteller', 'Klient'],
    'Auftragnehmer': ['Dienstleister', 'Ausführer', 'Lieferant'],
    'Ansprechpartner': ['Kontaktperson', 'Referent'],
    'Zuteilung': ['Zuweisung', 'Allokation', 'Verteilung'],
    'Delegation': ['Übertragung', 'Bevollmächtigung'],
    'Abstimmung': ['Koordination', 'Absprache', 'Harmonisierung'],
    'Stellvertreter': ['Ersatz', 'Vertreter'],
    'Koordination': ['Abstimmung', 'Organisation', 'Steuerung'],
    'Ausführung': ['Umsetzung', 'Realisation', 'Implementierung'],
    'Entlastung': ['Befreiung', 'Unterstützung'],
    'Pflicht': ['Aufgabe', 'Verpflichtung'],
    'Zuweisung': ['Zuteilung', 'Zuordnung'],
    'Vertretung': ['Stellvertretung', 'Repräsentanz'],
    'Termin': ['Verabredung', 'Frist', 'Datum'],
    'Frist': ['Termin', 'Stichtag', 'Deadline'],
    'Verzögerung': ['Verspätung', 'Verzug', 'Mora'],
    'Zeiterfassung': ['Stundenerfassung', 'Zeitmessung'],
}

def fetch_synonyms(word):
    cleaned = clean_word_for_synonyms(word)
    if cleaned in manual_synonyms:
        return manual_synonyms[cleaned]
        
    try:
        encoded = urllib.parse.quote(cleaned)
        url = f"https://www.openthesaurus.de/synonyme/search?q={encoded}&format=application/json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        synsets = data.get('synsets', [])
        synonyms = []
        for synset in synsets:
            for term in synset.get('terms', []):
                t = term.get('term', '')
                t_clean = re.sub(r'\(.*\)', '', t).strip()
                if t_clean.lower() != cleaned.lower() and t_clean and len(t_clean.split()) <= 2:
                    if t_clean not in synonyms:
                        synonyms.append(t_clean)
        if synonyms:
            return synonyms[:3]
    except Exception as e:
        pass
        
    # Default fallbacks
    return []

# 3. Main runner
def main():
    base_dir = r"c:\Users\MMonakhov\Documents\ChatAI\Deutch"
    vocab_dir = os.path.join(base_dir, "german_vocab")
    backup_dir = os.path.join(base_dir, "german_vocab_backup")
    
    # Create backup first
    if not os.path.exists(backup_dir):
        shutil.copytree(vocab_dir, backup_dir)
        print(f"Created backup in: {backup_dir}")
    else:
        print(f"Backup already exists in: {backup_dir}")
        
    # Process files
    for i in range(1, 8):
        file_path = os.path.join(vocab_dir, f"category_{i}.json")
        if not os.path.exists(file_path):
            continue
            
        print(f"Enriching file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        words = data.get("words", [])
        for idx, w in enumerate(words):
            word = w.get("word", "")
            pos = w.get("part_of_speech", "")
            
            # Enrich with synonyms
            syns = fetch_synonyms(word)
            w["synonyms"] = syns
            
            # Enrich verbs
            if pos == "Verb":
                cleaned_verb = clean_word_for_synonyms(word)
                verb_info = conjugate_verb(cleaned_verb)
                w["partizip_2"] = verb_info['partizip_2']
                w["imperative"] = verb_info['imperative']
                w["conjugations"] = verb_info['conjugations']
            
            # Print progress
            if idx % 10 == 0:
                print(f"  Processed {idx}/{len(words)} words...")
            time.sleep(0.15) # avoid flooding API
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    print("Enrichment complete!")

if __name__ == "__main__":
    main()
