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

# Descriptive User-Agent for Wikipedia API
WIKI_HEADERS = {
    "User-Agent": "LearnGermanVocabApp/1.0 (contact@myvocabapp.com; Python requests)"
}

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

def fetch_wikipedia_sentences(word):
    cleaned = clean_word(word)
    if not cleaned:
        return []
        
    search_url = f"https://de.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(cleaned)}&format=json"
    
    try:
        time.sleep(random.uniform(0.5, 1.5))
        r = requests.get(search_url, headers=WIKI_HEADERS, timeout=10)
        if r.status_code != 200:
            return []
            
        search_results = r.json()
        search_hits = search_results.get("query", {}).get("search", [])
        if not search_hits:
            return []
            
        titles = [hit["title"] for hit in search_hits[:3]]
        sentences = []
        seen = set()
        
        for title in titles:
            page_url = f"https://de.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=0&explaintext=1&titles={urllib.parse.quote(title)}&format=json"
            time.sleep(0.2)
            pr = requests.get(page_url, headers=WIKI_HEADERS, timeout=10)
            if pr.status_code == 200:
                page_data = pr.json()
                pages = page_data.get("query", {}).get("pages", {})
                for pid, pval in pages.items():
                    extract = pval.get("extract", "")
                    if not extract:
                        continue
                        
                    raw_sentences = re.split(r'\.\s+(?=[A-ZÄÖÜ])', extract)
                    for s in raw_sentences:
                        s = s.strip()
                        if s and not s.endswith('.'):
                            s += '.'
                            
                        # Case-insensitive containment check
                        if re.search(r'\b' + re.escape(cleaned) + r'\w*\b', s, re.IGNORECASE):
                            s = re.sub(r'\s+', ' ', s).strip()
                            if s not in seen and 25 < len(s) < 220:
                                seen.add(s)
                                sentences.append(s)
                                
        return sentences[:5]
    except Exception as e:
        print(f"Wikipedia exception for '{cleaned}': {e}")
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

