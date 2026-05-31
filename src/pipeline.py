import requests
from dotenv import load_dotenv
import os
load_dotenv()

def fetch_games():
    try: 
        api_key = os.getenv("RAWG_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Please set the RAWG_API_KEY environment variable.")
        base_url = "https://api.rawg.io/api/games"
        params = {
            "key": api_key
        }
        response = requests.get(base_url, params = params)
        response.raise_for_status()  #automatically throws an error if your HTTP request failed.
        data = response.json()
        all_games = data.get("results", [])
        while len(all_games) < 50:
            if not data.get("next"):
                break
            response = requests.get(data.get("next"))
            response.raise_for_status()
            data = response.json()
            all_games.extend(data.get("results", []))

        return all_games[:50]

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        print("Data fetching process completed.")

def main():
    raw_games = fetch_games()
    print(len(raw_games))
    
main()

