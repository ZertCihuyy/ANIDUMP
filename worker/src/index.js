const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/ZertCihuyy/ANIDUMP/main/data/raw';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // Redirect root to GitHub repository
    if (path === '/' || path === '') {
      return Response.redirect('https://github.com/ZertCihuyy/ANIDUMP/', 301);
    }

    // CORS Headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,HEAD,POST,OPTIONS',
      'Access-Control-Max-Age': '86400',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Parse query params
    const limit = parseInt(url.searchParams.get('limit')) || 20;
    const offset = parseInt(url.searchParams.get('offset')) || 0;
    const search = url.searchParams.get('q') || url.searchParams.get('search');
    const genre = url.searchParams.get('genre');

    // Helper to fetch JSON from GitHub directly to stay perfectly in sync
    async function fetchGitHubJSON(subpath) {
      const ghResponse = await fetch(`${GITHUB_RAW_BASE}${subpath}`, {
        headers: { 'User-Agent': 'ANIDUMP-Worker/1.0' }
      });
      
      if (!ghResponse.ok) return null;
      return await ghResponse.json();
    }

    // Helper to filter and paginate
    function processItems(items) {
      let filtered = items;
      
      if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(a => {
          const t = a.title || {};
          return (t.romaji && t.romaji.toLowerCase().includes(q)) ||
                 (t.english && t.english.toLowerCase().includes(q)) ||
                 (t.native && t.native.toLowerCase().includes(q)) ||
                 (a.synonyms && a.synonyms.some(s => s.toLowerCase().includes(q)));
        });
      }
      
      if (genre) {
        const g = genre.toLowerCase();
        filtered = filtered.filter(a => a.genres && a.genres.some(x => x.toLowerCase() === g));
      }
      
      const paginated = filtered.slice(offset, offset + limit);
      return {
        total: filtered.length,
        limit,
        offset,
        data: paginated
      };
    }

    function jsonResponse(data, status = 200) {
      return new Response(JSON.stringify(data), {
        status,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    try {
      if (path === '/anime') {
        const data = await fetchGitHubJSON('/lists/all_anime.json');
        if (!data) return jsonResponse({error: 'Data not found'}, 404);
        
        const items = Array.isArray(data) ? data : Object.values(data);
        return jsonResponse(processItems(items));
      }
      
      if (path === '/top') {
        const items = await fetchGitHubJSON('/lists/top_anime.json');
        return jsonResponse(processItems(items || []));
      }
      
      if (path === '/popular') {
        const items = await fetchGitHubJSON('/lists/popular_anime.json');
        return jsonResponse(processItems(items || []));
      }
      
      if (path === '/ongoing' || path === '/schedule') {
        const items = await fetchGitHubJSON('/lists/ongoing_anime.json');
        return jsonResponse(processItems(items || []));
      }
      
      if (path === '/season') {
        const items = await fetchGitHubJSON('/lists/season_now.json');
        return jsonResponse(processItems(items || []));
      }
      
      if (path === '/upcoming') {
        const items = await fetchGitHubJSON('/lists/upcoming_anime.json');
        return jsonResponse(processItems(items || []));
      }
      
      if (path === '/movies' || path === '/movie') {
        const items = await fetchGitHubJSON('/lists/top_movies.json');
        return jsonResponse(processItems(items || []));
      }
      
      // Get specific anime by ID (e.g. /anime/123)
      const match = path.match(/^\/anime\/(\d+)$/);
      if (match) {
        const id = parseInt(match[1]);
        const groupSize = 1000;
        const groupId = Math.floor(id / groupSize) * groupSize;
        const fileName = `/anime/anime_${groupId}-${groupId + groupSize - 1}.json`;
        
        const chunkData = await fetchGitHubJSON(fileName);
        if (chunkData && chunkData[id]) {
          return jsonResponse(chunkData[id]);
        }
        return jsonResponse({error: "Anime not found"}, 404);
      }
      
      return jsonResponse({
        error: "Endpoint not found", 
        endpoints: ["/anime", "/anime/:id", "/top", "/popular", "/ongoing", "/season", "/schedule"]
      }, 404);

    } catch (err) {
      return jsonResponse({error: err.message}, 500);
    }
  }
};
