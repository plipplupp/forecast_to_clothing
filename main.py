import requests
import logging
import datetime
import sqlite3
import http.client, urllib.parse
import os
from dotenv import load_dotenv
import configparser
import json

# --- Setup and Configuration ---
# Loads variables from the .env file and sets up the logger for output to a file.
load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# YR API endpoint
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete.json"

def load_config():
    """
    Loads configuration settings from config.ini.
    Provides default values if the file or sections are missing.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Set default values for weather and clothing recommendation sections
    if 'weather' not in config:
        config['weather'] = {
            'latitude': '59.879698',
            'longitude': '17.634381'
        }
    if 'clothing_recommendations' not in config:
        config['clothing_recommendations'] = {
            'check_forecast_at_night': 'false',
            'start_hour': '8',
            'end_hour': '17'
        }
        
    return config

# --- Core Program Logic ---
def get_weather_data(latitude, longitude):
    """
    Fetches weather data from YR's API for the specified coordinates.
    The 'User-Agent' header is required by the API's usage policy.
    """
    try:
        logger.info("Attempting to fetch weather data from YR API...")
        response = requests.get(
            API_URL,
            params={'lat': latitude, 'lon': longitude},
            headers={'User-Agent': 'PythonAppForecastToClothing/1.0'}
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        logger.info("Weather data fetched successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return None

def process_weather_data(data, start_hour, end_hour):
    """
    Processes the weather data to find max/min temperatures, rain, UV index,
    and checks for conditions that cause dew point warnings.
    Generates a string with clothing recommendations based on these values.
    """
    if not data or 'timeseries' not in data['properties']:
        logger.warning("No weather data to process or invalid format.")
        return "Kunde inte hämta väderdata."

    recommendations = []
    
    max_temp = -float('inf')
    min_temp = float('inf')
    will_it_rain = False
    
    total_rain_amount = 0
    total_min_rain_amount = 0
    total_max_rain_amount = 0
    
    max_uv_index = 0
    has_dew_point_warning = False

    logger.info(f"Processing weather data for {start_hour}:00-{end_hour}:00.")
    logger.info(f"Antal tidsstämplar i datan: {len(data['properties']['timeseries'])}")
    
    # Loop through all hourly forecast data points
    for timeslot in data['properties']['timeseries']:
        time_str = timeslot['time']
        time_utc = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))

        # Process dew point data for the morning hours regardless of the main time period
        if 6 <= time_utc.hour < 9:
            details = timeslot['data'].get('instant', {}).get('details', {})
            temp_at_dawn = details.get('air_temperature')
            dew_point_at_dawn = details.get('dew_point_temperature')
            
            if temp_at_dawn is not None and dew_point_at_dawn is not None:
                if temp_at_dawn <= dew_point_at_dawn + 1.5:
                    has_dew_point_warning = True

        # Only process data within the specified time range for recommendations
        if start_hour <= time_utc.hour < end_hour:
            details = timeslot['data'].get('instant', {}).get('details', {})
            details_1h = timeslot['data'].get('next_1_hours', {}).get('details', {})
            
            temp = details.get('air_temperature')
            uv_index = details.get('ultraviolet_index_clear_sky')
            rain_amount = details_1h.get('precipitation_amount', 0)
            min_rain_amount = details_1h.get('precipitation_amount_min', 0)
            max_rain_amount = details_1h.get('precipitation_amount_max', 0)
            
            if temp is not None:
                if temp > max_temp:
                    max_temp = temp
                if temp < min_temp:
                    min_temp = temp
            
            total_rain_amount += rain_amount
            total_min_rain_amount += min_rain_amount
            total_max_rain_amount += max_rain_amount
            
            if rain_amount > 0:
                will_it_rain = True
            if uv_index is not None and uv_index > max_uv_index:
                max_uv_index = uv_index
    
    # Build recommendations based on collected data
    if max_temp >= 20 and min_temp >= 15:
        recommendations.append(f"• Det blir varmt! Klä dig i shorts och t-shirt.")
    elif max_temp >= 20 and min_temp < 15:
        recommendations.append(f"• Det blir varmt och svalt. Klä dig i shorts och t-shirt och ta med en tunn jacka.")
    elif max_temp >= 15 and max_temp < 20:
        recommendations.append(f"• Ta med en tunn jacka, det blir svalt i skuggan.")
    elif max_temp >= 5 and max_temp < 15:
        recommendations.append(f"• Det blir svalt. Ta med dunjacka och mössa.")
    elif max_temp < 5:
        recommendations.append(f"• Det blir kallt. Ta varm jacka och överdragsbyxor.")

    if min_temp <= 15 and min_temp > 7:
        recommendations.append("• Det blir svalt. Ta med dunjacka och mössa.")
    if min_temp <= 7 and min_temp > 3:
        recommendations.append("• Det kan bli kyligt. Ta med dunjacka, tunna vantar och mössa.")
    elif min_temp <= 3 and min_temp > 0:
        recommendations.append("• Det kan bli kallt. Ta med varm jacka, överdragsbyxor,varma vantar och mössa.")
    elif min_temp <= 0:
        recommendations.append("• Det blir kallt. Ta overall, mössa och dubbla vantar.")

    if has_dew_point_warning:
        recommendations.append("• Det är fuktigt i gräset på morgonen. Ta med stövlar och byxor som tål fukt.")
    
    if max_uv_index > 3:
        recommendations.append(f"• Använd solskydd!")
      
    if total_min_rain_amount > 0:
        will_it_rain = True

    if will_it_rain:
        recommendations.append(f"• Det kan regna under dagen. Ta med regnkläder och stövlar.")
    
    total_regn = round(total_rain_amount, 1)
    min_total_regn = round(total_min_rain_amount, 1)
    max_total_regn = round(total_max_rain_amount, 1)

    summary = (f"\n\n"
               f"Dagens väderprognos:\n"
               f"Max: {max_temp}°C\n"
               f"Min: {min_temp}°C\n"
               f"UV-index: {max_uv_index}\n"
               f"Nederbörd: {total_regn} mm ({min_total_regn} till {max_total_regn} mm)")

    final_recommendation = "\n".join(recommendations) + summary
    logger.info(f"Generated recommendations: {final_recommendation}")
    logger.info(f"Antal tidsstämplar i datan: {len(data['properties']['timeseries'])}")
    return final_recommendation

# --- Data Handling and Notifications ---
def save_to_database(recommendation):
    """Saves today's clothing suggestion to a SQLite database."""
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
        logger.info("Today's recommendation saved to the database.")
    except sqlite3.Error as e:
        logger.error(f"Error connecting to or writing to the database: {e}")

