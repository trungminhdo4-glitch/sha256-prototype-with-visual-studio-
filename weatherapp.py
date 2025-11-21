import requests
import json

# Dein OpenWeatherMap API-Schlüssel
API_KEY = "ae1584e27f53bae62043ed38d7873a7a"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"

def get_current_weather(city_name):
    """
    Ruft die aktuellen Wetterdaten für eine gegebene Stadt ab.
    """
    # Parameter für den API-Aufruf
    # 'q' ist der Stadtname, 'appid' ist der Schlüssel, 'units=metric' für Grad Celsius
    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric',  # Temperaturen in Celsius
        'lang': 'de'        # Sprache der Beschreibung auf Deutsch
    }

    try:
        # API-Aufruf durchführen
        response = requests.get(BASE_URL, params=params)
        
        # Sicherstellen, dass der Aufruf erfolgreich war (Status-Code 200)
        response.raise_for_status() 
        
        # JSON-Antwort in ein Python-Wörterbuch umwandeln
        weather_data = response.json()

        # Prüfen, ob die Stadt gefunden wurde
        if weather_data.get("cod") == 404:
            print(f"Fehler: Stadt '{city_name}' wurde nicht gefunden.")
            return

        # --- Daten aus der Antwort extrahieren ---
        main_weather = weather_data['weather'][0]
        main_temp = weather_data['main']
        wind_info = weather_data['wind']
        
        # Wetterbericht ausgeben
        print(f"\n🌍 Aktuelles Wetter in {weather_data['name']}:")
        print("---------------------------------------")
        print(f"🌡️  Temperatur:   {main_temp['temp']:.1f}°C")
        print(f"🔥 Gefühlt wie:  {main_temp['feels_like']:.1f}°C")
        print(f"🌤️  Beschreibung: {main_weather['description'].capitalize()}")
        print(f"💨 Wind:          {wind_info['speed']:.1f} m/s")
        print(f"💧 Luftfeuchte:   {main_temp['humidity']}%")
        print("---------------------------------------")

    except requests.exceptions.HTTPError as err_h:
        # Fängt spezifische HTTP-Fehler ab (z.B. 401 Unauthorized)
        print(f"HTTP-Fehler ist aufgetreten: {err_h}")
    except requests.exceptions.ConnectionError as err_c:
        # Fängt Fehler bei Verbindung zur API ab
        print(f"Verbindungsfehler: {err_c}")
    except requests.exceptions.RequestException as err:
        # Fängt alle anderen Fehler der requests-Bibliothek ab
        print(f"Ein Fehler ist aufgetreten: {err}")
    except Exception as e:
        # Fängt andere allgemeine Fehler (z.B. bei der Datenverarbeitung) ab
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")


# --- Hauptprogramm ---
if __name__ == "__main__":
    # Benutzer zur Eingabe der Stadt auffordern
    city = input("Geben Sie den Namen der Stadt ein, deren Wetter Sie wissen möchten: ")
    
    # Funktion aufrufen
    get_current_weather(city)
