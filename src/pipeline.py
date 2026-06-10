import requests
from dotenv import load_dotenv
import os
load_dotenv()
import pandas as pd
import psycopg
import logging

os.makedirs("logs", exist_ok=True) # creates a folder in the directory called logs if it doesnt exist.

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def fetch_games():
    try: 
        logger.info("Starting data extraction process.")
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
        
        logger.info(f"Retrieved {len(all_games[:50])} games")

        return all_games[:50]

    except Exception as e:
        
        logger.error(f"An error occurred: {e}")
        raise  # we re-raise the exception after logging it so that the error can be handled by the caller or cause the program to exit, rather than silently failing and returning None or an empty list which could lead to further errors down the line when we try to process the data. By re-raising the exception, we ensure that any issues are properly surfaced and can be addressed.

    finally:
        logger.info("Data fetching process completed.")

def transform_games(raw_data):
    logger.info("Starting data transformation process.")
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
    logger.info("Data transformation process completed.")
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

        logger.info("Connected to the database successfully.")

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

        logger.info(f"Created and inserted {len(row_list)} records into the games table.")

    except Exception as e:
        logger.error(f"An error occurred while connecting to the database: {e}")
    
    finally:
        if cur is not None:  #Here we check if the connection and cursor were successfully created before trying to close them.
            cur.close()
        if conn is not None:
            conn.close()

def export_deliverable(cleaned_df):  # This will create the genre summary CSV file.

    report_df = cleaned_df.copy()
    report_df["genres"] = report_df["genres"].str.split(", ") #.str because pandas columns are arrays (Series), and standard Python string methods like .split() do not work on arrays directly. The .str accessor tells pandas to apply the string operation to every individual text item inside the column.
    report_df = report_df.explode("genres") # dataframe.explode() is used to transform a single row containing a list-like structure into multiple rows. Basically 1NF.
    report_df = report_df.groupby("genres").agg(
        game_count=("name","count"),
        avg_rating=("rating","mean"),
        avg_playtime=("playtime","mean"),
    ).reset_index()
    report_df["avg_rating"] = report_df["avg_rating"].round(2)
    report_df["avg_playtime"] = report_df["avg_playtime"].round(2)
    report_df.rename(columns={'genres': 'genre'}, inplace=True)   # this is how to rename a column in pandas, we use the rename method and pass a dictionary where the keys are the old column names and the values are the new column names. In this case, we want to rename the "genres" column to "genre" because after exploding, each row will only have one genre, so it makes more sense to use the singular form.
    report_df.sort_values("avg_rating", ascending=False, inplace=True) #Inplace=True chnages the original dataframe instead of creating a new one, and sort_values is used to sort the dataframe by the "avg_rating" column in descending order (highest rated genres first).
    
    os.makedirs("outputs", exist_ok=True) #creates a folder in the directory called outputs if it doesnt exist.
    
    report_df.to_csv("outputs/genre_summary.csv", index=False) # we set index to false because we don't want to include the index as a column in the CSV file. The index is just a row label and doesn't contain any meaningful data for our report, so we can exclude it from the CSV.

    logger.info("Generated outputs/genre_summary.csv")

def main():
    raw_data = fetch_games()
    cleaned_data = transform_games(raw_data)
    load_data(cleaned_data)
    export_deliverable(cleaned_data)

main()