def send_pushover_notification(message):
    """Sends a message via Pushover using built-in modules."""
    APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
    USER_KEY = os.getenv("PUSHOVER_USER_KEY")

    if not APP_TOKEN or not USER_KEY:
        logger.error("Pushover keys are missing from the .env file.")
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
            logger.info("Notification sent successfully via Pushover.")
        else:
            logger.error(f"Could not send notification. Status code: {response.status}")
    except Exception as e:
        logger.error(f"Could not send notification via Pushover: {e}")

# --- Main Program Execution ---
if __name__ == "__main__":
    logger.info("Program started.")
    
    # Load configuration settings from the config.ini file
    config = load_config()
    
    # Retrieve values from the configuration
    LATITUDE = config['weather'].getfloat('latitude')
    LONGITUDE = config['weather'].getfloat('longitude')
    START_HOUR = config['clothing_recommendations'].getint('start_hour')
    END_HOUR = config['clothing_recommendations'].getint('end_hour')
    
    # Fetch weather data and process it
    weather_json = get_weather_data(LATITUDE, LONGITUDE)
    
    # # Prints raw data
    # print("--- Rådata från YR-API:et (endast de första 2000 tecknen för att spara utrymme, ändar för att se mer) ---")
    # print(json.dumps(weather_json, indent=2)[:200000])
    # print("...")
    # print("----------------------------------------------------------------------------------\n")
    
    if weather_json:
        recommendation_text = process_weather_data(weather_json, START_HOUR, END_HOUR)
        save_to_database(recommendation_text)
        send_pushover_notification(recommendation_text)
    
    logger.info("Program finished.")