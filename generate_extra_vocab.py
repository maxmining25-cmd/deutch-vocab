# -*- coding: utf-8 -*-
import json
import os
import re
import sys

# Conjugator Logic (same as in enrich_all_json.py)
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
                'ich': 'übertrage', 'du': 'überägst', 'er/sie/es': 'überträgt',
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

def clean_word(word):
    clean = word.split(',')[0].strip()
    clean = re.sub(r'^(der|die|das|den|dem|des)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(.*\)', '', clean).strip()
    return clean

# Prepositions Mapping for new verbs
verb_prepositions = {
    'abheben': ['von + Dativ (снимать с чего-то / со счета)'],
    'ablehnen': ['(Akkusativ) (отклонять что-то)'],
    'absagen': ['(Dativ) (отказывать кому-то / отменять что-то)'],
    'abweichen': ['von + Dativ (отклоняться от чего-то)'],
    'anpassen': ['an + Akkusativ (приспосабливать к чему-то)'],
    'antworten': ['auf + Akkusativ (отвечать на что-то)'],
    'beantragen': ['(Akkusativ) (подавать заявление на что-то)'],
    'begründen': ['mit + Dativ (обосновывать чем-то)'],
    'beitragen': ['zu + Dativ (вносить вклад в что-то)'],
    'beraten': ['über + Akkusativ (консультировать о чем-то)'],
    'beteiligen': ['an + Dativ (sich beteiligen an / участвовать в чем-то)'],
    'eingehen auf': ['auf + Akkusativ (вникать во что-то / соглашаться на что-то)'],
    'einreichen': ['bei + Dativ (подавать в какое-то ведомство / организацию)'],
    'entscheiden': ['über + Akkusativ (решать о чем-то)', 'für + Akkusativ (sich entscheiden für / решаться в пользу чего-то)'],
    'erhöhen': ['um + Akkusativ (увеличить на сколько-то)', 'auf + Akkusativ (увеличить до какого-то значения)'],
    'erwarten': ['von + Dativ (ожидать от кого-то / чего-то)'],
    'fragen': ['nach + Dativ (спрашивать о чем-то)'],
    'handeln': ['mit + Dativ (торговать с кем-то)', 'von + Dativ (повествовать о чем-то)', 'um + Akkusativ (sich handeln um / речь идет о чем-то)'],
    'investieren': ['in + Akkusativ (инвестировать в что-то)'],
    'koordinieren': ['mit + Dativ (координировать с кем-то)'],
    'reisen': ['nach + Dativ (путешествовать в какую-то страну/город)', 'in + Akkusativ (путешествовать в какое-то место)'],
    'reklamieren': ['bei + Dativ (предъявлять претензии кому-то/в какое-то место)'],
    'scheitern': ['an + Dativ (потерпеть неудачу из-за чего-то)'],
    'senken': ['um + Akkusativ (снизить на сколько-то)', 'auf + Akkusativ (снизить до какого-то уровня)'],
    'sich anmelden': ['für + Akkusativ (зарегистрироваться на что-то)', 'bei + Dativ (зарегистрироваться у кого-то / в организации)'],
    'sich bedanken': ['bei + Dativ (благодарить кого-то)', 'für + Akkusativ (благодарить за что-то)'],
    'sich bewerben': ['um + Akkusativ (подавать заявление на какую-то должность)', 'bei + Dativ (подавать заявление в какую-то компанию)'],
    'sich verabschieden': ['von + Dativ (прощаться с кем-то)'],
    'sich verändern': ['zu + Dativ (измениться к чему-то)'],
    'sich vorbereiten': ['auf + Akkusativ (готовиться к чему-то)'],
    'sich vorstellen': ['(Dativ / Akkusativ) (представлять себе / представляться кому-то)'],
    'sparen': ['für + Akkusativ (копить на что-то)', 'an + Dativ (экономить на чём-то)'],
    'spekulieren': ['auf + Akkusativ (рассчитывать на что-то)', 'mit + Dativ (speкулировать чем-то)'],
    'spenden': ['an + Akkusativ (жертвовать кому-то)', 'für + Akkusativ (жертвовать на что-то)'],
    'steigen': ['um + Akkusativ (подняться на сколько-то)', 'auf + Akkusativ (подняться до какого-то уровня)'],
    'umsteigen': ['in + Akkusativ (пересаживаться в транспорт)'],
    'umtauschen': ['in + Akkusativ (обменивать на что-то / валюту)', 'gegen + Akkusativ (обменивать на другой товар)'],
    'umziehen': ['in + Akkusativ (переезжать в квартиру/дом)', 'nach + Dativ (переезжать в другой город/страну)'],
    'unterstützen': ['bei + Dativ (поддерживать в чём-то)'],
    'verhandeln': ['mit + Dativ (вести переговоры с кем-то)', 'über + Akkusativ (вести переговоры о чём-то)'],
    'versenden': ['an + Akkusativ (отправлять кому-то)'],
    'wechseln': ['zu + Dativ (перейти к чему-то другому / сменить на что-то)'],
    'zuhören': ['(Dativ) (слушать кого-то)'],
    'zusagen': ['(Dativ) (соглашаться / пообещать кому-то)'],
    'überweisen': ['auf + Akkusativ (переводить на какой-то счет)'],
    'überzeugen': ['von + Dativ (убеждать в чём-то)']
}

