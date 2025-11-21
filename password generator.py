import string

# Die alte Funktion wird durch die neue, korrigierte Funktion ersetzt
def generate_password(min_length, numbers=True, special_chars=True):
    # 1. Zeichen-Sets und Muss-Listen definieren
    letters = string.ascii_letters
    digits = string.digits
    specials = string.punctuation
    
    characters = letters
    must_include = [letters] # Garantiere immer Buchstaben (oder zumindest eine Kategorie)
    
    if numbers:
        characters += digits
        must_include.append(digits)
    if special_chars:
        characters += specials
        must_include.append(specials)
        
    pwd = []
    
    # 2. Phase 1: Mindestens ein Zeichen jedes erforderlichen Typs hinzufügen
    for char_set in must_include:
        pwd.append(random.choice(char_set))
        
    # 3. Phase 2: Restliche Zeichen (bis min_length) zufällig hinzufügen
    # Der Pool der Zeichen wird aus den aktivierten Sets gebildet
    full_pool = characters
    while len(pwd) < min_length:
        pwd.append(random.choice(full_pool))
        
    # 4. Mischen, um die Reihenfolge zu randomisieren
    random.shuffle(pwd)
    
    # 5. Rückgabe als String
    return "".join(pwd)

# --- Beispiel Nutzung (bleibt gleich!) ---
# Alle alten Aufrufe funktionieren nun mit der verbesserten Logik
password_len_10 = generate_password(10)
print(f"Password (Korrigierte Logik, Länge 10): {password_len_10} (Länge: {len(password_len_10)})")

password_simple = generate_password(8, numbers=False, special_chars=False)
print(f"Password (Korrigierte Logik, nur Buchstaben): {password_simple} (Länge: {len(password_simple)})")
