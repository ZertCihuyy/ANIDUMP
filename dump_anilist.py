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
      favorites
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
query ($page: Int, $perPage: Int, $updatedSince: Int) {
  Page (page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
      perPage
    }
    media (type: ANIME, sort: UPDATED_AT_DESC, updatedAt_greater: $updatedSince) {
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
      favorites
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
            
            # Check rate limits (AniList has a 90 per minute limit)
            remaining = int(response.headers.get('x-ratelimit-remaining', 90))
            if remaining <= 5:
                reset_time = int(response.headers.get('x-ratelimit-reset', time.time() + 60))
                sleep_time = max(0, reset_time - int(time.time())) + 1
                logging.info(f"Rate limit almost reached. Sleeping for {sleep_time}s...")
                time.sleep(sleep_time)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429: # Too Many Requests
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
    # Group data by thousands to keep file sizes manageable
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

def main():
    parser = argparse.ArgumentParser(description='Dump AniList Data')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental', 
                        help='Mode of dumping: full (all data) or incremental (recently updated)')
    parser.add_argument('--hours', type=int, default=2, 
                        help='Number of hours to look back for incremental updates')
    args = parser.parse_args()

    base_dir = Path("data/anime")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    page = 1
    has_next_page = True
    
    logging.info(f"Starting Anilist dump in {args.mode} mode...")
    
    query = QUERY_FULL if args.mode == 'full' else QUERY_INCREMENTAL
    variables = {'perPage': 50} # Maximum allowed complexity might restrict this
    
    if args.mode == 'incremental':
        updated_since = int(time.time()) - (args.hours * 3600)
        variables['updatedSince'] = updated_since
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
            
        save_anime_data(anime_list, base_dir)
        total_fetched += len(anime_list)
        
        has_next_page = page_info['hasNextPage']
        page += 1
        
        # Sleep slightly to be gentle on the API
        time.sleep(1)
        
    logging.info(f"Dump complete! Total anime fetched/updated: {total_fetched}")

if __name__ == "__main__":
    main()