# Local high-quality synonyms fallback to avoid slow network queries
local_synonyms_db = {
    'Budget': ['Etat', 'Finanzmittel', 'Finanzrahmen'],
    'Kredit': ['Darlehen', 'Anleihe', 'Vorschuss'],
    'Steuer': ['Abgabe', 'Gebühr', 'Zoll'],
    'Aktie': ['Wertpapier', 'Anteilsschein', 'Anteil'],
    'Zinsen': ['Rendite', 'Gewinnbeteiligung', 'Ertrag'],
    'Umsatz': ['Einnahmen', 'Gesamtumsatz', 'Absatz'],
    'Gewinn': ['Profit', 'Ertrag', 'Überschuss'],
    'Verlust': ['Minus', 'Defizit', 'Einbuße'],
    'Bilanz': ['Jahresabschluss', 'Statusberichterstattung', 'Kassensturz'],
    'Börse': ['Aktienmarkt', 'Handelsplatz', 'Wertpapierbörse'],
    'Konto': ['Bankkonto', 'Guthaben', 'Kontoauszug'],
    'Schulden': ['Verbindlichkeiten', 'Rückstände', 'Passiva'],
    'Investition': ['Anlage', 'Geldanlage', 'Kapitalanlage'],
    'Bewerbung': ['Kandidatur', 'Gesuch', 'Stellengesuch'],
    'Lebenslauf': ['Werdegang', 'Curriculum Vitae', 'Vita'],
    'Stärke': ['Vorzug', 'Pluspunkt', 'Kompetenz'],
    'Schwäche': ['Mangel', 'Defizit', 'Fehler'],
    'Gehalt': ['Lohn', 'Verdienst', 'Einkommen'],
    'Karriere': ['Laufbahn', 'Werdegang', 'Aufstieg'],
    'Vorstellungsgespräch': ['Bewerbungsgespräch', 'Jobinterview', 'Gespräch'],
    'Zusage': ['Zustimmung', 'Zustimmungserklärung', 'Bewilligung'],
    'Absage': ['Ablehnung', 'Korb', 'Zurückweisung'],
    'Teamfähigkeit': ['Kooperationsbereitschaft', 'Gemeinsinn'],
    'Behörde': ['Amt', 'Dienststelle', 'Verwaltungsstelle'],
    'Amt': ['Behörde', 'Dienststelle', 'Institution'],
    'Formular': ['Vordruck', 'Dokument', 'Fragebogen'],
    'Antrag': ['Gesuch', 'Anfrage', 'Forderung'],
    'Wohnung': ['Unterkunft', 'Heim', 'Apartment'],
    'Anmeldung': ['Registrierung', 'Erfassung', 'Eintragung'],
    'Gesundheit': ['Wohlergehen', 'Fitness', 'Heilung'],
    'Reise': ['Fahrt', 'Ausflug', 'Tour'],
    'Kassenzettel': ['Quittung', 'Beleg', 'Kassenbon'],
    'Vertrag': ['Abkommen', 'Vereinbarung', 'Kontrakt'],
    'Arbeitsvertrag': ['Anstellungsvertrag', 'Arbeitskontrakt'],
    'Kontoeröffnung': ['Kontoeinrichtung'],
    'Sparen': ['Ansparen', 'Zurücklegen'],
    'Zahlung': ['Begleichung', 'Überweisung', 'Entrichtung'],
    'Finanzamt': ['Steuerbehörde'],
    'Steuererklärung': ['Steuerveranlagung'],
    'Bewerber': ['Kandidat', 'Interessent'],
    'Lebenslauf-Aufbau': ['Gliederung des Lebenslaufs'],
    'Arbeitsplatz': ['Büro', 'Stelle'],
    'Arbeitnehmer': ['Angestellter', 'Beschäftigter'],
    'Arbeitgeber': ['Chef', 'Unternehmen', 'Firma'],
    'Mitarbeiter': ['Kollege', 'Angestellter', 'Teammitglied'],
    'Unterlagen': ['Dokumente', 'Akten', 'Papiere'],
    'Anschrift': ['Adresse'],
    'Miete': ['Mietgebühr', 'Mietzahlung'],
    'Vermieter': ['Besitzer', 'Eigentümer'],
    'Mieter': ['Bewohner']
}

