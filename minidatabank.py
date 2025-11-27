import json
import os
import sys
import re # NEU: Für E-Mail-Validierung
from typing import List, Dict, Any

# --- KONSTANTE ---
DATEI_NAME = 'meine_mini_db.json'

# ====================================================================
# I. DIE DATENSTRUKTUR-KLASSE (DATENKAPSELUNG & VALIDIERUNG)
# ====================================================================

class Person:
    """Repräsentiert einen einzelnen Datensatz (Eintrag) in der Datenbank."""
    def __init__(self, name: str, email: str, stadt: str, id: int = None):
        self.id = id
        self.name = name
        self.email = email
        self.stadt = stadt

    @staticmethod
    def pruefe_gueltigkeit(name: str, email: str, stadt: str) -> List[str]:
        """Prüft die Gültigkeit der Eingabedaten und gibt eine Liste von Fehlermeldungen zurück."""
        fehler = []
        
        if not name or name.strip() == "":
            fehler.append("Name darf nicht leer sein.")
            
        if not stadt or stadt.strip() == "":
            fehler.append("Stadt darf nicht leer sein.")
            
        # Einfache E-Mail-Validierung mit Regular Expression:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.fullmatch(email_regex, email):
            fehler.append(f"E-Mail-Adresse '{email}' ist ungültig.")
            
        return fehler
        
    def to_dict(self) -> Dict[str, Any]:
        """Wandelt das Objekt in ein Dictionary um, um es in JSON speichern zu können."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "stadt": self.stadt
        }

    def __str__(self) -> str:
        """Definiert die lesbare String-Repräsentation des Objekts."""
        return f"ID: {self.id}, Name: {self.name}, Email: {self.email}, Stadt: {self.stadt}"

    def __repr__(self) -> str:
        return f"Person(id={self.id}, name='{self.name}')"

# ====================================================================
# II. DIE DATENBANK KLASSE (LOGIK)
# ====================================================================

class MiniDatenbank:
    
    def __init__(self, dateiname: str):
        """Initialisiert die Datenbank: speichert den Dateinamen und lädt die Daten."""
        self.dateiname = dateiname
        self.daten: List[Person] = self._laden() 

    # --- PRIVATE METHODEN (Laden/Speichern) ---
    def _laden(self) -> List[Person]:
        """Lädt Daten aus der JSON-Datei und konvertiert sie in Person-Objekte."""
        try:
            if not os.path.exists(self.dateiname) or os.path.getsize(self.dateiname) == 0:
                print(f"Datei '{self.dateiname}' nicht gefunden oder leer. Starte mit einer leeren Datenbank.")
                return []
            with open(self.dateiname, 'r', encoding='utf-8') as f:
                daten_dicts = json.load(f)
            
            # Konvertiert geladene Dictionaries in Person-Objekte
            personen_objekte = [Person(**eintrag) for eintrag in daten_dicts]
            return personen_objekte
            
        except json.JSONDecodeError:
            print(f"Fehler: Datei '{self.dateiname}' ist fehlerhaftes JSON. Starte mit leerer DB.")
            return []
        except Exception as e:
            print(f"Fehler beim Laden: {e}")
            return []

    def _speichern(self):
        """Speichert die aktuellen Daten (Person-Objekte) in der JSON-Datei."""
        try:
            # Konvertiert Person-Objekte in Dictionaries zur Speicherung
            daten_zum_speichern = [person.to_dict() for person in self.daten]
            
            with open(self.dateiname, 'w', encoding='utf-8') as f:
                json.dump(daten_zum_speichern, f, indent=4)
            print(f"Daten erfolgreich in '{self.dateiname}' gespeichert.")
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")
            
    # --- CRUD METHODEN ---
    
    def hinzufuegen(self, neuer_eintrag: Person):
        """Fügt einen Eintrag hinzu (Create) und speichert. Inkl. E-Mail-Eindeutigkeitsprüfung."""
        
        # 1. EINDEUTIGKEITSPRÜFUNG (arbeitet mit Person-Objekten)
        email_neu = neuer_eintrag.email.lower()
        if any(p.email.lower() == email_neu for p in self.daten):
            print(f"❌ Fehler: E-Mail-Adresse '{neuer_eintrag.email}' existiert bereits. Eintrag nicht hinzugefügt.")
            return # Bricht die Funktion ab

        # 2. Auto-Inkrement ID
        neue_id = max(p.id for p in self.daten) + 1 if self.daten else 1
        neuer_eintrag.id = neue_id
        self.daten.append(neuer_eintrag)

        self._speichern()
        print(f"✅ Neuer Eintrag mit ID {neue_id} hinzugefügt.")

    def suchen(self, such_kriterien: Dict[str, str]) -> List[Person]:
        """Sucht nach exakten Kriterien (Name und/oder Stadt)."""
        ergebnisse = []
        for person in self.daten:
            passt = True
            eintrag_dict = person.to_dict() # Für einfache Feldsuche das Dictionary nutzen
            for key, value in such_kriterien.items():
                if eintrag_dict.get(key) is None or str(eintrag_dict.get(key, '')).lower() != str(value).lower():
                    passt = False
                    break
            if passt:
                ergebnisse.append(person)
        return ergebnisse

    def volltext_suche(self, suchbegriff: str) -> List[Person]:
        """Sucht nach einem Stichwort in allen Textfeldern."""
        if not suchbegriff:
            return []
            
        suchbegriff = suchbegriff.lower()
        ergebnisse = []

        for person in self.daten:
            # Durchsucht Name, Email, Stadt und ID (als String)
            search_fields = [
                str(person.name), 
                str(person.email), 
                str(person.stadt), 
                str(person.id)
            ]
            
            if any(suchbegriff in field.lower() for field in search_fields):
                ergebnisse.append(person)
                
        return ergebnisse
    
    def aendern(self, id_zum_aendern: int, neue_daten: Dict[str, str]):
        """Ändert existierende Daten eines Eintrags."""
        geaendert = False
        
        # NEUE OPTIMIERUNG: Vor der Änderung die Daten validieren
        # Wir müssen nur die Felder validieren, die geändert werden
        gepruefte_daten = {}
        for key, value in neue_daten.items():
            if key in ['name', 'email', 'stadt']:
                 if key == 'email':
                    # Einfache E-Mail-Validierung
                    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if not re.fullmatch(email_regex, value):
                        print(f"❌ Fehler: Neue E-Mail-Adresse '{value}' ist ungültig. Änderung abgebrochen.")
                        return
                 if not value or value.strip() == "":
                    print(f"❌ Fehler: Feld '{key}' darf nicht leer sein. Änderung abgebrochen.")
                    return
                 gepruefte_daten[key] = value

        if not gepruefte_daten:
            print("Keine gültigen Daten zum Ändern eingegeben.")
            return


        for person in self.daten:
            if person.id == id_zum_aendern:
                # Felder direkt am Objekt aktualisieren
                if 'name' in gepruefte_daten: person.name = gepruefte_daten['name']
                if 'email' in gepruefte_daten: person.email = gepruefte_daten['email']
                if 'stadt' in gepruefte_daten: person.stadt = gepruefte_daten['stadt']
                
                geaendert = True
                print(f"Eintrag mit ID {id_zum_aendern} erfolgreich aktualisiert.")
                break

        if geaendert:
            self._speichern()
        else:
            print(f"Fehler: Eintrag mit ID {id_zum_aendern} wurde nicht gefunden.")

    def loeschen(self, id_zum_loeschen: int):
        """Löscht einen Eintrag anhand seiner ID."""
        vorherige_laenge = len(self.daten)
        # Erstellt eine neue Liste ohne das zu löschende Person-Objekt
        self.daten = [
            person for person in self.daten
            if person.id != id_zum_loeschen
        ]

        geaendert = (vorherige_laenge > len(self.daten))

        if geaendert:
            self._speichern()
            print(f"Eintrag mit ID {id_zum_loeschen} erfolgreich gelöscht.")
        else:
            print(f"Fehler: Eintrag mit ID {id_zum_loeschen} wurde nicht gefunden.")


# ====================================================================
# III. HAUPTPROGRAMM (BENUTZER-INTERFACE)
# ====================================================================

def ergebnisse_anzeigen(ergebnisse: List[Person], sortiere_nach: str = 'id'):
    """
    Gibt die Liste der Person-Objekte leserlich aus und sortiert sie optional.
    """
    if not ergebnisse:
        print("-> Keine Einträge gefunden.")
        return

    # Sortierlogik: Funktioniert direkt mit den Attributen der Person-Objekte.
    if sortiere_nach:
        try:
            ergebnisse = sorted(
                ergebnisse, 
                # Nutzt getattr, um das Sortierfeld dynamisch abzurufen
                key=lambda p: str(getattr(p, sortiere_nach, '')).lower() 
            )
            print(f"--- {len(ergebnisse)} Ergebnis(se) gefunden (sortiert nach {sortiere_nach}) ---")
        except AttributeError:
             print(f"--- {len(ergebnisse)} Ergebnis(se) gefunden ---")
             print(f"⚠️ Warnung: Sortierung nach '{sortiere_nach}' fehlgeschlagen. Attribut existiert nicht.")
        except TypeError:
            print(f"--- {len(ergebnisse)} Ergebnis(se) gefunden ---")
            print(f"⚠️ Warnung: Sortierung nach '{sortiere_nach}' fehlgeschlagen (Typ-Fehler).")
    else:
        print(f"--- {len(ergebnisse)} Ergebnis(se) gefunden ---")

    # Ausgabe der Einträge (Nutzt die __str__ Methode der Person-Klasse)
    for person in ergebnisse:
        print(person)
    print("------------------------------------------")


def haupt_anwendung(db: MiniDatenbank):
    """Startet das Hauptmenü und die interaktive Steuerung der Datenbank."""
    
    print("\n--- 💻 Mini-Datenbank Verwaltung gestartet (Endgültige OOP-Version) ---")

    while True:
        print("\n--- Hauptmenü ---")
        print("1: Alle Einträge anzeigen (Read All)")
        print("2: Neuen Eintrag hinzufügen (Create)")
        print("3: Eintrag suchen (Query, exakte Felder)")
        print("4: Eintrag bearbeiten (Update)")
        print("5: Eintrag löschen (Delete)")
        print("7: Globale Volltextsuche (Search All Fields)")
        print("6: Beenden")
        
        wahl = input("Bitte wählen Sie eine Option (1-7, oder 6 zum Beenden): ")

        # --- 1: ALLE ANZEIGEN (READ) ---
        if wahl == '1':
            ergebnisse_anzeigen(db.daten, sortiere_nach='name')

        # --- 2: HINZUFÜGEN (CREATE) ---
        elif wahl == '2':
            print("\n-> Neuen Eintrag erstellen:")
            name = input("Name: ")
            email = input("E-Mail: ")
            stadt = input("Stadt: ")
            
            # NEUE VALIDIERUNG: Prüft die Eingaben des Benutzers
            validierungs_fehler = Person.pruefe_gueltigkeit(name, email, stadt)
            
            if validierungs_fehler:
                print("\n❌ Eingabe ungültig. Fehler:")
                for fehler in validierungs_fehler:
                    print(f"  - {fehler}")
                continue # Geht zurück zum Hauptmenü
            
            # Wenn Validierung erfolgreich: Erstellt Person-Objekt und fügt hinzu
            neuer_eintrag = Person(name=name, email=email, stadt=stadt)
            db.hinzufuegen(neuer_eintrag)

        # --- 3: SUCHEN (QUERY) ---
        elif wahl == '3':
            print("\n-> Nach mehreren Kriterien suchen (leer lassen, um zu ignorieren):")
            such_kriterien = {}
            name_such = input("Name (Suche, z.B. Max): ")
            if name_such: such_kriterien['name'] = name_such
            stadt_such = input("Stadt (Suche, z.B. Berlin): ")
            if stadt_such: such_kriterien['stadt'] = stadt_such
            
            if such_kriterien:
                ergebnisse = db.suchen(such_kriterien)
                ergebnisse_anzeigen(ergebnisse)
            else:
                print("Keine Suchkriterien eingegeben.")
        
        # --- 7: GLOBALE VOLLTEXTSUCHE ---
        elif wahl == '7':
            print("\n-> Globale Suche über alle Felder (Name, Email, Stadt, ID):")
            suchtext = input("Bitte geben Sie einen Suchbegriff ein: ")
            
            if suchtext:
                ergebnisse = db.volltext_suche(suchtext) 
                ergebnisse_anzeigen(ergebnisse)
            else:
                print("Suchbegriff darf nicht leer sein.")

        # --- 4: BEARBEITEN (UPDATE) ---
        elif wahl == '4':
            try:
                id_aendern = int(input("Geben Sie die ID des zu bearbeitenden Eintrags ein: "))
                print("Welche Felder möchten Sie ändern? (Leer lassen, um zu ignorieren)")
                neue_daten = {}
                neuer_name = input("Neuer Name: ")
                if neuer_name: neue_daten['name'] = neuer_name
                neue_email = input("Neue E-Mail: ")
                if neue_email: neue_daten['email'] = neue_email
                neue_stadt = input("Neue Stadt: ")
                if neue_stadt: neue_daten['stadt'] = neue_stadt

                if neue_daten:
                    db.aendern(id_aendern, neue_daten)
                else:
                    print("Keine Daten zum Ändern eingegeben.")

            except ValueError:
                print("Ungültige ID eingegeben.")

        # --- 5: LÖSCHEN (DELETE) ---
        elif wahl == '5':
            try:
                id_loeschen = int(input("Geben Sie die ID des zu löschenden Eintrags ein: "))
                db.loeschen(id_loeschen)
            except ValueError:
                print("Ungültige ID eingegeben.")

        # --- 6: BEENDEN ---
        elif wahl == '6':
            print("Datenbank-Verwaltung beendet. Alle Änderungen wurden gespeichert.")
            break

        # --- UNGÜLTIGE EINGABE ---
        else:
            print("Ungültige Wahl. Bitte eine Zahl von 1 bis 7 (oder 6 zum Beenden) eingeben.")


# ====================================================================
# IV. PROGRAMMSTART
# ====================================================================

if __name__ == "__main__":
    db_objekt = MiniDatenbank(DATEI_NAME)
    haupt_anwendung(db_objekt)
