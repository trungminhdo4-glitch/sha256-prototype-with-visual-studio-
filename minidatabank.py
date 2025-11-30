import tkinter as tk
from tkinter import messagebox
from tkinter import ttk 
import json
import os
import sys
import re 
from typing import List, Dict, Any, Optional, Set
from operator import attrgetter
from datetime import datetime

# Pydantic muss installiert sein: pip install pydantic
from pydantic import BaseModel, EmailStr, ValidationError

# --- KONSTANTE ---
DATEI_NAME = 'meine_mini_db.json'
STADT_DATEI_NAME = 'staedte_db.json' 

# ====================================================================
# I. DIE DATENSTRUKTUR-KLASSEN (NORMALISIERT)
# ====================================================================

# NEU: Pydantic-Modell für die Stadt-Entität
class Stadt(BaseModel):
    id: Optional[int] = None
    name: str
    
    class Config:
        from_attributes = True

# Pydantic-Modell für die Basisdaten (speichert ID)
class PersonBase(BaseModel):
    name: str
    email: EmailStr 
    stadt_id: int 
    erstellungsdatum: Optional[datetime] = None
    
# Pydantic-Modell für das Erstellen eines neuen Eintrags
class PersonCreate(PersonBase):
    pass

# Pydantic-Modell für das Ändern/Update
class PersonUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    stadt_id: Optional[int] = None 
    
