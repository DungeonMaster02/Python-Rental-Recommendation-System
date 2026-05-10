import { useEffect, useState } from 'react';
import {
  fetchHomeStats,
  fetchGridSafetyGeoJson,
  fetchListings,
  fetchModelMetrics,
  fetchRecommendations,
} from './api';
import type {
  GridSafetyGeoJson,
  HomeStats,
  Listing,
  ModelMetrics,
  RecommendationListing,
  RecommendationWeights,
} from './types';

interface AsyncState<T> {
  data: T;
  loading: boolean;
  error: string | null;
}

export function useListings(limit = 300): AsyncState<Listing[]> {
  const [data, setData] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchListings(limit)
      .then((rows) => {
        if (active) {
          setData(rows);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [limit]);

  return { data, loading, error };
}

export function useGridSafetyGeoJson(year = 2026, limit = 20000): AsyncState<GridSafetyGeoJson> {
  const [data, setData] = useState<GridSafetyGeoJson>({ type: 'FeatureCollection', features: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchGridSafetyGeoJson(year, limit)
      .then((geojson) => {
        if (active) {
          setData(geojson);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [year, limit]);

  return { data, loading, error };
}

export function useRecommendations(
  weights: RecommendationWeights,
  limit = 10,
  debounceMs = 200
): AsyncState<RecommendationListing[]> {
  const [data, setData] = useState<RecommendationListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    const timer = window.setTimeout(() => {
      fetchRecommendations(weights, limit)
        .then((rows) => {
          if (active) {
            setData(rows);
            setLoading(false);
          }
        })
        .catch((err: unknown) => {
          if (active) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            setLoading(false);
          }
        });
    }, debounceMs);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [weights, limit, debounceMs]);

  return { data, loading, error };
}

export function useModelMetrics(): AsyncState<ModelMetrics | null> {
  const [data, setData] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchModelMetrics()
      .then((metrics) => {
        if (active) {
          setData(metrics);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { data, loading, error };
}

export function useHomeStats(): AsyncState<HomeStats | null> {
  const [data, setData] = useState<HomeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchHomeStats()
      .then((stats) => {
        if (active) {
          setData(stats);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { data, loading, error };
}