def fetch_synonyms(word):
    cleaned = clean_word(word)
    if cleaned in local_synonyms_db:
        return local_synonyms_db[cleaned]
    return []

# Template-based sentence generator
def generate_examples(word, part_of_speech, ru_trans):
    examples = []
    
    if part_of_speech == "Noun":
        parts = word.split(',')
        singular_part = parts[0].strip()
        plural_part = parts[1].strip() if len(parts) > 1 else ""
        
        m = re.match(r'^(der|die|das)\s+(.+)$', singular_part, re.IGNORECASE)
        if m:
            article = m.group(1).lower()
            noun = m.group(2).strip()
        else:
            article = ""
            noun = singular_part
            
        is_plural = "nur pl" in plural_part.lower() or (article == "die" and "plur" in plural_part.lower())
        
        acc_article = "den" if article == "der" else (article if article in ["die", "das"] else "")
        dat_article = "der" if article == "die" and not is_plural else ("dem" if article in ["der", "das"] else "den")
        
        singular_part_cap = singular_part[0].upper() + singular_part[1:]
        
        # 1. Nominative
        if is_plural:
            de_1 = f"Hier sind {singular_part}."
        else:
            de_1 = f"Hier ist {singular_part}."
        ru_1 = f"Вот {ru_trans}."
        
        # 2. Accusative
        de_2 = f"Wir müssen {acc_article} {noun} genau analysieren."
        ru_2 = f"Мы должны точно проанализировать следующий объект: {ru_trans}."
        
        # 3. Dative
        de_3 = f"Sind Sie mit {dat_article} {noun} einverstanden?"
        ru_3 = f"Вы согласны с тем, что касается понятия: {ru_trans}?"
        
        # 4. Accusative Preposition
        de_4 = f"Wir konzentrieren uns heute auf {acc_article} {noun}."
        ru_4 = f"Сегодня мы концентрируемся на теме: {ru_trans}."
        
        # 5. Subject
        if is_plural:
            de_5 = f"{singular_part_cap} spielen eine entscheidende Rolle für den Erfolg."
        else:
            de_5 = f"{singular_part_cap} spielt eine entscheidende Rolle für den Erfolg."
        ru_5 = f"{ru_trans[0].upper() + ru_trans[1:]} играет решающую роль в успехе."
        
        examples = [
            {"de": de_1, "ru": ru_1},
            {"de": de_2, "ru": ru_2},
            {"de": de_3, "ru": ru_3},
            {"de": de_4, "ru": ru_4},
            {"de": de_5, "ru": ru_5}
        ]
        
    elif part_of_speech == "Verb":
        is_reflexive = word.startswith("sich ")
        base_verb = word[5:] if is_reflexive else word
        
        conj = conjugate_verb(base_verb)
        wir_form = conj['conjugations']['wir']
        ich_form = conj['conjugations']['ich']
        er_form = conj['conjugations']['er/sie/es']
        partizip_2 = conj['partizip_2']
        
        imp_parts = [p.strip() for p in conj['imperative'].split('/')]
        imp_sie_raw = imp_parts[2] if len(imp_parts) > 2 else f"{base_verb} Sie"
        imp_sie = imp_sie_raw.replace("!", "").strip()
        
        if is_reflexive:
            wir_form_str = f"{wir_form} uns"
            ich_form_str = f"{ich_form} mich"
            er_form_str = f"{er_form} sich"
            partizip_2_str = f"uns {partizip_2}"
            imp_sie_str = f"{imp_sie} sich"
        else:
            wir_form_str = wir_form
            ich_form_str = ich_form
            er_form_str = er_form
            partizip_2_str = partizip_2
            imp_sie_str = imp_sie
            
        # 1. Wir form
        de_1 = f"Wir {wir_form_str} diese Angelegenheit direkt im Team."
        ru_1 = f"Мы {ru_trans} этот вопрос непосредственно в команде."
        
        # 2. Ich form
        de_2 = f"Ich {ich_form_str} die notwendigen Unterlagen sofort."
        ru_2 = f"Я {ru_trans} необходимые документы незамедлительно."
        
        # 3. Er form
        de_3 = f"Der verantwortliche Kollege {er_form_str} das Ganze sehr professionell."
        ru_3 = f"Ответственный коллега {ru_trans} всё это очень профессионально."
        
        # 4. Perfekt
        de_4 = f"Wir haben das Thema erfolgreich {partizip_2_str}."
        ru_4 = f"Мы успешно {ru_trans} (в прошедшем времени) эту тему."
        
        # 5. Imperative
        de_5 = f"{imp_sie_str} bitte rechtzeitig!"
        ru_5 = f"Пожалуйста, выполните действие: {ru_trans} вовремя!"
        
        examples = [
            {"de": de_1, "ru": ru_1},
            {"de": de_2, "ru": ru_2},
            {"de": de_3, "ru": ru_3},
            {"de": de_4, "ru": ru_4},
            {"de": de_5, "ru": ru_5}
        ]
        
    else:  # Adjective or Phrase
        de_1 = f"Dieses Verfahren ist wirklich {word}."
        ru_1 = f"Этот процесс действительно {ru_trans}."
        
        de_2 = f"Es ist sehr wichtig, dass alles {word} bleibt."
        ru_2 = f"Очень важно, чтобы всё оставалось {ru_trans}."
        
        de_3 = f"Wir arbeiten heute besonders {word}."
        ru_3 = f"Сегодня мы работаем особенно {ru_trans}."
        
        de_4 = f"Das erzielte Ergebnis ist sehr {word}."
        ru_4 = f"Полученный результат очень {ru_trans}."
        
        de_5 = f"Ich finde diese Arbeitsweise persönlich {word}."
        ru_5 = f"Я лично нахожу этот стиль работы {ru_trans}."
        
        examples = [
            {"de": de_1, "ru": ru_1},
            {"de": de_2, "ru": ru_2},
            {"de": de_3, "ru": ru_3},
            {"de": de_4, "ru": ru_4},
            {"de": de_5, "ru": ru_5}
        ]
        
    return examples

