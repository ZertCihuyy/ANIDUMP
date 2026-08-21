import requests
import json
import time
import os
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = 'https://graphql.anilist.co'

QUERY_FULL = '''
query ($page: Int, $perPage: Int) {
  Page (page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
      perPage
    }
    media (type: ANIME, sort: ID) {
      id
      idMal
      title { romaji english native }
      type
      format
      status
      description
      episodes
      duration
      season
      seasonYear
      startDate { year month day }
      endDate { year month day }
      coverImage { extraLarge large medium color }
      bannerImage
      genres
      synonyms
      averageScore
      meanScore
      popularity
      trending
      favourites
      isAdult
      countryOfOrigin
      source
      trailer { id site thumbnail }
      externalLinks { url site type }
      streamingEpisodes { title thumbnail url site }
      nextAiringEpisode { airingAt timeUntilAiring episode }
      relations { edges { relationType node { id title { romaji english } type } } }
      tags { id name rank isMediaSpoiler }
      studios { edges { isMain node { id name } } }
      characters(sort: [ROLE, RELEVANCE, ID], page: 1, perPage: 10) {
        edges {
          role
          node { id name { full native } }
          voiceActors(language: JAPANESE, sort: [RELEVANCE, ID]) {
            id
            name { full native }
          }
        }
      }
      updatedAt
    }
  }
}
'''

QUERY_INCREMENTAL = '''
query ($page: Int, $perPage: Int) {
  Page (page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
      perPage
    }
    media (type: ANIME, sort: UPDATED_AT_DESC) {
      id
      idMal
      title { romaji english native }
      type
      format
      status
      description
      episodes
      duration
      season
      seasonYear
      startDate { year month day }
      endDate { year month day }
      coverImage { extraLarge large medium color }
      bannerImage
      genres
      synonyms
      averageScore
      meanScore
      popularity
      trending
      favourites
      isAdult
      countryOfOrigin
      source
      trailer { id site thumbnail }
      externalLinks { url site type }
      streamingEpisodes { title thumbnail url site }
      nextAiringEpisode { airingAt timeUntilAiring episode }
      relations { edges { relationType node { id title { romaji english } type } } }
      tags { id name rank isMediaSpoiler }
      studios { edges { isMain node { id name } } }
      characters(sort: [ROLE, RELEVANCE, ID], page: 1, perPage: 10) {
        edges {
          role
          node { id name { full native } }
          voiceActors(language: JAPANESE, sort: [RELEVANCE, ID]) {
            id
            name { full native }
          }
        }
      }
      updatedAt
    }
  }
}
'''

def fetch_page(query, variables):
    while True:
        try:
            response = requests.post(API_URL, json={'query': query, 'variables': variables})
            
            remaining = int(response.headers.get('x-ratelimit-remaining', 90))
            if remaining <= 5:
                reset_time = int(response.headers.get('x-ratelimit-reset', time.time() + 60))
                sleep_time = max(0, reset_time - int(time.time())) + 1
                logging.info(f"Rate limit almost reached. Sleeping for {sleep_time}s...")
                time.sleep(sleep_time)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logging.warning(f"429 Too Many Requests. Sleeping for {retry_after}s...")
                time.sleep(retry_after)
            else:
                logging.error(f"Error {response.status_code}: {response.text}")
                logging.info("Sleeping 10s before retry...")
                time.sleep(10)
        except Exception as e:
            logging.error(f"Exception: {e}")
            time.sleep(5)

