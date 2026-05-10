import type {
  GridSafetyGeoJson,
  HomeStats,
  Listing,
  ModelMetrics,
  RecommendationListing,
  RecommendationWeights,
} from './types';

interface ApiRowsResponse<T> {
  ok: boolean;
  rows?: T[];
  count?: number;
  message?: string;
}

interface GridSafetyGeoJsonResponse {
  ok: boolean;
  year?: number;
  count?: number;
  geojson?: GridSafetyGeoJson;
  message?: string;
}

interface ModelMetricsResponse extends ModelMetrics {
  ok: boolean;
  message?: string;
}

interface HomeStatsResponse extends HomeStats {
  ok: boolean;
  message?: string;
}

interface RecommendationResponse extends ApiRowsResponse<RecommendationListing> {
  weights?: {
    safety: number;
    convenience: number;
    distance: number;
    affordability: number;
  };
}

const rawApiBase =
  ((import.meta as { env?: Record<string, string | undefined> }).env?.VITE_API_BASE_URL || '');
const API_BASE = rawApiBase.replace(/\/$/, '');

function buildApiUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        query.set(key, String(value));
      }
    }
  }

  const normalized = path.startsWith('/') ? path : `/${path}`;
  const search = query.toString();
  return `${API_BASE}${normalized}${search ? `?${search}` : ''}`;
}

async function getJson<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const response = await fetch(buildApiUrl(path, params), {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export async function fetchListings(limit = 300): Promise<Listing[]> {
  const data = await getJson<ApiRowsResponse<Listing>>('/api/listings', { limit });
  if (!data.ok) {
    throw new Error(data.message || 'Failed to load listings');
  }
  return data.rows || [];
}

export async function fetchRecommendations(
  weights: RecommendationWeights,
  limit = 10
): Promise<RecommendationListing[]> {
  const data = await getJson<RecommendationResponse>('/api/recommend', {
    ...weights,
    limit,
  });
  if (!data.ok) {
    throw new Error(data.message || 'Failed to load recommendations');
  }
  return data.rows || [];
}

export async function fetchGridSafetyGeoJson(year = 2026, limit = 20000): Promise<GridSafetyGeoJson> {
  const data = await getJson<GridSafetyGeoJsonResponse>('/api/grid-safety-geojson', { year, limit });
  if (!data.ok) {
    throw new Error(data.message || 'Failed to load safety map geojson');
  }
  return data.geojson || { type: 'FeatureCollection', features: [] };
}

export async function fetchModelMetrics(): Promise<ModelMetrics> {
  const data = await getJson<ModelMetricsResponse>('/api/model-metrics');
  if (!data.ok) {
    throw new Error(data.message || 'Failed to load model metrics');
  }

  return {
    combined_rmse: data.combined_rmse,
    property_rmse: data.property_rmse,
    violence_rmse: data.violence_rmse,
    hit_rate: data.hit_rate,
    jaccard: data.jaccard,
  };
}

export async function fetchHomeStats(): Promise<HomeStats> {
  const data = await getJson<HomeStatsResponse>('/api/home-stats');
  if (!data.ok) {
    throw new Error(data.message || 'Failed to load home stats');
  }

  return {
    active_listings: Number(data.active_listings || 0),
    median_safety_score: data.median_safety_score ?? null,
    source: data.source || 'unknown',
  };
}
