import type { Feature, FeatureCollection, Geometry } from 'geojson';

export interface Amenity {
  name: string;
  type: string;
  distance: number;
}

export interface CrimeData {
  property: number;
  violence: number;
  property: number;
  total: number;
}

export interface Listing {
  listing_id: number;
  href: string;
  title: string;
  price: number;
  location_text: string;
  latitude: number;
  longitude: number;
  bedroom_number: number;
  distance_score: number;
  convenience_score: number;
  safety_score: number;
  affordability_score: number;
  composite_score: number;
  bedrooms: number;
  bathrooms: number;
  address: string;
  description: string;
  amenities: Amenity[];
  crime_data: CrimeData;
  url: string;
  image_url: string;
}

export interface RecommendationListing extends Listing {
  weighted_score: number;
}

export interface RecommendationWeights {
  safety: number;
  convenience: number;
  distance: number;
  affordability: number;
}

export interface GridCell {
  grid_id: string;
  convenience_score: number;
  safety_score: number;
  safety_bucket: number;
  year: number;
}

export type GridSafetyFeature = Feature<Geometry, GridCell>;

export type GridSafetyGeoJson = FeatureCollection<Geometry, GridCell>;

export interface ModelMetrics {
  combined_rmse: number | null;
  property_rmse: number | null;
  violence_rmse: number | null;
  hit_rate: number | null;
  jaccard: number | null;
}

export interface HomeStats {
  active_listings: number;
  median_safety_score: number | null;
  source: string;
}
