import requests
from dotenv import load_dotenv
import os
load_dotenv()
import pandas as pd

def fetch_games():
    try: 
        api_key = os.getenv("RAWG_API_KEY")       #retrives the key from env
        if not api_key:   # important to check if the key is actually there, otherwise we will get an error when we try to use it.
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
            if not data.get("next"):  #if there is no next page then the loop stops or else we will get an error when we try to access the next page.
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

def transform_games(raw_data):
    cleaned_data = []
    for game in raw_data:
        cleaned_game = {
            "name": game.get("name"),
            "rating": game.get("rating"),
            "released": game.get("released"),
            "genres": ", ".join([genre.get("name")for genre in game.get("genres", [])]),   #we use a list comprehension to extract the genre names and then join them into a single string separated by commas.since its easier to transer to a df.
            "platforms": ", ".join([platform.get("platform", {}).get("name")for platform in game.get("platforms", [])]), # join can turn a list to a string.
            "playtime": game.get("playtime"),
            "ratings_count": game.get("ratings_count"),
        }
        cleaned_data.append(cleaned_game)
    cleaned_df = pd.DataFrame(cleaned_data)
    return cleaned_df

def main():
    raw_data = fetch_games()
    cleaned_data = transform_games(raw_data)

    
main()

