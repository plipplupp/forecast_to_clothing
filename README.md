# Weather Data to Clothing Recommendation

This is a Python program that fetches weather data from YR's API (`api.met.no`), processes the forecast to generate clothing suggestions, and then sends a notification with the recommendation to your phone via **Pushover**.  
The daily recommendation is also stored locally in an SQLite database for future reference and history.

## Features

- **Fetch weather data:** Retrieves weather forecast for specific coordinates (Uppsala) from `api.met.no`.
- **Generate recommendations:** Based on maximum and minimum temperatures, precipitation forecast, and UV index, the program creates smart clothing suggestions for a specific time period (08:00–17:00).
- **Notifications:** Sends the daily clothing recommendation as a push notification to your phone via Pushover.
- **Database:** Saves the daily recommendation in a local SQLite database (`weather_data.db`) for historical data and logging.
- **Automated execution:** The program can be set up to run automatically every morning via a `.bat` file and Windows Task Scheduler.

## Installation and Setup

Follow these steps to get started.

### 1. Create a virtual environment

```powershell
python -m venv venv
```

Then activate the virtual environment:

```powershell
venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Pushover API keys

This program uses Pushover to send notifications to your phone.  
You need to obtain an **application token** and a **user key** from Pushover.

Create a file named `.env` in your project folder and add your keys in the following format:

```env
PUSHOVER_APP_TOKEN="your_app_token"
PUSHOVER_USER_KEY="your_user_key"
```

### 4. Create a batch file

The program runs via `run_script.bat`.  
Make sure the paths in the batch file match your Python installation and virtual environment.

Example `run_script.bat`:

```bat
@echo off
"C:\Users\Computer\Your\Path\forecast_to_clothing\venv\Scripts\python.exe"
"C:\Users\Computer\Your\Path\forecast_to_clothing\main.py"
```

This path should reflect your folder structure.

---

## Usage

### Run manually

Make sure your virtual environment is activated, then run:

```powershell
python main.py
```

### Automate with Task Scheduler

To run the program automatically every morning, set up a scheduled task in Windows Task Scheduler:

1. Open **Task Scheduler**.  
2. Create a new basic task (*Create Basic Task*).  
3. Choose a suitable name and trigger (e.g., every day at 07:00).  
4. As the **Action**, select *Start a program*.  
5. In the **Program/script** field, enter the path to your `run_script.bat` file:  

   ```powershell
   C:\Users\Computer\Your\Path\forecast_to_clothing\run_script.bat
   ```

6. In the **Start in (optional)** field, enter the path to your project folder (important so the program can find its files such as logs and database):  

   ```powershell
   C:\Users\Computer\Your\Path\forecast_to_clothing
   ```