# Dictionary of manual high-quality sentences for highly technical terms (SAP, Fiori, etc.)
MANUAL_SENTENCES = {
    "Fiori-App": [
        {"de": "Die neue Fiori-App erleichtert den Anwendern die Erfassung der täglichen Arbeitszeiten.", "ru": "Новое приложение Fiori упрощает пользователям ввод ежедневного рабочего времени."},
        {"de": "Wir müssen diese Fiori-App im Fiori Launchpad für die Buchhaltung aktivieren.", "ru": "Нам нужно активировать это приложение Fiori на панели запуска Fiori Launchpad для бухгалтерии."},
        {"de": "Der Berater konfigurierte die Fiori-App gemäß den Anforderungen des Kunden.", "ru": "Консультант настроил приложение Fiori в соответствии с требованиями клиента."}
    ],
    "Launchpad-Kachel": [
        {"de": "Jeder Benutzer kann seine eigene Launchpad-Kachel auf der Startseite hinzufügen oder entfernen.", "ru": "Каждый пользователь может добавлять или удалять свою собственную плитку Launchpad на домашней странице."},
        {"de": "Durch Klicken auf die Launchpad-Kachel wird die entsprechende SAP-Anwendung geöffnet.", "ru": "При нажатии на плитку Launchpad открывается соответствующее приложение SAP."},
        {"de": "Die Launchpad-Kachel zeigt dynamische Daten wie die Anzahl der offenen Aufgaben an.", "ru": "Плитка Launchpad отображает динамические данные, такие как количество открытых задач."}
    ],
    "Customizing-Menü": [
        {"de": "Im Customizing-Menü können wir die globalen Einstellungen für den Buchungskreis pflegen.", "ru": "В меню настроек (Customizing) мы можем вести глобальные параметры балансовой единицы."},
        {"de": "Dieser Parameter lässt sich direkt im Customizing-Menü über die Transaktion SPRO ändern.", "ru": "Этот параметр можно изменить непосредственно в меню настроек с помощью транзакции SPRO."}
    ],
    "Launchpad-Design": [
        {"de": "Das Launchpad-Design wurde an das Corporate Design des Unternehmens angepasst.", "ru": "Дизайн Launchpad был адаптирован под фирменный стиль компании."},
        {"de": "Ein benutzerfreundliches Launchpad-Design erhöht die Akzeptanz des SAP-Systems.", "ru": "Удобный дизайн Launchpad повышает готовность пользователей работать с системой SAP."}
    ],
    "Web-Dynpro-App": [
        {"de": "Einige ältere Transaktionen werden im Web-Browser als Web-Dynpro-App dargestellt.", "ru": "Некоторые старые транзакции отображаются в веб-браузере как приложение Web-Dynpro."},
        {"de": "Wir müssen die Web-Dynpro-App im Backend-System registrieren und testen.", "ru": "Нам нужно зарегистрировать и протестировать приложение Web-Dynpro в бэкэнд-системе."}
    ],
    "App-Inhalt": [
        {"de": "Der App-Inhalt wird basierend auf den Berechtigungen des Benutzers dynamisch geladen.", "ru": "Содержимое приложения загружается динамически на основе полномочий пользователя."},
        {"de": "Der Administrator pflegt den App-Inhalt in der Fiori-Datenbank.", "ru": "Администратор ведет содержимое приложения в базе данных Fiori."}
    ],
    "Kachel-Bibliothek": [
        {"de": "In der Kachel-Bibliothek finden Sie alle verfügbaren Standard-Apps für Ihre Rolle.", "ru": "В библиотеке плиток вы найдете все доступные стандартные приложения для вашей роли."},
        {"de": "Wir können neue Kacheln aus der Kachel-Bibliothek auf unserer Startseite platzieren.", "ru": "Мы можем размещать новые плитки из библиотеки плиток на нашей домашней странице."}
    ],
    "Kachel-Gruppe": [
        {"de": "Der Administrator hat eine neue Kachel-Gruppe für das Controlling-Team angelegt.", "ru": "Администратор создал новую группу плиток для команды контроллинга."},
        {"de": "Die Kachel-Gruppe strukturiert die Anwendungen übersichtlich auf dem Bildschirm.", "ru": "Группа плиток структурирует приложения на экране для наглядности."}
    ],
    "Zielzuordnung": [
        {"de": "Die Zielzuordnung verknüpft die Launchpad-Kachel mit der eigentlichen Anwendung.", "ru": "Целевое назначение связывает плитку Launchpad с самим приложением."},
        {"de": "Überprüfen Sie die Zielzuordnung, wenn die Kachel beim Anklicken einen Fehler anzeigt.", "ru": "Проверьте целевое назначение, если плитка выдает ошибку при нажатии."}
    ],
    "Cloud-Platform": [
        {"de": "Wir entwickeln unsere Erweiterungen auf der SAP Cloud-Platform.", "ru": "Мы разрабатываем наши расширения на SAP Cloud Platform."},
        {"de": "Die Cloud-Platform ermöglicht eine schnelle Integration verschiedener Systeme.", "ru": "Облачная платформа обеспечивает быструю интеграцию различных систем."}
    ],
    "OData-Schnittstelle": [
        {"de": "Die Fiori-App kommuniziert über eine sichere OData-Schnittstelle mit dem SAP-Backend.", "ru": "Приложение Fiori взаимодействует с бэкэндом SAP через безопасный интерфейс OData."},
        {"de": "Wir müssen die OData-Schnittstelle im SAP Gateway aktivieren.", "ru": "Нам необходимо активировать интерфейс OData в SAP Gateway."}
    ],
    "Gateway-Server": [
        {"de": "Der Gateway-Server leitet die Anfragen der mobilen Apps an das Backend-System weiter.", "ru": "Сервер Gateway перенаправляет запросы мобильных приложений в бэкэнд-систему."},
        {"de": "Der Gateway-Server steuert die Authentifizierung der Benutzer.", "ru": "Сервер Gateway управляет аутентификацией пользователей."}
    ],
    "Backend-System": [
        {"de": "Die eigentlichen betriebswirtschaftlichen Daten liegen im Backend-System.", "ru": "Фактические бизнес-данные находятся в бэкэнд-системе."},
        {"de": "Die OData-Services müssen im Backend-System registriert werden.", "ru": "Сервисы OData должны быть зарегистрированы в бэкэнд-системе."}
    ],
    "Frontend-System": [
        {"de": "Das Frontend-System stellt die Benutzeroberfläche für die Endanwender bereit.", "ru": "Фронтэнд-система предоставляет интерфейс пользователя для конечных пользователей."},
        {"de": "Alle Fiori-Kacheln und Launchpads werden im Frontend-System verwaltet.", "ru": "Все плитки Fiori и панели запуска управляются во фронтэнд-системе."}
    ],
    "Customizing": [
        {"de": "Nach der Installation müssen wir das Customizing für die Finanzbuchhaltung durchführen.", "ru": "После установки нам нужно выполнить настройку (Customizing) для финансовой бухгалтерии."},
        {"de": "Das Customizing erfolgt im Einführungsleitfaden über die Transaktion SPRO.", "ru": "Настройка (Customizing) выполняется в руководстве по внедрению через транзакцию SPRO."}
    ],
    "Einführungsleitfaden": [
        {"de": "Im Einführungsleitfaden sind alle Schritte zur Systemkonfiguration übersichtlich aufgelistet.", "ru": "В руководстве по внедрению наглядно перечислены все шаги по конфигурации системы."},
        {"de": "Wir folgen dem Einführungsleitfaden, um die neuen Steuersätze einzurichten.", "ru": "Мы следуем руководству по внедрению, чтобы настроить новые налоговые ставки."}
    ],
    "Customizing-Tabelle": [
        {"de": "Die neuen Buchungsschlüssel werden in einer Customizing-Tabelle gespeichert.", "ru": "Новые ключи проводки сохраняются в таблице настроек (Customizing-Tabelle)."},
        {"de": "Direkte Änderungen an einer Customizing-Tabelle im Produktivsystem sind untersagt.", "ru": "Прямые изменения в таблице настроек в продуктивной системе запрещены."}
    ],
    "Produktivsystem": [
        {"de": "Nach erfolgreichen Tests können wir die Änderungen in das Produktivsystem transportieren.", "ru": "После успешных тестов мы можем перенести изменения в продуктивную систему."},
        {"de": "Im Produktivsystem arbeiten die Mitarbeiter des Kunden mit realen Geschäftsdaten.", "ru": "В продуктивной системе сотрудники клиента работают с реальными бизнес-данными."}
    ],
    "Altdatenübernahme": [
        {"de": "Die Altdatenübernahme ist ein kritischer Schritt beim Go-Live des neuen SAP-Systems.", "ru": "Перенос исторических данных — это критически важный шаг при запуске новой системы SAP."},
        {"de": "Vor der Altdatenübernahme müssen wir alle Daten gründlich bereinigen.", "ru": "Перед переносом исторических данных нам необходимо тщательно очистить все данные."}
    ],
    "Lückenanalyse": [
        {"de": "Die Lückenanalyse zeigt die Abweichungen zwischen dem SAP-Standard und den Kundenanforderungen.", "ru": "Анализ расхождений (Lückenanalyse) показывает отклонения между стандартом SAP и требованиями клиента."},
        {"de": "Auf Basis der Lückenanalyse entscheiden wir, ob wir eine Eigenentwicklung benötigen.", "ru": "На основе анализа расхождений мы решаем, требуется ли нам собственная разработка."}
    ],
    "SAP-Einführungsprojekt": [
        {"de": "Das SAP-Einführungsprojekt erfordert eine enge Zusammenarbeit zwischen IT und Fachabteilung.", "ru": "Проект внедрения SAP требует тесного взаимодействия между ИТ и бизнес-подразделениями."},
        {"de": "Unser SAP-Einführungsprojekt befindet sich derzeit in der Realisierungsphase.", "ru": "Наш проект внедрения SAP в настоящее время находится на этапе реализации."}
    ],
    "Integrationstest": [
        {"de": "Im Integrationstest prüfen wir das Zusammenspiel verschiedener SAP-Module.", "ru": "В ходе интеграционного теста мы проверяем взаимодействие различных модулей SAP."},
        {"de": "Der Integrationstest muss vollständig dokumentiert werden.", "ru": "Интеграционный тест должен быть полностью задокументирован."}
    ],
    "Workbench-Objekt": [
        {"de": "Ein ABAP-Programm ist ein typisches Workbench-Objekt, das transportiert werden muss.", "ru": "Программа ABAP — это типичный объект Workbench, который должен быть перенесен."},
        {"de": "Jedes neue Workbench-Objekt muss einem Paket zugeordnet werden.", "ru": "Каждый новый объект Workbench должен быть назначен пакету."}
    ],
    "Tabellenpflege": [
        {"de": "Der Entwickler hat eine Tabellenpflege für die neue Customizing-Tabelle generiert.", "ru": "Разработчик сгенерировал ведение таблицы для новой настроечной таблицы."},
        {"de": "Über die Tabellenpflege können Anwender Daten direkt erfassen und ändern.", "ru": "Через ведение таблицы пользователи могут напрямую вводить и изменять данные."}
    ],
    "SAP-Standard-Verhalten": [
        {"de": "Wir sollten das SAP-Standard-Verhalten nicht ohne triftigen Grund ändern.", "ru": "Нам не следует менять стандартное поведение SAP без веской причины."},
        {"de": "Das SAP-Standard-Verhalten deckt die meisten Geschäftsprozesse bereits ab.", "ru": "Стандартное поведение SAP уже покрывает большинство бизнес-процессов."}
    ],
    "User-Exit": [
        {"de": "Wir nutzen einen User-Exit, um eine zusätzliche Validierung beim Speichern hinzuzufügen.", "ru": "Мы используем User-Exit, чтобы добавить дополнительную проверку при сохранении."},
        {"de": "Der User-Exit ermöglicht kundenspezifische Erweiterungen im SAP-Standard.", "ru": "User-Exit позволяет выполнять специфические для клиента расширения в стандарте SAP."}
    ],
    "ABAP": [
        {"de": "Die Geschäftslogik im ERP-System ist vollständig in ABAP geschrieben.", "ru": "Бизнес-логика в ERP-системе полностью написана на ABAP."},
        {"de": "Erfahrene Entwickler können komplexe Berichte in ABAP erstellen.", "ru": "Опытные разработчики могут создавать сложные отчеты на ABAP."}
    ],
    "ABAP-Entwickler": [
        {"de": "Wir suchen einen erfahrenen ABAP-Entwickler zur Unterstützung unseres Teams.", "ru": "Мы ищем опытного разработчика ABAP для поддержки нашей команды."},
        {"de": "Der ABAP-Entwickler implementiert die Anforderungen aus dem Fachkonzept.", "ru": "Разработчик ABAP реализует требования из функционального проекта."}
    ],
    "Anforderungserhebung": [
        {"de": "Die Anforderungserhebung findet in Workshops mit den Key-Usern statt.", "ru": "Сбор требований проходит на воркшопах с ключевыми пользователями."},
        {"de": "Eine präzise Anforderungserhebung verhindert spätere Verzögerungen im Projekt.", "ru": "Точный сбор требований предотвращает последующие задержки в проекте."}
    ],
    "Key-User": [
        {"de": "Der Key-User testet die neuen Funktionen und schult die Endanwender.", "ru": "Ключевой пользователь тестирует новые функции и обучает конечных пользователей."},
        {"de": "Die Key-User aus der Buchhaltung gaben grünes Licht für den Produktivstart.", "ru": "Ключевые пользователи из бухгалтерии дали зеленый свет на запуск в промышленную эксплуатацию."}
    ],
    "Testdrehbuch": [
        {"de": "Für den Integrationstest hat der Berater ein detailliertes Testdrehbuch erstellt.", "ru": "Для интеграционного теста консультант создал детальный сценарий тестирования (Testdrehbuch)."},
        {"de": "Jeder Schritt im Testdrehbuch muss vom Tester abgezeichnet werden.", "ru": "Каждый шаг в сценарии тестирования должен быть подписан тестером."}
    ],
    "Hypercare-Phase": [
        {"de": "Nach dem Go-Live unterstützt das Projektteam den Kunden in der Hypercare-Phase.", "ru": "После запуска проекта команда проекта поддерживает клиента на этапе усиленной поддержки (Hypercare)."},
        {"de": "Die Hypercare-Phase dauert in der Regel vier Wochen.", "ru": "Этап усиленной поддержки обычно длится четыре недели."}
    ],
    "Ticket-Volumen": [
        {"de": "Das Ticket-Volumen stieg direkt nach dem Produktivstart kurzzeitig an.", "ru": "Объем тикетов кратковременно вырос сразу после запуска в эксплуатацию."},
        {"de": "Durch Schulungen konnten wir das Ticket-Volumen im Support reduzieren.", "ru": "Благодаря обучению мы смогли сократить объем тикетов в поддержке."}
    ],
    "Datenbereinigung": [
        {"de": "Die Datenbereinigung im Altsystem spart viel Zeit bei der Datenmigration.", "ru": "Очистка данных в старой системе экономит много времени при миграции данных."},
        {"de": "Für die Datenbereinigung sind die Fachabteilungen verantwortlich.", "ru": "За очистку данных несут ответственность бизнес-подразделения."}
    ],
    "Schnittstellenabstimmung": [
        {"de": "Die Schnittstellenabstimmung mit den externen Partnern läuft planmäßig.", "ru": "Согласование интерфейсов с внешними партнерами идет по плану."},
        {"de": "Wir müssen die Schnittstellenabstimmung vor dem Integrationstest abschließen.", "ru": "Нам необходимо завершить согласование интерфейсов перед интеграционным тестом."}
    ],
    "Migrationswerkzeug": [
        {"de": "Als Migrationswerkzeug nutzen wir das bewährte SAP S/4HANA Migration Cockpit.", "ru": "В качестве инструмента миграции мы используем проверенный SAP S/4HANA Migration Cockpit."},
        {"de": "Das Migrationswerkzeug importiert die Daten automatisch aus Excel-Vorlagen.", "ru": "Инструмент миграции автоматически импортирует данные из шаблонов Excel."}
    ],
    "Mapping-Regel": [
        {"de": "Die Mapping-Regel bestimmt, wie die alten Kontonummern in die neuen übersetzt werden.", "ru": "Правило сопоставления (Mapping-Regel) определяет, как старые номера счетов переводятся в новые."},
        {"de": "Wir müssen jede Mapping-Regel im Migrationswerkzeug definieren.", "ru": "Мы должны определить каждое правило сопоставления в инструменте миграции."}
    ],
    "Quellfeld": [
        {"de": "Der Wert aus dem Quellfeld wird in das entsprechende Zielfeld übertragen.", "ru": "Значение из исходного поля переносится в соответствующее целевое поле."},
        {"de": "Das Quellfeld in der Alttabelle hat eine Länge von zehn Zeichen.", "ru": "Исходное поле в старой таблице имеет длину десять символов."}
    ],
    "Konvertierungsregel": [
        {"de": "Die Konvertierungsregel wandelt das Datumsformat der Altdaten um.", "ru": "Правило преобразования изменяет формат даты исторических данных."},
        {"de": "Wir haben eine kundenspezifische Konvertierungsregel für die Kundennummern implementiert.", "ru": "Мы внедрили специфическое для клиента правило преобразования для номеров клиентов."}
    ],
    "Sandbox-System": [
        {"de": "Im Sandbox-System können wir neue Customizing-Ideen ohne Risiko ausprobieren.", "ru": "В системе песочницы (Sandbox) мы можем без риска опробовать новые идеи настроек."},
        {"de": "Das Sandbox-System wurde gestern mit aktuellen Daten aktualisiert.", "ru": "Система песочницы была обновлена вчера актуальными данными."}
    ],
    "Release-Upgrade": [
        {"de": "Am Wochenende führen wir ein Release-Upgrade auf dem Testsystem durch.", "ru": "В выходные мы проведем обновление релиза в тестовой системе."},
        {"de": "Ein Release-Upgrade bringt neue Funktionen und Sicherheitsupdates.", "ru": "Обновление релиза приносит новые функции и обновления безопасности."}
    ],
    "SAP-Hinweis": [
        {"de": "Dieser Fehler lässt sich durch das Einspielen eines SAP-Hinweises beheben.", "ru": "Эту ошибку можно исправить, применив ноту SAP (SAP-Hinweis)."},
        {"de": "Der Berater suchte im SAP-Support-Portal nach einem passenden SAP-Hinweis.", "ru": "Консультант искал подходящую ноту SAP на портале поддержки SAP."}
    ],
    "Systemaktualisierung": [
        {"de": "Die geplante Systemaktualisierung findet außerhalb der Arbeitszeiten statt.", "ru": "Запланированное обновление системы происходит в нерабочее время."},
        {"de": "Während der Systemaktualisierung ist das SAP-System nicht erreichbar.", "ru": "Во время обновления системы система SAP недоступна."}
    ],
    "Wiederherstellungszeit": [
        {"de": "Die maximale Wiederherstellungszeit im Katastrophenfall beträgt vier Stunden.", "ru": "Максимальное время восстановления в случае катастрофы составляет четыре часа."},
        {"de": "Wir testen die Wiederherstellungszeit bei unserer jährlichen Notfallübung.", "ru": "Мы тестируем время восстановления во время ежегодных учений по чрезвычайным ситуациям."}
    ],
    "Katastrophenfall-Vorsorge": [
        {"de": "Die Katastrophenfall-Vorsorge sieht tägliche Backups an einem separaten Standort vor.", "ru": "Аварийное планирование предусматривает ежедневное резервное копирование в отдельном месте."},
        {"de": "Ein wichtiger Teil der Katastrophenfall-Vorsorge ist der Disaster-Recovery-Plan.", "ru": "Важной частью планирования действий на случай чрезвычайных ситуаций является план аварийного восстановления."}
    ],
    "Berechtigungskonzept": [
        {"de": "Das neue Berechtigungskonzept schützt sensible Personaldaten vor unbefugtem Zugriff.", "ru": "Новая концепция полномочий защищает конфиденциальные данные персонала от несанкционированного доступа."},
        {"de": "Der Sicherheitsbeauftragte muss das Berechtigungskonzept genehmigen.", "ru": "Сотрудник по безопасности должен утвердить концепцию полномочий."}
    ],
    "Stressresistenz": [
        {"de": "In diesem Job ist eine hohe Stressresistenz unbedingt erforderlich.", "ru": "На этой работе обязательно требуется высокая стрессоустойчивость."},
        {"de": "Ihre Stressresistenz hilft Ihnen, auch in schwierigen Situationen ruhig zu bleiben.", "ru": "Ваша стрессоустойчивость помогает вам сохранять спокойствие даже в сложных ситуациях."}
    ],
    "Diplomatiegespür": [
        {"de": "Als Projektleiter benötigt er viel Diplomatiegespür im Umgang mit Kunden.", "ru": "Как руководителю проекта, ему требуется большое чувство дипломатии при общении с клиентами."},
        {"de": "Mit Diplomatiegespür lassen sich Konflikte im Team schnell lösen.", "ru": "С чувством дипломатии конфликты в команде можно решить быстро."}
    ],
    "Gemeinschaftkonto": [
        {"de": "Eheleute können ein Gemeinschaftskonto für die Haushaltskasse einrichten.", "ru": "Супруги могут открыть совместный счет для ведения домашнего хозяйства."},
        {"de": "Für das Gemeinschaftskonto sind beide Partner gleichberechtigt zeichnungsberechtigt.", "ru": "Для совместного счета оба партнера имеют одинаковые права подписи."}
    ],
    "Buchungsperiode": [
        {"de": "Die Buchungsperiode für den Vormonat muss geschlossen werden.", "ru": "Период проводки для предыдущего месяца должен быть закрыт."},
        {"de": "Wir können Buchungen nur in einer geöffneten Buchungsperiode erfassen.", "ru": "Мы можем вводить проводки только в открытом периоде проводки."}
    ],
    "Saldenbilanz": [
        {"de": "Die Saldenbilanz dient zur Überprüfung der Buchungen vor dem Jahresabschluss.", "ru": "Оборотный баланс служит для проверки проводок перед закрытием финансового года."},
        {"de": "Der Wirtschaftsprüfer prüft die Saldenbilanz des Mandanten.", "ru": "Аудитор проверяет оборотный баланс клиента."}
    ],
    "Kostenstelle": [
        {"de": "Jede Abteilung im Unternehmen hat eine eigene Kostenstelle zur Erfassung der Ausgaben.", "ru": "Каждый отдел в компании имеет собственное место возникновения затрат для учета расходов."},
        {"de": "Wir müssen die Kostenstelle auf der Bestellung angeben.", "ru": "Мы должны указать место возникновения затрат в заказе."}
    ],
    "Kontenrahmen": [
        {"de": "Der Kontenrahmen strukturiert die Konten für die Finanzbuchhaltung.", "ru": "План счетов структурирует счета для финансовой бухгалтерии."},
        {"de": "Für deutsche Unternehmen ist der Gemeinschaftskontenrahmen (GKR) üblich.", "ru": "Для немецких компаний является привычным единый план счетов (GKR)."}
    ],
    "Kreditorenbuchhaltung": [
        {"de": "Die Kreditorenbuchhaltung bearbeitet die eingehenden Rechnungen der Lieferanten.", "ru": "Бухгалтерия кредиторов обрабатывает входящие счета поставщиков."},
        {"de": "Er arbeitet als Buchhalter in der Kreditorenbuchhaltung.", "ru": "Он работает бухгалтером в бухгалтерии кредиторов."}
    ],
    "Debitorenbuchhaltung": [
        {"de": "Die Debitorenbuchhaltung überwacht die Zahlungseingänge der Kunden.", "ru": "Бухгалтерия дебиторов отслеживает поступления платежей от клиентов."},
        {"de": "Offene Posten der Kunden werden in der Debitorenbuchhaltung geklärt.", "ru": "Открытые позиции клиентов выравниваются в бухгалтерии дебиторов."}
    ],
    "Buchungskreis": [
        {"de": "Ein Buchungskreis stellt eine eigenständige bilanzierende Einheit dar.", "ru": "Балансовая единица представляет собой независимую единицу бухгалтерского учета."},
        {"de": "Wir müssen Berichte auf Ebene des Buchungskreises erstellen.", "ru": "Мы должны формировать отчеты на уровне балансовой единицы."}
    ],
    "Sachkonto": [
        {"de": "Jede Buchung im Hauptbuch erfolgt auf ein bestimmtes Sachkonto.", "ru": "Каждая проводка в Главной книге выполняется на определенный счет главной книги."},
        {"de": "Der Steuerberater legte ein neues Sachkonto für Reisekosten an.", "ru": "Налоговый консультант создал новый счет главной книги для командировочных расходов."}
    ],
    "Kostenstellenrechnung": [
        {"de": "Die Kostenstellenrechnung hilft bei der Analyse der Gemeinkosten.", "ru": "Учет затрат по МВЗ помогает в анализе накладных расходов."},
        {"de": "Im SAP-System ist die Kostenstellenrechnung ein Teil des CO-Moduls.", "ru": "В системе SAP учет затрат по МВЗ является частью модуля CO."}
    ],
    "Kostenart": [
        {"de": "Die Kostenart klassifiziert die betrieblichen Aufwendungen im Controlling.", "ru": "Вид затрат классифицирует операционные расходы в контроллинге."},
        {"de": "Wir unterscheiden zwischen primären und sekundären Kostenarten.", "ru": "Мы различаем первичные и вторичные виды затрат."}
    ],
    "Innenauftrag": [
        {"de": "Ein Innenauftrag dient zur Überwachung der Kosten für ein internes Event.", "ru": "Внутренний заказ служит для мониторинга затрат на внутреннее мероприятие."},
        {"de": "Die Kosten auf dem Innenauftrag müssen am Periodenende abgerechnet werden.", "ru": "Затраты по внутреннему заказу должны быть рассчитаны в конце периода."}
    ],
    "Profit-Center-Accounting": [
        {"de": "Das Profit-Center-Accounting dient der internen Unternehmenssteuerung.", "ru": "Учет по центрам прибыли служит для целей внутреннего управления компанией."},
        {"de": "Wir werten die Erlöse im Profit-Center-Accounting aus.", "ru": "Мы анализируем выручку в учете по центрам прибыли."}
    ],
    "Ergebnisrechnung": [
        {"de": "Die Ergebnisrechnung ermittelt den Erfolg einzelner Marktsegmente.", "ru": "Учет результатов определяет финансовый успех отдельных сегментов рынка."},
        {"de": "Der Vertriebsvorstand analysiert die Berichte aus der Ergebnisrechnung.", "ru": "Директор по продажам анализирует отчеты из учета результатов."}
    ],
    "Anlagenspiegel": [
        {"de": "Der Anlagenspiegel zeigt die Entwicklung des Anlagevermögens über das Geschäftsjahr.", "ru": "Ведомость движения основных средств показывает изменение основных средств за отчетный год."},
        {"de": "Der Anlagenspiegel ist ein Pflichtbestandteil des Jahresabschlusses.", "ru": "Ведомость движения основных средств является обязательной частью годовой отчетности."}
    ],
    "Schlussrechnung": [
        {"de": "Nach Abschluss der Bauarbeiten stellte das Unternehmen die Schlussrechnung.", "ru": "После завершения строительных работ компания выставила финальный счет."},
        {"de": "Wir prüfen die Schlussrechnung auf eventuelle Abweichungen vom Angebot.", "ru": "Мы проверяем финальный счет на предмет возможных отклонений от предложения."}
    ],
    "Zahllauf": [
        {"de": "Der Zahllauf wird jeden Donnerstag automatisch gestartet.", "ru": "Прогон программы платежей запускается автоматически каждый четверг."},
        {"de": "Der Abteilungsleiter muss die Zahlungsliste nach dem Zahllauf freigeben.", "ru": "Руководитель отдела должен утвердить платежный реестр после прогона программы платежей."}
    ],
    "Mahnverfahren": [
        {"de": "Wenn der Kunde nicht zahlt, müssen wir das Mahnverfahren einleiten.", "ru": "Если клиент не платит, нам придется запустить процедуру напоминания платежей."},
        {"de": "Das Mahnverfahren läuft in mehreren Stufen ab.", "ru": "Процедура напоминания платежей проходит в несколько этапов."}
    ],
    "Mahnlauf": [
        {"de": "Der wöchentliche Mahnlauf selektiert alle überfälligen Rechnungen.", "ru": "Еженедельный прогон программы напоминаний выбирает все просроченные счета."},
        {"de": "Die Mahnungen werden nach dem Mahnlauf gedruckt und versendet.", "ru": "Напоминания распечатываются и отправляются после прогона программы напоминаний."}
    ],
    "Übergangskonto": [
        {"de": "Zahlungen auf dem Übergangskonto müssen täglich geklärt werden.", "ru": "Платежи на транзитном счете должны выравниваться ежедневно."},
        {"de": "Wir buchen den Geldeingang zunächst auf ein Übergangskonto.", "ru": "Мы временно проводим поступление денежных средств на транзитный счет."}
    ],
    "Abstimmvereinbarung": [
        {"de": "Wir haben eine Abstimmvereinbarung mit der Tochtergesellschaft getroffen.", "ru": "Мы заключили соглашение о выравнивании с дочерней компанией."},
        {"de": "Die Abstimmvereinbarung regelt die Details der Intercompany-Abstimmung.", "ru": "Соглашение о выравнивании регулирует детали сверки межфилиальных расчетов."}
    ],
    "Abstimmkonto": [
        {"de": "Das Abstimmkonto verbindet die Nebenbuchhaltung mit dem Hauptbuch.", "ru": "Контрольный счет связывает вспомогательную книгу с Главной книгой."},
        {"de": "Direkte Buchungen auf ein Abstimmkonto sind im SAP-System gesperrt.", "ru": "Прямые проводки на контрольный счет заблокированы в системе SAP."}
    ],
    "Kontenplan": [
        {"de": "Der Kontenplan legt die Struktur und die Nummernkreise der Konten fest.", "ru": "План счетов определяет структуру и диапазоны номеров счетов."},
        {"de": "Wir nutzen einen einheitlichen Kontenplan für alle Gesellschaften.", "ru": "Мы используем единый план счетов для всех юридических лиц."}
    ],
    "Saldovortrag": [
        {"de": "Der Saldovortrag der Sachkonten erfolgt zu Beginn des neuen Geschäftsjahres.", "ru": "Перенос сальдо по счетам главной книги выполняется в начале нового финансового года."},
        {"de": "Überprüfen Sie den Saldovortrag vor den ersten Buchungen im neuen Jahr.", "ru": "Проверьте перенос сальдо перед первыми проводками в новом году."}
    ],
    "Zahllast": [
        {"de": "Die Zahllast muss bis zum zehnten Tag des Folgemonats an das Finanzamt überwiesen werden.", "ru": "Сумма налога к уплате должна быть перечислена в налоговую службу до десятого числа следующего месяца."},
        {"de": "Die Zahllast berechnet sich aus Umsatzsteuer minus Vorsteuer.", "ru": "Сумма налога к уплате рассчитывается как исходящий НДС минус входящий НДС."}
    ],
    "Sachkontenbuch": [
        {"de": "Alle Buchungsbelege werden chronologisch im Sachkontenbuch erfasst.", "ru": "Все бухгалтерские документы хронологически регистрируются в книге счетов Главной книги."},
        {"de": "Das Sachkontenbuch liefert den Nachweis über alle Finanztransaktionen.", "ru": "Регистр счетов Главной книги служит подтверждением всех финансовых операций."}
    ],
    "Belegaufteilung": [
        {"de": "Die Belegaufteilung ermöglicht eine Bilanzierung auf Segmentebene.", "ru": "Разделение документа (document splitting) позволяет формировать баланс на уровне сегментов."},
        {"de": "Die Regeln für die Belegaufteilung müssen im Customizing genau definiert sein.", "ru": "Правила разделения документа должны быть точно определены в настройках."}
    ],
    "Konzernwährung": [
        {"de": "Die Konzernwährung unserer Muttergesellschaft ist der US-Dollar.", "ru": "Концерновой валютой нашей материнской компании является доллар США."},
        {"de": "Alle lokalen Abschlüsse werden in die Konzernwährung umgerechnet.", "ru": "Все локальные отчеты переводятся в концерновую валюту."}
    ],
    "Kreiswährung": [
        {"de": "Die Kreiswährung entspricht der gesetzlichen Währung des Landes.", "ru": "Местная валюта соответствует законной валюте страны."},
        {"de": "Der Buchungskreis führt seine Bücher in der Kreiswährung Euro.", "ru": "Балансовая единица ведет свои книги в местной валюте евро."}
    ],
    "Fremdwährungsbewertung": [
        {"de": "Die Fremdwährungsbewertung wird im Rahmen des Monatsabschlusses durchgeführt.", "ru": "Оценка в иностранной валюте выполняется в рамках закрытия месяца."},
        {"de": "Bei der Fremdwährungsbewertung werden offene Posten zum aktuellen Stichtagskurs bewertet.", "ru": "При оценке в иностранной валюте открытые позиции оцениваются по текущему курсу на отчетную дату."}
    ],
    "Kursdifferenzkonto": [
        {"de": "Gewinne und Verluste aus Kursschwankungen werden auf das Kursdifferenzkonto gebucht.", "ru": "Прибыли и убытки от колебаний курсов проводятся на счет курсовых разниц."},
        {"de": "Das Kursdifferenzkonto muss im Customizing hinterlegt sein.", "ru": "Счет курсовых разниц должен быть прописан в настройках."}
    ],
    "Intercompany-Geschäft": [
        {"de": "Für das Intercompany-Geschäft müssen wir spezielle Verrechnungskonten nutzen.", "ru": "Для межфилиальных сделок мы должны использовать специальные счета выравнивания."},
        {"de": "Die Konsolidierung eliminiert die Umsätze aus dem Intercompany-Geschäft.", "ru": "Консолидация исключает выручку от межфилиальных сделок."}
    ],
    "Kostenstellen-Gruppe": [
        {"de": "Wir haben eine neue Kostenstellen-Gruppe für alle Produktionsabteilungen angelegt.", "ru": "Мы создали новую группу МВЗ для всех производственных отделов."},
        {"de": "Die Kostenstellen-Gruppe vereinfacht das Berichtswesen im Controlling.", "ru": "Группа МВЗ упрощает отчетность в контроллинге."}
    ],
    "Profit-Center-Gruppe": [
        {"de": "Der Vertriebsbereich West ist einer bestimmten Profit-Center-Gruppe zugeordnet.", "ru": "Сбытовой регион Запад назначен определенной группе центров прибыли."},
        {"de": "Wir können Berichte für eine gesamte Profit-Center-Gruppe erstellen.", "ru": "Мы можем формировать отчеты по всей группе центров прибыли."}
    ],
    "Standardhierarchie": [
        {"de": "Die Standardhierarchie umfasst alle Kostenstellen des Buchungskreises.", "ru": "Стандартная иерархия включает в себя все МВЗ балансовой единицы."},
        {"de": "Jede neu angelegte Kostenstelle muss der Standardhierarchie zugeordnet werden.", "ru": "Каждое вновь созданное МВЗ должно быть отнесено к стандартной иерархии."}
    ],
    "Plankalkulation": [
        {"de": "Die Plankalkulation ermittelt die Standardkosten für das kommende Jahr.", "ru": "Плановая калькуляция определяет стандартную себестоимость на предстоящий год."},
        {"de": "Die Plankalkulation muss vor Beginn des neuen Geschäftsjahres freigegeben werden.", "ru": "Плановая калькуляция должна быть утверждена до начала нового финансового года."}
    ],
    "Istkalkulation": [
        {"de": "Die Istkalkulation ermittelt die tatsächlichen Produktionskosten am Periodenende.", "ru": "Фактическая калькуляция определяет фактические производственные затраты в конце периода."},
        {"de": "Das Material-Ledger nutzt die Istkalkulation zur Bestandsbewertung.", "ru": "Регистр материалов использует фактическую калькуляцию для оценки запасов."}
    ],
    "Tarifermittlung": [
        {"de": "Die Tarifermittlung berechnet den Verrechnungssatz für eine Leistungsart.", "ru": "Расчет тарифа определяет ставку списания для вида работ."},
        {"de": "Die iterative Tarifermittlung berücksichtigt gegenseitige Leistungsbeziehungen.", "ru": "Итерационный расчет тарифа учитывает взаимное оказание услуг."}
    ],
    "Abweichungsanalyse": [
        {"de": "Die Abweichungsanalyse zeigt die Differenzen zwischen Plan- und Istkosten.", "ru": "Анализ отклонений показывает разницу между плановыми и фактическими затратами."},
        {"de": "Nach der Abweichungsanalyse leiten wir Korrekturmaßnahmen ein.", "ru": "После проведения анализа отклонений мы предпринимаем корректирующие меры."}
    ],
    "Deckungsbeitragsrechnung": [
        {"de": "Die Deckungsbeitragsrechnung hilft uns bei der Beurteilung der Produktprofitabilität.", "ru": "Учет маржинального дохода помогает нам оценить рентабельность продукции."},
        {"de": "In der Deckungsbeitragsrechnung werden die variablen Kosten von den Erlösen abgezogen.", "ru": "В учете маржинального дохода переменные затраты вычитаются из выручки."}
    ],
    "Buchungsschlüssel": [
        {"de": "Der Buchungsschlüssel steuert die Soll-Haben-Buchung und die Kontoart.", "ru": "Ключ проводки управляет дебетованием/кредитованием и видом счета."},
        {"de": "Der Buchungsschlüssel 40 steht für eine Soll-Buchung auf einem Sachkonto.", "ru": "Ключ проводки 40 означает дебетовую проводку по счету Главной книги."}
    ],
    "Abstimmungsarbeit": [
        {"de": "Die Abstimmungsarbeit vor dem Jahresabschluss erfordert viel Geduld.", "ru": "Работа по сверке перед закрытием года требует большого терпения."},
        {"de": "Durch Automatisierung konnten wir die Abstimmungsarbeit erheblich reduzieren.", "ru": "Благодаря автоматизации мы смогли значительно сократить работу по сверке."}
    ],
    "Monatsabschluss": [
        {"de": "Der Monatsabschluss muss bis zum dritten Werktag des Folgemonats fertig sein.", "ru": "Закрытие месяца должно быть завершено к третьему рабочему дню следующего месяца."},
        {"de": "Alle Buchungen müssen vor dem Monatsabschluss vollständig erfasst werden.", "ru": "Все проводки должны быть полностью введены перед закрытием месяца."}
    ],
    "Zahlungsbeleg": [
        {"de": "Drucken Sie den Zahlungsbeleg als Nachweis für die Überweisung aus.", "ru": "Распечатайте платежный документ в качестве подтверждения перевода."},
        {"de": "Der Zahlungsbeleg wird automatisch beim Ausführen des Zahllaufs erzeugt.", "ru": "Платежный документ создается автоматически при выполнении прогона платежей."}
    ],
    "Wertberichtigung": [
        {"de": "Für zweifelhafte Forderungen müssen wir eine Wertberichtigung buchen.", "ru": "По сомнительной дебиторской задолженности мы должны провести корректировку стоимости."},
        {"de": "Die Wertberichtigung mindert den Gewinn des aktuellen Geschäftsjahres.", "ru": "Корректировка стоимости уменьшает прибыль текущего отчетного года."}
    ],
    "Rechnungsabgrenzung": [
        {"de": "Die Rechnungsabgrenzung stellt die periodengerechte Gewinnermittlung sicher.", "ru": "Разграничение доходов и расходов обеспечивает определение прибыли по периодам."},
        {"de": "Die Miete für Januar müssen wir im Dezember als Rechnungsabgrenzung buchen.", "ru": "Аренду за январь мы должны провести в декабре как расходы будущих периодов."}
    ],
    "Anzahlungsanforderung": [
        {"de": "Wir haben dem Kunden eine Anzahlungsanforderung über dreißig Prozent geschickt.", "ru": "Мы отправили клиенту запрос авансового платежа в размере тридцати процентов."},
        {"de": "Die Anzahlungsanforderung ist eine statistische Buchung ohne Erfolgswirkung.", "ru": "Запрос авансового платежа — это статистическая проводка, не влияющая на прибыль."}
    ],
    "Umsatzsteuer-Voranmeldung": [
        {"de": "Die Umsatzsteuer-Voranmeldung muss monatlich elektronisch übermittelt werden.", "ru": "Предварительная декларация по НДС должна ежемесячно подаваться в электронном виде."},
        {"de": "Der Buchhalter bereitet die Umsatzsteuer-Voranmeldung für das Finanzamt vor.", "ru": "Бухгалтер готовит предварительную декларацию по НДС для налоговой службы."}
    ],
    "Steuerkennzeichen": [
        {"de": "Das Steuerkennzeichen ermittelt automatisch den korrekten Steuersatz.", "ru": "Налоговый код автоматически определяет правильную ставку налога."},
        {"de": "Verwenden Sie das Steuerkennzeichen V1 für inländische Vorsteuer.", "ru": "Используйте налоговый код V1 для расчета входящего НДС внутри страны."}
    ],
    "Abschreibungsbereich": [
        {"de": "Wir nutzen einen Abschreibungsbereich für die Handelsbilanz und einen für die Steuerbilanz.", "ru": "Мы используем одну область амортизации для торгового баланса и другую — для налогового баланса."},
        {"de": "Der Abschreibungsbereich definiert die Nutzungsdauer der Anlage.", "ru": "Область амортизации определяет срок полезного использования основного средства."}
    ],
    "Abschreibungsschlüssel": [
        {"de": "Der Abschreibungsschlüssel steuert die Methode und den Prozentsatz der Abschreibung.", "ru": "Код амортизации управляет методом и процентной ставкой амортизации."},
        {"de": "Für Gebäude nutzen wir einen linearen Abschreibungsschlüssel.", "ru": "Для зданий мы используем код линейной амортизации."}
    ]
}