category_mapping = {
    # Finance
    "Finanzgrundlagen & Geld": 8,
    "Buchhaltung & Bilanz": 9,
    "Banken & Kredite": 10,
    "Steuern & Finanzamt": 11,
    "Investition & Börse": 12,
    # Interview
    "Bewerbung & Lebenslauf": 13,
    "Gesprächsablauf & Fragen": 14,
    "Stärken & Kompetenzen": 15,
    "Arbeitsbedingungen & Gehalt": 16,
    "Karriere & Weiterbildung": 17,
    # Official
    "Behörden & Formulare": 18,
    "Wohnung & Anmeldung": 19,
    "Gesundheit & Kassen": 20,
    "ÖPNV & Reisen": 21,
    "Alltag & Dienste": 22
}

category_names = {
    8: "Finanzgrundlagen & Geld",
    9: "Buchhaltung & Bilanz",
    10: "Banken & Kredite",
    11: "Steuern & Finanzamt",
    12: "Investition & Börse",
    13: "Bewerbung & Lebenslauf",
    14: "Gesprächsablauf & Fragen",
    15: "Stärken & Kompetenzen",
    16: "Arbeitsbedingungen & Gehalt",
    17: "Karriere & Weiterbildung",
    18: "Behörden & Formulare",
    19: "Wohnung & Anmeldung",
    20: "Gesundheit & Kassen",
    21: "ÖPNV & Reisen",
    22: "Alltag & Dienste"
}

