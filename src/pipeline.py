import requests
from dotenv import load_dotenv
import os
load_dotenv()
import pandas as pd
import psycopg

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
            "rawg_id": game.get("id"),
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

def load_data(cleaned_df):
    conn = None  # We initialize the connection and cursor to None so that we can check if they were successfully created before trying to close them in the finally block. This helps prevent errors if the connection or cursor was never established.
    cur = None  
    try:
        conn = psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS games (
                rawg_id INTEGER PRIMARY KEY,
                name TEXT,
                rating FLOAT,
                released DATE,
                genres TEXT,
                platforms TEXT,
                playtime INTEGER,
                ratings_count INTEGER
                );
            '''
        )

        row_list = list(cleaned_df.itertuples(index=False)) #list of tuples, index false means we don't want to include the index as a column in the tuples. This is important because when we insert the data into the database, we only want to insert the actual data columns and not the index.
        
        cur.executemany(
            '''
            INSERT INTO games (rawg_id, name, rating, released, genres, platforms, playtime, ratings_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (rawg_id) DO NOTHING;
            ''',
            row_list
        )

        conn.commit()   #commits the transaction to the database, which means that the changes we made (creating the table) are saved to the database. If we didn't call commit(), the changes would not be saved and would be lost when the connection is closed.

    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
    
    finally:
        if conn is not None and cur is not None:    #Here we check if the connection and cursor were successfully created before trying to close them.
            cur.close()
            conn.close()



def main():
    raw_data = fetch_games()
    cleaned_data = transform_games(raw_data)
    load_data(cleaned_data)

main()