def save_anime_data(anime_list, base_dir):
    group_size = 1000
    groups_updated = {}
    
    for anime in anime_list:
        anime_id = anime['id']
        group_id = (anime_id // group_size) * group_size
        
        if group_id not in groups_updated:
            groups_updated[group_id] = {}
            group_file = base_dir / f"anime_{group_id}-{group_id + group_size - 1}.json"
            if group_file.exists():
                with open(group_file, 'r', encoding='utf-8') as f:
                    try:
                        groups_updated[group_id] = json.load(f)
                    except json.JSONDecodeError:
                        pass
        
        groups_updated[group_id][str(anime_id)] = anime

    for group_id, data in groups_updated.items():
        group_file = base_dir / f"anime_{group_id}-{group_id + group_size - 1}.json"
        with open(group_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def generate_indexes(base_dir):
    logging.info("Generating index and feature files...")
    all_anime = {}
    
    # Read all chunked JSON files
    for file in base_dir.glob("anime_*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_anime.update(data)
        except Exception as e:
            logging.error(f"Failed to read {file}: {e}")
            
    if not all_anime:
        logging.info("No data found to generate indexes.")
        return

    # Create lists directory at data/raw/lists
    lists_dir = base_dir.parent / "lists"
    lists_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Full Raw Data (all_anime.json) - Minified to save space
    logging.info("Saving all_anime.json (minified)...")
    with open(lists_dir / 'all_anime.json', 'w', encoding='utf-8') as f:
        # Using separators=(',', ':') removes whitespace to keep file size minimal (avoiding GitHub 100MB limit)
        json.dump(all_anime, f, ensure_ascii=False, separators=(',', ':'))
        
    anime_list = list(all_anime.values())
    
    # 2. Top Anime by Score
    logging.info("Generating top_anime.json...")
    top_anime = sorted([a for a in anime_list if a.get('averageScore')], key=lambda x: x['averageScore'], reverse=True)[:500]
    with open(lists_dir / 'top_anime.json', 'w', encoding='utf-8') as f:
        json.dump(top_anime, f, ensure_ascii=False, indent=2)
        
    # 3. Most Popular Anime
    logging.info("Generating popular_anime.json...")
    popular = sorted([a for a in anime_list if a.get('popularity')], key=lambda x: x['popularity'], reverse=True)[:500]
    with open(lists_dir / 'popular_anime.json', 'w', encoding='utf-8') as f:
        json.dump(popular, f, ensure_ascii=False, indent=2)
        
    # 4. Ongoing / Releasing Anime
    logging.info("Generating ongoing_anime.json...")
    ongoing = [a for a in anime_list if a.get('status') == 'RELEASING']
    with open(lists_dir / 'ongoing_anime.json', 'w', encoding='utf-8') as f:
        json.dump(ongoing, f, ensure_ascii=False, indent=2)
        
    # 5. Current Season (Quick heuristic based on current month)
    logging.info("Generating season_now.json...")
    import datetime
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    if month in (1, 2, 3): season = 'WINTER'
    elif month in (4, 5, 6): season = 'SPRING'
    elif month in (7, 8, 9): season = 'SUMMER'
    else: season = 'FALL'
    
    season_anime = [a for a in anime_list if a.get('season') == season and a.get('seasonYear') == year]
    with open(lists_dir / 'season_now.json', 'w', encoding='utf-8') as f:
        json.dump(season_anime, f, ensure_ascii=False, indent=2)

    logging.info("Indexes successfully generated!")

def main():
    parser = argparse.ArgumentParser(description='Dump AniList Data')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental', 
                        help='Mode of dumping: full (all data) or incremental (recently updated)')
    parser.add_argument('--hours', type=int, default=2, 
                        help='Number of hours to look back for incremental updates')
    args = parser.parse_args()

    # Determine script location to properly route paths
    script_dir = Path(__file__).parent.resolve()
    # Save into data/raw/anime which is in the parent directory of scripts/
    base_dir = script_dir.parent / "data" / "raw" / "anime"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    page = 1
    has_next_page = True
    
    logging.info(f"Starting Anilist dump in {args.mode} mode. Saving to {base_dir}")
    
    query = QUERY_FULL if args.mode == 'full' else QUERY_INCREMENTAL
    variables = {'perPage': 50}
    
    updated_since = 0
    if args.mode == 'incremental':
        updated_since = int(time.time()) - (args.hours * 3600)
        logging.info(f"Fetching anime updated since {updated_since}")

    total_fetched = 0
    while has_next_page:
        logging.info(f"Fetching page {page}...")
        variables['page'] = page
        
        data = fetch_page(query, variables)
        
        if not data or 'data' not in data or not data['data']['Page']:
            logging.error("Failed to fetch data or invalid format.")
            break
            
        page_info = data['data']['Page']['pageInfo']
        anime_list = data['data']['Page']['media']
        
        if not anime_list:
            logging.info("No more anime found.")
            break
            
        # If incremental, filter out anime older than our timestamp and stop pagination if necessary
        if args.mode == 'incremental':
            filtered_anime_list = []
            reached_old_data = False
            for anime in anime_list:
                anime_updated = anime.get('updatedAt', 0)
                if anime_updated >= updated_since:
                    filtered_anime_list.append(anime)
                else:
                    reached_old_data = True
            
            if filtered_anime_list:
                save_anime_data(filtered_anime_list, base_dir)
                total_fetched += len(filtered_anime_list)
            
            if reached_old_data:
                logging.info("Reached data older than the update threshold. Stopping.")
                break
        else:
            save_anime_data(anime_list, base_dir)
            total_fetched += len(anime_list)
        
        has_next_page = page_info['hasNextPage']
        page += 1
        time.sleep(1)
        
    logging.info(f"Dump complete! Total anime fetched/updated: {total_fetched}")
    
    # Generate the requested index lists
    generate_indexes(base_dir)

if __name__ == "__main__":
    main()