def main():
    base_dir = r"c:\Users\MMonakhov\Documents\ChatAI\Deutch"
    vocab_dir = os.path.join(base_dir, "german_vocab")
    
    if not os.path.exists(vocab_dir):
        os.makedirs(vocab_dir)
        
    sys.path.append(base_dir)
    import finance_data
    import interview_data
    import official_data
    
    all_source_words = []
    all_source_words.extend(finance_data.words)
    all_source_words.extend(interview_data.words)
    all_source_words.extend(official_data.words)
    
    print(f"Total source words to process: {len(all_source_words)}")
    
    # Group words by category ID
    categorized_words = {cat_id: [] for cat_id in category_names.keys()}
    
    for item in all_source_words:
        word, pos, level, ru, en, subcat = item
        cat_id = category_mapping.get(subcat)
        if cat_id is None:
            print(f"Warning: subcategory '{subcat}' not mapped!")
            continue
        categorized_words[cat_id].append(item)
        
    # Process each category
    for cat_id, words in categorized_words.items():
        cat_name = category_names[cat_id]
        print(f"Processing Category {cat_id}: '{cat_name}' ({len(words)} words)...")
        
        json_words = []
        for idx, item in enumerate(words):
            word, pos, level, ru, en, subcat = item
            
            # 1. Local synonyms lookup
            syns = fetch_synonyms(word)
            
            # 2. Generate examples
            examples = generate_examples(word, pos, ru)
            
            word_obj = {
                "word": word,
                "part_of_speech": pos,
                "level": level,
                "translation_ru": ru,
                "translation_en": en,
                "examples": examples,
                "synonyms": syns
            }
            
            # 3. Add verb specific properties
            if pos == "Verb":
                cleaned_verb = clean_word(word)
                verb_info = conjugate_verb(cleaned_verb)
                word_obj["partizip_2"] = verb_info['partizip_2']
                word_obj["imperative"] = verb_info['imperative']
                word_obj["conjugations"] = verb_info['conjugations']
                
                # Add prepositions if we have them
                preps = verb_prepositions.get(cleaned_verb, [])
                word_obj["prepositions"] = preps
                
            json_words.append(word_obj)
            
        cat_data = {
            "category": cat_name,
            "words": json_words
        }
        
        file_path = os.path.join(vocab_dir, f"category_{cat_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cat_data, f, ensure_ascii=False, indent=2)
        print(f"Saved Category {cat_id} to {file_path}")
        
    print("All categories generated successfully!")

if __name__ == "__main__":
    main()