# Pydantic-Modell für das Lesen von Daten (inkl. ID)
class Person(PersonBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True

# --- ZURÜCKFALL-MODELL FÜR DIE MIGRATION (ALTES FORMAT) ---
class _OldPerson(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr
    stadt: str # WICHTIG: Altes Feld war 'stadt' (string)
    erstellungsdatum: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ====================================================================
# II. DIE DATENBANK KLASSE (LOGIK) - MIT MIGRATION
# ====================================================================

class MiniDatenbank:
    
    def __init__(self, dateiname: str, stadt_dateiname: str):
        self.dateiname = dateiname
        self.stadt_dateiname = stadt_dateiname
        
        self.staedte: List[Stadt] = []
        self.daten: List[Person] = []
        
        # Indizes (werden beim Laden/Speichern aktualisiert)
        self._email_index: Set[str] = set() 
        self._stadt_namen_map: Dict[str, int] = {}
        self._stadt_id_map: Dict[int, str] = {}
        
        self._initialisiere_daten()

    # --- MIGRATIONS- UND INITIALISIERUNGSLOGIK ---
    def _initialisiere_daten(self):
        """Versucht, Daten im neuen Format zu laden oder migriert alte Daten."""
        
        # 1. Versuche, die Daten im NEUEN Format zu laden
        self.staedte = self._laden(self.stadt_dateiname, Stadt)
        self.daten = self._laden(self.dateiname, Person)
        
        # 2. Prüfe, ob eine Migration nötig ist (Datenbank ist leer, aber Datei existiert)
        if not self.daten and os.path.exists(self.dateiname) and os.path.getsize(self.dateiname) > 0:
            print("INFO: Alte Datenbankstruktur erkannt. Starte Migration...")
            try:
                self._migrieren_daten()
            except Exception as e:
                print(f"SCHWERWIEGENDER FEHLER bei der Migration: {e}")
                messagebox.showerror("Migrationsfehler", "Konnte alte Datenbank nicht konvertieren. Die Daten wurden übersprungen.")
                
        # 3. Indizes basierend auf den geladenen/migrierten Daten neu aufbauen
        self._baue_indizes_neu()
        print(f"INFO: {len(self.daten)} Personen und {len(self.staedte)} Städte geladen.")


    def _migrieren_daten(self):
        """Liest die alte (unnormalisierte) Datei und konvertiert sie."""
        
        alt_daten = self._laden(self.dateiname, _OldPerson)
        if not alt_daten:
            return
            
        neue_personen: List[Person] = []
        
        for old_person in alt_daten:
            # 1. Stadt-ID für den alten Stadtnamen ermitteln/erstellen
            stadt_id = self.finde_oder_erstelle_stadt(old_person.stadt, migrieren=True) 
            
            # 2. Neue Person-Objekt erstellen
            neue_person = Person(
                id=old_person.id,
                name=old_person.name,
                email=old_person.email,
                stadt_id=stadt_id,
                erstellungsdatum=old_person.erstellungsdatum
            )
            neue_personen.append(neue_person)

        self.daten = neue_personen
        
        # Speichere die migrierten Daten sofort, um das alte Format zu ersetzen
        self._speichern_alle()
        messagebox.showinfo("Datenmigration abgeschlossen", f"Erfolgreich {len(self.daten)} Einträge aus altem Format konvertiert. Die Daten wurden nun normalisiert gespeichert.")


    def _baue_indizes_neu(self):
        """Baut alle Indizes basierend auf self.daten und self.staedte neu auf."""
        self._email_index = {p.email.lower() for p in self.daten}
        self._stadt_namen_map = {s.name.lower(): s.id for s in self.staedte if s.id is not None}
        self._stadt_id_map = {s.id: s.name for s in self.staedte if s.id is not None}


    # --- PRIVATE METHODEN (Laden/Speichern) ---
    def _laden(self, dateiname: str, model: type[BaseModel]) -> List[BaseModel]:
        """Generische Lademethode."""
        try:
            if not os.path.exists(dateiname) or os.path.getsize(dateiname) == 0:
                return []
            with open(dateiname, 'r', encoding='utf-8') as f:
                daten_dicts = json.load(f)
            return [model(**eintrag) for eintrag in daten_dicts]
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            # Im Migrationsfall wollen wir hier den Fehler *nicht* behandeln
            # da wir eine andere Validierung probieren werden.
            if model == Person: # Nur wenn das Laden des neuen Formats fehlschlägt
                return []
            raise # Wenn das OldPerson-Modell fehlschlägt, ist die Datei kaputt


    def _speichern(self, daten_objekte: List[BaseModel], dateiname: str):
        """Generische atomare Speichermethode."""
        temp_dateiname = dateiname + ".tmp"
        try:
            daten_zum_speichern = [obj.model_dump(mode='json') for obj in daten_objekte]
            
            with open(temp_dateiname, 'w', encoding='utf-8') as f:
                json.dump(daten_zum_speichern, f, indent=4)
            
            os.replace(temp_dateiname, dateiname)
        except Exception as e:
            print(f"FEHLER beim atomaren Speichern von '{dateiname}': {e}")
            if os.path.exists(temp_dateiname):
                 os.remove(temp_dateiname)

    def _speichern_alle(self):
        """Speichert beide Listen (Personen und Städte)."""
        self._speichern(self.daten, self.dateiname)
        self._speichern(self.staedte, self.stadt_dateiname)

    # --- STADT-HELPER ---
    def finde_oder_erstelle_stadt(self, stadt_name: str, migrieren: bool = False) -> int:
        """Sucht Stadt-ID oder erstellt neuen Stadt-Eintrag, gibt ID zurück."""
        stadt_name_lower = stadt_name.lower().strip()
        if not stadt_name_lower:
            raise ValueError("Stadtname darf nicht leer sein.")

        if stadt_name_lower in self._stadt_namen_map:
            return self._stadt_namen_map[stadt_name_lower]

        # Neu erstellen
        neue_id = max(s.id for s in self.staedte if s.id is not None) + 1 if self.staedte else 1
        neue_stadt = Stadt(id=neue_id, name=stadt_name.strip())
        
        self.staedte.append(neue_stadt)
        self._stadt_namen_map[stadt_name_lower] = neue_id
        self._stadt_id_map[neue_id] = neue_stadt.name
        
        # Speichern nur, wenn wir nicht gerade migrieren (Migration speichert alles am Ende)
        if not migrieren:
            self._speichern_alle() 
            
        return neue_id
        
    def get_stadtname(self, stadt_id: int) -> str:
        """Gibt den Namen der Stadt basierend auf der ID zurück."""
        return self._stadt_id_map.get(stadt_id, "Unbekannt")

    # --- CRUD METHODEN ---
    
    def finde_nach_id(self, id_gesucht: int) -> Optional[Person]:
        for person in self.daten:
            if person.id == id_gesucht:
                return person
        return None

    def hinzufuegen(self, neuer_eintrag: Dict[str, Any]):
        """Fügt einen Eintrag hinzu. Erwartet Name, Email und den Stadt-Namen."""
        
        if 'stadt' not in neuer_eintrag:
             raise ValueError("Stadtname fehlt.")
             
        stadt_name = neuer_eintrag.pop('stadt')
        stadt_id = self.finde_oder_erstelle_stadt(stadt_name)
        neuer_eintrag['stadt_id'] = stadt_id
        
        try:
            if 'erstellungsdatum' not in neuer_eintrag or neuer_eintrag['erstellungsdatum'] is None:
                 neuer_eintrag['erstellungsdatum'] = datetime.now().replace(microsecond=0)

            person_objekt = PersonCreate(**neuer_eintrag)
            person_objekt_mit_id = Person(**person_objekt.model_dump())
        except ValidationError as e:
            raise ValueError(f"Validierungsfehler beim Hinzufügen: {e}")

        email_neu = person_objekt_mit_id.email.lower()
        if email_neu in self._email_index:
            raise ValueError(f"E-Mail-Adresse '{person_objekt_mit_id.email}' existiert bereits. Eintrag nicht hinzugefügt.")
            
        neue_id = max(p.id for p in self.daten if p.id is not None) + 1 if self.daten else 1
        person_objekt_mit_id.id = neue_id
        
        self.daten.append(person_objekt_mit_id)
        self._email_index.add(email_neu)
        
        self._speichern_alle()

    def aendern(self, id_zum_aendern: int, neue_daten: Dict[str, str]):
        """Ändert existierende Daten eines Eintrags (Update). Erwartet Stadt-Namen."""
        
        person_zu_aendern = self.finde_nach_id(id_zum_aendern)
        if not person_zu_aendern:
            raise LookupError(f"Eintrag mit ID {id_zum_aendern} wurde nicht gefunden.")
            
        if 'stadt' in neue_daten and neue_daten['stadt']:
            stadt_name = neue_daten.pop('stadt')
            stadt_id = self.finde_oder_erstelle_stadt(stadt_name)
            neue_daten['stadt_id'] = stadt_id
        
        try:
            update_data = PersonUpdate(**neue_daten)
        except ValidationError as e:
            raise ValueError(f"Validierungsfehler: {e.errors()}")
        
        aktualisiert = False
        
        if update_data.email is not None and update_data.email != person_zu_aendern.email:
            neue_email_lower = update_data.email.lower()
            if neue_email_lower in self._email_index:
                raise ValueError(f"E-Mail-Adresse '{update_data.email}' existiert bereits bei einem anderen Eintrag.")
            
            self._email_index.discard(person_zu_aendern.email.lower())
            self._email_index.add(neue_email_lower)
            person_zu_aendern.email = update_data.email
            aktualisiert = True
        
        if update_data.name is not None and update_data.name.strip() != "" and update_data.name != person_zu_aendern.name:
            person_zu_aendern.name = update_data.name
            aktualisiert = True
            
        if update_data.stadt_id is not None and update_data.stadt_id != person_zu_aendern.stadt_id:
            person_zu_aendern.stadt_id = update_data.stadt_id
            aktualisiert = True

        if aktualisiert:
            self._speichern_alle()

    def loeschen(self, id_zum_loeschen: int):
        vorherige_laenge = len(self.daten)
        
        person_zum_loeschen = self.finde_nach_id(id_zum_loeschen)
        
        self.daten = [
            person for person in self.daten
            if person.id != id_zum_loeschen
        ]

        geaendert = (vorherige_laenge > len(self.daten))

        if geaendert:
            if person_zum_loeschen:
                self._email_index.discard(person_zum_loeschen.email.lower())
            
            self._speichern_alle()
        else:
            raise LookupError(f"Eintrag mit ID {id_zum_loeschen} wurde nicht gefunden.")
            
    # --- SUCH- UND SORTIER-METHODEN (unverändert) ---
    
    def filter_by_criteria(self, kriterien: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Daten. Gibt Dicts zurück, um den Stadt-Namen hinzuzufügen."""
        
        ergebnisse = self.daten
        
        for key, value in kriterien.items():
            if not value: continue
            
            if key in ['name', 'email']:
                suchwert = str(value).lower()
                ergebnisse = [
                    person for person in ergebnisse 
                    if suchwert in str(getattr(person, key, '')).lower()
                ]
            
            elif key == 'id':
                 try:
                     suchwert = int(value)
                     ergebnisse = [person for person in ergebnisse if person.id == suchwert]
                 except ValueError:
                     pass 
            
        if 'stadt' in kriterien and kriterien['stadt']:
            suchwert_stadt = kriterien['stadt'].lower()
            gefilterte_stadt_ids = {
                id for name, id in self._stadt_namen_map.items() 
                if suchwert_stadt in name
            }
            ergebnisse = [
                person for person in ergebnisse 
                if person.stadt_id in gefilterte_stadt_ids
            ]

        output = []
        for person in ergebnisse:
            d = person.model_dump(mode='json')
            d['stadt'] = self.get_stadtname(person.stadt_id) 
            output.append(d)
        
        return output

    def sortieren(self, daten_liste: List[Any], feld: str, absteigend: bool = False) -> List[Any]:
        if feld not in ['id', 'name', 'email', 'stadt', 'erstellungsdatum', 'stadt_id']:
            raise ValueError(f"Sortierfeld '{feld}' ist ungültig.")
        
        if feld == 'stadt':
            return sorted(
                daten_liste, 
                key=lambda x: self.get_stadtname(x['stadt_id'] if isinstance(x, dict) else x.stadt_id).lower(), 
                reverse=absteigend
            )
        
        return sorted(
            daten_liste, 
            key=lambda x: getattr(x, feld) if isinstance(x, Person) else x.get(feld),
            reverse=absteigend
        )


# ====================================================================
# III. HAUPTPROGRAMM (BENUTZER-INTERFACE) - TKINTER GUI MIT TREEVIEW
# ====================================================================

class DBApp:
    def __init__(self, master, db):
        self.master = master
        self.master.title("Mini-DB Verwaltung (Tkinter GUI)")
        self.db = db
        
        # --- GUI-Variablen ---
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.stadt_var = tk.StringVar() 
        self.id_edit_var = tk.StringVar()
        self.aktive_bearbeitungs_id: Optional[int] = None
        
        # Suchvariablen
        self.such_name_var = tk.StringVar()
        self.such_stadt_var = tk.StringVar()
        self.such_email_var = tk.StringVar()
        
        self.erzeuge_eingabemaske()
        self.erzeuge_steuerungsbuttons()
        self.erzeuge_suchmaske()
        self.erzeuge_anzeigebereich() 
        
        self.update_display(sortier_feld='name') 

    # --- ZENTRALER FEHLER-WRAPPER ---
    def _db_aktion_wrapper(self, aktion: callable, erfolgs_msg: str, **kwargs):
        try:
            aktion(**kwargs)
            messagebox.showinfo("Erfolg", erfolgs_msg)
            self.setze_formular_zurueck()
            self.update_display(sortier_feld='name') 
        except ValidationError as e:
            fehler_detail = "\n".join([f"Feld '{err['loc'][0]}': {err['msg']}" for err in e.errors()])
            messagebox.showerror("Eingabefehler (Pydantic)", fehler_detail)
        except (ValueError, LookupError) as e:
            messagebox.showerror("DB-Fehler", str(e))
        except Exception as e:
            messagebox.showerror("Unbekannter Fehler", f"Ein unbekannter Fehler ist aufgetreten: {e}")

    # --- ERZEUGUNGS-METHODEN (Gekürzt) ---
    def erzeuge_eingabemaske(self):
        self.eingabe_frame = tk.LabelFrame(self.master, text="➕ Neuen Eintrag erstellen", padx=10, pady=10)
        self.eingabe_frame.pack(pady=10)

        tk.Label(self.eingabe_frame, text="Name:").grid(row=0, column=0, sticky="w")
        tk.Entry(self.eingabe_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(self.eingabe_frame, text="E-Mail:").grid(row=1, column=0, sticky="w")
        tk.Entry(self.eingabe_frame, textvariable=self.email_var, width=40).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(self.eingabe_frame, text="Stadt:").grid(row=2, column=0, sticky="w")
        tk.Entry(self.eingabe_frame, textvariable=self.stadt_var, width=40).grid(row=2, column=1, padx=5, pady=2)
        
        self.haupt_aktion_button = tk.Button(self.eingabe_frame, text="➕ Eintrag Hinzufügen (Create)", 
              command=self.handle_create, bg="#4CAF50", fg="white")
        self.haupt_aktion_button.grid(row=3, column=0, columnspan=2, pady=10)

    def erzeuge_steuerungsbuttons(self):
        frame = tk.LabelFrame(self.master, text="✏️ Eintrag bearbeiten / 🗑️ Löschen", padx=10, pady=10)
        frame.pack(pady=5)
        
        tk.Label(frame, text="ID:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.id_edit_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Button(frame, text="Daten laden (Read)", command=self.handle_load_for_update, 
                  bg="#008CBA", fg="white").grid(row=0, column=2, padx=5)

        tk.Button(frame, text="↩️ Formular zurücksetzen", command=self.setze_formular_zurueck, 
                  bg="#555555", fg="white").grid(row=0, column=3, padx=5)
        
        tk.Button(frame, text="🗑️ Löschen (Delete)", command=self.handle_delete, 
                  bg="#f44336", fg="white").grid(row=0, column=4, padx=5)

    def erzeuge_suchmaske(self):
        frame = tk.LabelFrame(self.master, text="🔍 Erweiterte Suche (Teilstringsuche)", padx=10, pady=10)
        frame.pack(pady=5)
        
        tk.Label(frame, text="Name enthält:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.such_name_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(frame, text="Stadt enthält:").grid(row=0, column=2, sticky="w")
        tk.Entry(frame, textvariable=self.such_stadt_var, width=20).grid(row=0, column=3, padx=5, pady=2)
        
        tk.Label(frame, text="E-Mail enthält:").grid(row=1, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.such_email_var, width=20).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Button(frame, text="🔍 Suche starten", command=self.handle_search, 
                  bg="#FFC107", fg="black").grid(row=1, column=3, padx=5, pady=5)
        
        tk.Button(frame, text="Alle Einträge anzeigen", command=lambda: self.update_display(sortier_feld='name')).grid(row=1, column=2, padx=5, pady=5)

    def erzeuge_anzeigebereich(self):
        tk.Label(self.master, text="\nAktuelle Datenbank-Einträge (Klicken Sie auf Spaltenüberschrift zum Sortieren):").pack()
        
        columns = ('id', 'name', 'email', 'stadt', 'erstellungsdatum')
        self.tree = ttk.Treeview(self.master, columns=columns, show='headings', height=10)
        
        self.tree.heading('id', text='ID', command=lambda: self.sortiere_treeview('id'))
        self.tree.heading('name', text='Name', command=lambda: self.sortiere_treeview('name'))
        self.tree.heading('email', text='E-Mail', command=lambda: self.sortiere_treeview('email'))
        self.tree.heading('stadt', text='Stadt', command=lambda: self.sortiere_treeview('stadt'))
        self.tree.heading('erstellungsdatum', text='Erstellt am', command=lambda: self.sortiere_treeview('erstellungsdatum'))

        self.tree.column('id', width=40, anchor='center')
        self.tree.column('name', width=150)
        self.tree.column('email', width=200)
        self.tree.column('stadt', width=120)
        self.tree.column('erstellungsdatum', width=120, anchor='center')

        scrollbar = ttk.Scrollbar(self.master, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', self.on_treeview_select)


    # --- AKTIONEN (CRUD) ---
    def setze_formular_zurueck(self):
        self.name_var.set("")
        self.email_var.set("")
        self.stadt_var.set("")
        self.id_edit_var.set("")
        self.aktive_bearbeitungs_id = None
        
        self.eingabe_frame.config(text="➕ Neuen Eintrag erstellen")
        self.haupt_aktion_button.config(text="➕ Eintrag Hinzufügen (Create)", 
                                         command=self.handle_create, 
                                         bg="#4CAF50")

    def handle_create(self):
        if self.aktive_bearbeitungs_id is not None:
             messagebox.showwarning("Modus", "Bitte speichern Sie zuerst die Bearbeitung ab oder setzen Sie das Formular zurück.")
             return
             
        neuer_eintrag = {
            'name': self.name_var.get(), 
            'email': self.email_var.get(), 
            'stadt': self.stadt_var.get()
        }
        
        self._db_aktion_wrapper(
            aktion=self.db.hinzufuegen,
            erfolgs_msg=f"Eintrag für '{neuer_eintrag['name']}' erfolgreich hinzugefügt.",
            neuer_eintrag=neuer_eintrag
        )

    def on_treeview_select(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, 'values')
            if values:
                self.id_edit_var.set(values[0]) 
                self.handle_load_for_update()   


    def handle_load_for_update(self):
        id_str = self.id_edit_var.get()
        if not id_str:
            messagebox.showwarning("Fehlende ID", "Bitte geben Sie die ID des zu bearbeitenden Eintrags ein.")
            return

        try:
            id_zu_laden = int(id_str)
        except ValueError:
            messagebox.showerror("Fehler", "Die ID muss eine ganze Zahl sein.")
            return

        person = self.db.finde_nach_id(id_zu_laden)
        
        if person:
            self.name_var.set(person.name)
            self.email_var.set(person.email)
            self.stadt_var.set(self.db.get_stadtname(person.stadt_id))
            
            self.aktive_bearbeitungs_id = person.id
            
            self.eingabe_frame.config(text=f"✏️ Eintrag bearbeiten (ID: {person.id})")
            self.haupt_aktion_button.config(text="✅ Änderungen speichern (Update)", 
                                             command=self.handle_update, 
                                             bg="#008CBA") 
        else:
            messagebox.showerror("Fehler", f"Eintrag mit ID {id_zu_laden} nicht gefunden.")
            self.setze_formular_zurueck()

    def handle_update(self):
        if self.aktive_bearbeitungs_id is None:
            messagebox.showwarning("Fehler", "Kein Eintrag zum Speichern geladen.")
            self.setze_formular_zurueck()
            return
            
        neue_daten = {
            'name': self.name_var.get(),
            'email': self.email_var.get(),
            'stadt': self.stadt_var.get() 
        }
        
        self._db_aktion_wrapper(
            aktion=self.db.aendern,
            erfolgs_msg=f"Eintrag mit ID {self.aktive_bearbeitungs_id} erfolgreich aktualisiert.",
            id_zum_aendern=self.aktive_bearbeitungs_id,
            neue_daten=neue_daten
        )

    def handle_delete(self):
        id_str = self.id_edit_var.get()
        
        if not id_str:
            messagebox.showwarning("Fehlende ID", "Bitte geben Sie die ID des zu löschenden Eintrags ein.")
            return

        try:
            id_zum_loeschen = int(id_str)
        except ValueError:
            messagebox.showerror("Fehler", "Die ID muss eine ganze Zahl sein.")
            return

        bestaetigung = messagebox.askyesno(
            "Eintrag löschen", 
            f"Sind Sie sicher, dass Sie den Eintrag mit der ID {id_zum_loeschen} LÖSCHEN möchten?"
        )

        if bestaetigung:
            self._db_aktion_wrapper(
                aktion=self.db.loeschen,
                erfolgs_msg=f"Eintrag mit ID {id_zum_loeschen} erfolgreich gelöscht.",
                id_zum_loeschen=id_zum_loeschen
            )
            
    # --- ANZEIGE / SORTIERUNG ---

    def sortiere_treeview(self, col):
        """Sortiert die Treeview-Daten interaktiv beim Klick auf die Spaltenüberschrift."""
        
        data = []
        for item in self.tree.get_children(''):
            values = self.tree.item(item, 'values')
            data.append({
                'id': int(values[0]),
                'name': values[1],
                'email': values[2],
                'stadt': values[3],
                'erstellungsdatum': values[4],
                'stadt_id': self.db._stadt_namen_map.get(values[3].lower(), -1)
            })

        current_sort = self.tree.heading(col, option="text")
        if current_sort.endswith(" ▼"):
            direction = False # Aufsteigend
            new_text = col.capitalize() + " ▲"
        else:
            direction = True # Absteigend
            new_text = col.capitalize() + " ▼"

        sortierte_daten = self.db.sortieren(data, feld=col, absteigend=direction)

        self.tree.delete(*self.tree.get_children())
        for row in sortierte_daten:
            self.tree.insert('', tk.END, values=(
                row['id'],
                row['name'],
                row['email'],
                row['stadt'],
                row['erstellungsdatum'][:10]
            ))
            
        for c in self.tree['columns']:
            text = self.tree.heading(c, option="text")
            if c != col and ("▲" in text or "▼" in text):
                 self.tree.heading(c, text=c.capitalize())
        self.tree.heading(col, text=new_text)


    def handle_search(self):
        kriterien = {}
        
        if self.such_name_var.get().strip():
            kriterien['name'] = self.such_name_var.get()
        if self.such_stadt_var.get().strip():
            kriterien['stadt'] = self.such_stadt_var.get()
        if self.such_email_var.get().strip():
            kriterien['email'] = self.such_email_var.get()
            
        if not kriterien:
            messagebox.showwarning("Suche", "Bitte geben Sie mindestens ein Suchkriterium ein.")
            return

        try:
            ergebnisse = self.db.filter_by_criteria(kriterien)
            sortierte_ergebnisse = self.db.sortieren(ergebnisse, feld='name')

            self._update_treeview_data(sortierte_ergebnisse)
            
            messagebox.showinfo("Suche erfolgreich", f"{len(ergebnisse)} Einträge gefunden.")
            
        except Exception as e:
            messagebox.showerror("Suchfehler", f"Ein Fehler bei der Suche ist aufgetreten: {e}")

    
    def _update_treeview_data(self, daten: List[Dict]):
        """Interne Methode zum leeren und Befüllen der Treeview."""
        self.tree.delete(*self.tree.get_children())
        
        if not daten:
            return

        for row in daten:
            self.tree.insert('', tk.END, values=(
                row.get('id'),
                row.get('name'),
                row.get('email'),
                row.get('stadt'),
                str(row.get('erstellungsdatum', 'N/A'))[:10]
            ))

    def update_display(self, sortier_feld: str = 'name', absteigend: bool = False):
        """Aktualisiert die Treeview mit allen aktuellen DB-Daten."""
        
        alle_daten_mit_stadtname = []
        for person in self.db.daten:
            d = person.model_dump(mode='json')
            d['stadt'] = self.db.get_stadtname(person.stadt_id)
            alle_daten_mit_stadtname.append(d)
        
        sortierte_daten = self.db.sortieren(alle_daten_mit_stadtname, feld=sortier_feld, absteigend=absteigend)
        
        self._update_treeview_data(sortierte_daten)
        

# ====================================================================
# IV. PROGRAMMSTART
# ====================================================================

if __name__ == "__main__":
    db_objekt = MiniDatenbank(DATEI_NAME, STADT_DATEI_NAME)
    
    root = tk.Tk()
    app = DBApp(root, db_objekt)
    root.mainloop()
