# ANIDUMP / ANIDB.MY.ID 🌸

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ANIDUMP** is a fully automated, comprehensive offline database of Anime fetched directly from AniList via GitHub Actions. It is updated **every hour** and contains everything from basic information to full synopses, characters, voice actors, external streaming links, and episode schedules!

This repository serves as both the **Database** (raw JSONs) and the **API Backend** (via a provided Cloudflare Worker).

## 🚀 Features
- **Hourly Auto-Updates**: Incremental fetching ensures the data is always up to date without abusing APIs.
- **Full Anime Data**: Titles (Romaji, English, Native, Synonyms), synopses, genres, tags, trailer IDs, characters, voice actors (Japanese), relations, and streaming episodes.
- **Categorized Lists**: Ready-to-use indexes such as Top 500, Most Popular, Currently Airing (Ongoing), and Current Season.
- **Serverless API**: Includes a Cloudflare Worker script that wraps the raw JSONs into a powerful, searchable REST API.

---

## 📂 Repository Structure

- `data/raw/anime/`: The core database. Contains chunked JSON files (e.g., `anime_0-999.json`) to keep Git diffs minimal during hourly updates.
- `data/raw/lists/`: Ready-to-use aggregated lists (`all_anime.json`, `top_anime.json`, `popular_anime.json`, `ongoing_anime.json`, `season_now.json`).
- `scripts/`: Python scripts used by GitHub Actions to pull data from AniList.
- `worker/`: The Cloudflare Worker code to turn this repo into a real-time REST API.

---

## 🌐 API Endpoints (Cloudflare Worker)

If you deploy the included Cloudflare Worker (e.g., to `anidb.my.id`), you can access the data using the following endpoints. 

*All endpoints support standard pagination and filtering.*

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Redirects to this GitHub repository. |
| `/anime` | `GET` | Returns all anime. Supports search and pagination. |
| `/anime/:id` | `GET` | Fetch full details for a specific AniList ID in O(1) time. |
| `/top` | `GET` | Returns the Top 500 anime based on average score. |
| `/popular` | `GET` | Returns the Most Popular anime. |
| `/ongoing` | `GET` | Returns currently releasing/airing anime (Schedules). |
| `/schedule` | `GET` | Alias for `/ongoing`. |
| `/season` | `GET` | Returns anime airing in the current season. |
| `/upcoming` | `GET` | Returns upcoming/unreleased anime. |
| `/movies` | `GET` | Returns the Top 500 Anime Movies based on average score. |

### Query Parameters
You can append these parameters to any array endpoint (like `/anime`, `/top`, `/ongoing`):
- `?limit=10` (Default 20): Number of results to return.
- `?offset=20` (Default 0): Number of results to skip (for pagination).
- `?q=naruto` or `?search=naruto`: Search anime by title (Romaji, English, Native, or Synonyms).
- `?genre=action`: Filter results by a specific genre.

**Example Request:**
`https://anidb.my.id/anime?q=attack&genre=action&limit=5&offset=0`

---

## 🛠️ Worker Setup & Deployment (Node.js)

To deploy the API worker to your own Cloudflare account (or custom domain), follow these steps:

### Prerequisites
- [Node.js](https://nodejs.org/) installed on your computer.
- A [Cloudflare](https://dash.cloudflare.com) account.

### Deployment Steps
1. **Clone this repository**
   ```bash
   git clone https://github.com/ZertCihuyy/ANIDUMP.git
   cd ANIDUMP/worker
   ```
2. **Install dependencies**
   ```bash
   npm install
   ```
3. **Login to Cloudflare**
   ```bash
   npx wrangler login
   ```
4. **Test locally (Optional)**
   ```bash
   npm run dev
   ```
5. **Deploy to Cloudflare**
   ```bash
   npm run deploy
   ```
Once deployed, you can assign your custom domain (e.g., `anidb.my.id`) to the worker in your Cloudflare Dashboard!

---

## 🤝 Contributing
Contributions are highly welcome! Since this is an open-source project aimed at helping developers build anime apps without worrying about scraping or rate-limiting:
- Found a bug in the Python scraper? Open an Issue or submit a Pull Request!
- Want to add new filtering features to the CF Worker? We'd love to see it.
- Feel free to fork and modify it for your own needs.

## 📄 License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.
*Data is sourced from AniList. Please respect their API guidelines if modifying the scraper.*
