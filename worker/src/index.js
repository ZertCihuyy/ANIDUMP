const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/ZertCihuyy/ANIDUMP/main/data/raw';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // CORS Headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,HEAD,POST,OPTIONS',
      'Access-Control-Max-Age': '86400',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Redirect root to GitHub repository
    if (path === '/' || path === '') {
      return Response.redirect('https://github.com/ZertCihuyy/ANIDUMP/', 301);
    }

    // Parse query params
    const limit = parseInt(url.searchParams.get('limit')) || 20;
    let offset = parseInt(url.searchParams.get('offset')) || 0;
    
    // Support ?page=1 as an alternative to offset
    const pageParams = parseInt(url.searchParams.get('page'));
    if (pageParams && pageParams > 0) {
      offset = (pageParams - 1) * limit;
    }

    const search = url.searchParams.get('q') || url.searchParams.get('search');
    const genre = url.searchParams.get('genre');
    const sort = url.searchParams.get('sort');
    const statusFilter = url.searchParams.get('status');
    const yearFilter = parseInt(url.searchParams.get('year'));
    const studioFilter = url.searchParams.get('studio');

    // Helper to fetch JSON from GitHub directly to stay perfectly in sync
    async function fetchGitHubJSON(subpath) {
      const ghResponse = await fetch(`${GITHUB_RAW_BASE}${subpath}`, {
        headers: { 'User-Agent': 'ANIDUMP-Worker/1.0' }
      });
      
      if (!ghResponse.ok) return null;
      return await ghResponse.json();
    }

    // Helper to filter, sort and paginate
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
        const genresList = genre.toLowerCase().split(',').map(g => g.trim());
        filtered = filtered.filter(a => {
          if (!a.genres) return false;
          const animeGenres = a.genres.map(g => g.toLowerCase());
          return genresList.every(g => animeGenres.includes(g));
        });
      }

      const tagsParam = url.searchParams.get('tag') || url.searchParams.get('tags');
      if (tagsParam) {
        const tagsList = tagsParam.toLowerCase().split(',').map(t => t.trim());
        filtered = filtered.filter(a => {
          if (!a.tags) return false;
          const animeTags = a.tags.map(t => t.name.toLowerCase());
          return tagsList.every(t => animeTags.includes(t));
        });
      }
      
      if (statusFilter) {
        const st = statusFilter.toUpperCase();
        filtered = filtered.filter(a => a.status === st);
      }
      
      if (yearFilter) {
        filtered = filtered.filter(a => a.seasonYear === yearFilter || (a.startDate && a.startDate.year === yearFilter));
      }

      if (studioFilter) {
        const stu = studioFilter.toLowerCase();
        filtered = filtered.filter(a => {
          if (!a.studios || !a.studios.edges) return false;
          return a.studios.edges.some(s => s.node && s.node.name.toLowerCase().includes(stu));
        });
      }
      
      if (sort) {
        const s = sort.toLowerCase();
        if (s === 'score') {
          filtered.sort((a, b) => (b.averageScore || 0) - (a.averageScore || 0));
        } else if (s === 'popularity') {
          filtered.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
        } else if (s === 'new' || s === 'newest') {
          filtered.sort((a, b) => {
            const dateA = a.startDate ? (a.startDate.year * 10000 + (a.startDate.month || 1) * 100 + (a.startDate.day || 1)) : 0;
            const dateB = b.startDate ? (b.startDate.year * 10000 + (b.startDate.month || 1) * 100 + (b.startDate.day || 1)) : 0;
            return dateB - dateA;
          });
        } else if (s === 'old' || s === 'oldest') {
          filtered.sort((a, b) => {
            const dateA = a.startDate ? (a.startDate.year * 10000 + (a.startDate.month || 1) * 100 + (a.startDate.day || 1)) : 99999999;
            const dateB = b.startDate ? (b.startDate.year * 10000 + (b.startDate.month || 1) * 100 + (b.startDate.day || 1)) : 99999999;
            return dateA - dateB;
          });
        }
      }
      
      const total = filtered.length;
      const paginated = filtered.slice(offset, offset + limit);
      
      return {
        total,
        limit,
        offset,
        page: Math.floor(offset / limit) + 1,
        total_pages: Math.ceil(total / limit),
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
      
      if (path === '/recent-episodes') {
        const items = await fetchGitHubJSON('/lists/recent_episodes.json');
        return jsonResponse(processItems(items || []));
      }

      // Metadata Endpoints
      if (path === '/meta' || path === '/total-anime') {
        const items = await fetchGitHubJSON('/lists/metadata.json');
        return jsonResponse(items || {});
      }
      
      if (path === '/genres') {
        const items = await fetchGitHubJSON('/lists/genres.json');
        return jsonResponse(items || []);
      }
      
      if (path === '/tags') {
        const items = await fetchGitHubJSON('/lists/tags.json');
        return jsonResponse(items || []);
      }
      
      if (path === '/studios') {
        const items = await fetchGitHubJSON('/lists/studios.json');
        return jsonResponse(items || []);
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
        endpoints: [
          "/anime", "/anime/:id", "/top", "/popular", "/ongoing", 
          "/season", "/schedule", "/upcoming", "/movies", "/recent-episodes",
          "/meta", "/genres", "/tags", "/studios"
        ]
      }, 404);

    } catch (err) {
      return jsonResponse({error: err.message}, 500);
    }
  }
};
