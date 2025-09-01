import requests
import logging
import datetime
import sqlite3
import http.client, urllib.parse
import os
from dotenv import load_dotenv

# Ladda variablerna från .env-filen
load_dotenv()

# Skapa en logger-instans för denna modul
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Skapa en fil-handler som loggar meddelanden till 'logfile.log'
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(logging.INFO)

# Skapa en formatter för loggmeddelandena
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Lägg till handlern till logger-instansen
logger.addHandler(file_handler)

# API-URL och koordinater
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete.json"
LATITUDE = 59.879698
LONGITUDE = 17.634381

def get_weather_data():
    """Hämtar väderdata från YR:s API."""
    try:
        logger.info("Försöker hämta väderdata från YR API...")
        response = requests.get(
            API_URL,
            params={'lat': LATITUDE, 'lon': LONGITUDE},
            headers={'User-Agent': 'PythonAppForecastToClothing/1.0'}
        )
        response.raise_for_status()
        logger.info("Väderdata hämtad framgångsrikt.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Fel vid hämtning av väderdata: {e}")
        return None

def process_weather_data(data):
    """
    Bearbetar väderdatan för tidsperioden 08:00-17:00 och genererar klädförslag.
    Returnerar en sträng med rekommendationer.
    """
    if not data or 'timeseries' not in data['properties']:
        logger.warning("Ingen väderdata att bearbeta eller ogiltigt format.")
        return "Kunde inte hämta väderdata."

    recommendations = []
    
    max_temp = -float('inf')
    min_temp = float('inf')
    will_it_rain = False
    
    total_rain_amount = 0
    total_min_rain_amount = 0
    total_max_rain_amount = 0
    
    max_uv_index = 0

    logger.info("Bearbetar väderdata för 08:00-17:00.")

    for timeslot in data['properties']['timeseries']:
        time_str = timeslot['time']
        time_utc = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        if 8 <= time_utc.hour < 17:
            details = timeslot['data'].get('instant', {}).get('details', {})
            details_1h = timeslot['data'].get('next_1_hours', {}).get('details', {})
            
            temp = details.get('air_temperature')
            uv_index = details.get('ultraviolet_index_clear_sky')
            
            rain_amount = details_1h.get('precipitation_amount', 0)
            min_rain_amount = details_1h.get('precipitation_amount_min', 0)
            max_rain_amount = details_1h.get('precipitation_amount_max', 0)
            
            if temp is not None and temp > max_temp:
                max_temp = temp
            if temp is not None and temp < min_temp:
                min_temp = temp
            
            total_rain_amount += rain_amount
            total_min_rain_amount += min_rain_amount
            total_max_rain_amount += max_rain_amount
            
            if rain_amount > 0:
                will_it_rain = True
            
            if uv_index is not None and uv_index > max_uv_index:
                max_uv_index = uv_index
    
    # Generera klädförslag baserat på de sammanställda värdena
    recommendations = []
    
    # Rekommendationer baserade på både max och min
    if max_temp >= 20 and min_temp >= 15:
        recommendations.append(f"Det blir varmt! Klä dig i shorts och t-shirt.")
    elif max_temp >= 20 and min_temp < 15:
        recommendations.append(f"Det blir varmt och svalt. Klä dig i shorts och t-shirt och ta med en tunn jacka.")
    elif max_temp >= 15 and max_temp < 20:
        recommendations.append(f"Ta med en tunn jacka, det blir svalt i skuggan.")
    elif max_temp >= 5 and max_temp < 15:
        recommendations.append(f"Det blir svalt. Ta med dunjacka och mössa.")
    elif max_temp < 5:
        recommendations.append(f"Det blir kallt. Ta varm jacka och överdragsbyxor.")

    # Rekommendationer baserade enbart på min-temp
    if min_temp <= 15 and min_temp > 7:
        recommendations.append("Det blir svalt. Ta med dunjacka och mössa.")
    if min_temp <= 7 and min_temp > 3:
        recommendations.append("Det kan bli kyligt. Ta med dunjacka, tunna vantar och mössa.")
    elif min_temp <= 3 and min_temp > 0:
        recommendations.append("Det kan bli kallt. Ta med varm jacka, överdragsbyxor,varma vantar och mössa.")
    elif min_temp <= 0:
        recommendations.append("Det blir kallt. Ta overall, mössa och dubbla vantar.")

    # Rekommendation för regn
    if will_it_rain:
        recommendations.append(f"Det kan regna under dagen. Ta med regnkläder och stövlar.")
    
    # Sammanfattning
    total_regn = round(total_rain_amount, 1)
    min_total_regn = round(total_min_rain_amount, 1)
    max_total_regn = round(total_max_rain_amount, 1)

    summary = (f"\n\n"
               f"Dagens väderprognos:\n"
               f"Max: {max_temp}°C\n"
               f"Min: {min_temp}°C\n"
               f"UV-index: {max_uv_index}\n"
               f"Nederbörd: {total_regn} mm ({min_total_regn} till {max_total_regn} mm)")

    # Lägger ihop alla rekommendationer i en sträng 
    final_recommendation = "\n".join(recommendations) + summary
    logger.info(f"Genererade rekommendationer: {final_recommendation}")
    return final_recommendation

def save_to_database(recommendation):
    """Sparar dagens klädförslag till en SQLite-databas."""
    try:
        conn = sqlite3.connect('weather_data.db')
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS clothing_recommendations (
                date TEXT PRIMARY KEY,
                recommendation TEXT
            )
        ''')
        
        today = datetime.date.today().isoformat()
        
        c.execute('''
            REPLACE INTO clothing_recommendations (date, recommendation)
            VALUES (?, ?)
        ''', (today, recommendation))
        
        conn.commit()
        conn.close()
        logger.info("Dagens rekommendation sparad i databasen.")
    except sqlite3.Error as e:
        logger.error(f"Fel vid anslutning eller skrivning till databas: {e}")

def send_pushover_notification(message):
    """Skickar ett meddelande via Pushover med hjälp av inbyggda moduler."""
    # Läs nycklarna från miljövariablerna
    APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
    USER_KEY = os.getenv("PUSHOVER_USER_KEY")

    if not APP_TOKEN or not USER_KEY:
        logger.error("Pushover nycklar saknas i .env-filen.")
        return

    try:
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
            urllib.parse.urlencode({
                "token": APP_TOKEN,
                "user": USER_KEY,
                "message": message,
                "title": "Dagens Klädprognos"
            }), { "Content-type": "application/x-www-form-urlencoded" })
        response = conn.getresponse()
        
        if response.status == 200:
            logger.info("Notis skickad framgångsrikt via Pushover.")
        else:
            logger.error(f"Kunde inte skicka notis. Statuskod: {response.status}")
    except Exception as e:
        logger.error(f"Kunde inte skicka notis via Pushover: {e}")

if __name__ == "__main__":
    logger.info("Programmet startas.")
    weather_json = get_weather_data()
    if weather_json:
        recommendation_text = process_weather_data(weather_json)
        save_to_database(recommendation_text)
        send_pushover_notification(recommendation_text)
    logger.info("Programmet avslutas.")