def enrich_from_wiki_or_manual(word):
    cleaned = clean_word(word)
    
    # Check manual sentences first
    if cleaned in MANUAL_SENTENCES:
        print(f"  [Manual] Found manual sentences for '{cleaned}'")
        return MANUAL_SENTENCES[cleaned]
        
    # Try Wikipedia
    sentences = fetch_wikipedia_sentences(word)
    if sentences:
        formatted = []
        for de_s in sentences:
            ru_s = translate_to_russian(de_s)
            if ru_s:
                formatted.append({"de": de_s, "ru": ru_s})
        if len(formatted) >= 2:
            print(f"  [Wikipedia] Successfully fetched {len(formatted)} sentences.")
            return formatted
            
    # Try direct translations for simple cases or fallback templates but make them realistic
    return []

def main():
    category_files = sorted(
        [f for f in os.listdir(VOCAB_DIR) if f.startswith("category_") and f.endswith(".json")],
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    
    total_enriched = 0
    total_failed = 0
    failed_words = []
    
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
                print(f"Enriching: '{word_str}'")
                
                # Check cache first
                cleaned = clean_word(word_str)
                if cleaned in cache and cache[cleaned]:
                    w["examples"] = cache[cleaned]
                    updated = True
                    total_enriched += 1
                    print(f"  [Cache] Loaded from cache.")
                    continue
                    
                sentences = enrich_from_wiki_or_manual(word_str)
                if sentences:
                    w["examples"] = sentences
                    cache[cleaned] = sentences
                    updated = True
                    total_enriched += 1
                    save_cache()
                else:
                    total_failed += 1
                    failed_words.append((file_name, word_str))
                    print(f"  [Failed] No sentences found for '{word_str}'.")
                    
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved changes to {file_name}")
            
    print(f"\nEnrichment complete. Total enriched: {total_enriched}, Total failed: {total_failed}")
    if failed_words:
        print("\n--- Failed Words ---")
        for f_file, f_word in failed_words:
            print(f"  {f_file}: {f_word}")
            
if __name__ == "__main__":
    main()
