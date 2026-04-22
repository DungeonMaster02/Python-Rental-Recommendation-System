import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Shield, TrendingDown } from 'lucide-react';
import { GeoJSON, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { GeoJsonObject } from 'geojson';
import type { GridCell, GridSafetyFeature, GridSafetyGeoJson } from '../utils/types';
import { useGridSafetyGeoJson } from '../utils/hooks';
import { ensureLeafletMarkerIcons } from '../utils/leaflet';

ensureLeafletMarkerIcons();

const USC_COORD: [number, number] = [34.0224, -118.2851];
const LAYER_COLORS = ['#D32F2F', '#F57C00', '#FBC02D', '#8BC34A', '#2E7D32'];
const LAYER_LABELS = ['Layer 1 (0-20)', 'Layer 2 (21-40)', 'Layer 3 (41-60)', 'Layer 4 (61-80)', 'Layer 5 (81-100)'];

function clampSafetyScore(score: number): number {
  return Math.min(100, Math.max(0, score));
}

function resolveLayerIndex(cell?: GridCell): number {
  const bucket = Number(cell?.safety_bucket);
  if (Number.isFinite(bucket) && bucket > 0) {
    // Bucket mapping from DB:
    // 1: 0-10, 2: 11-20, ... 10: 91-100.
    // Group every two buckets into one map layer.
    const normalizedBucket = Math.min(10, Math.max(1, Math.round(bucket)));
    return Math.min(4, Math.floor((normalizedBucket - 1) / 2));
  }

  const score = clampSafetyScore(Number(cell?.safety_score ?? 0));
  if (score <= 20) return 0;
  if (score <= 40) return 1;
  if (score <= 60) return 2;
  if (score <= 80) return 3;
  return 4;
}

function getSafetyColor(cell?: GridCell): string {
  return LAYER_COLORS[resolveLayerIndex(cell)];
}

function FitGeoJsonBounds({ geojson }: { geojson: GridSafetyGeoJson }) {
  const map = useMap();

  useEffect(() => {
    if (geojson.features.length === 0) return;
    const layer = L.geoJSON(geojson as GeoJsonObject);
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.03));
    }
  }, [geojson, map]);

  return null;
}

export function SafetyMapPage() {
  const [selectedCell, setSelectedCell] = useState<GridCell | null>(null);
  const { data: geojson, loading, error } = useGridSafetyGeoJson(2026, 20000);

  const getGridStyle = (feature?: GridSafetyFeature) => {
    return {
      fillColor: getSafetyColor(feature?.properties),
      weight: 0.35,
      opacity: 0.85,
      color: '#111827',
      fillOpacity: 0.72,
    };
  };

  const onEachFeature = (feature: GridSafetyFeature, layer: L.Layer) => {
    const props = feature.properties;
    if (!props) return;

    const safety = Number(props.safety_score ?? 0);
    const convenience = Number(props.convenience_score ?? 0);

    layer.on({
      click: () => setSelectedCell(props),
    });

    if (layer instanceof L.Path) {
      layer.on({
        mouseover: () => {
          layer.setStyle({
            weight: 1.2,
            color: '#111827',
            fillOpacity: 0.9,
          });
        },
        mouseout: () => {
          layer.setStyle(getGridStyle(feature));
        },
      });
      layer.bindTooltip(
        `Grid ${props.grid_id}<br/>Safety ${safety.toFixed(1)}<br/>Convenience ${convenience.toFixed(1)}`,
        { sticky: true }
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-[#CE1141] mb-2">LA Safety Heat Map</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Map */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Safety Heat Map - 2026</CardTitle>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: LAYER_COLORS[0] }}></div>
                      <span>{LAYER_LABELS[0]}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: LAYER_COLORS[1] }}></div>
                      <span>{LAYER_LABELS[1]}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: LAYER_COLORS[2] }}></div>
                      <span>{LAYER_LABELS[2]}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: LAYER_COLORS[3] }}></div>
                      <span>{LAYER_LABELS[3]}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: LAYER_COLORS[4] }}></div>
                      <span>{LAYER_LABELS[4]}</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {loading && (
                  <div className="mb-4 rounded-lg border bg-gray-50 p-4 text-sm text-gray-600">
                    Loading safety grid from backend...
                  </div>
                )}

                {error && (
                  <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    Failed to load safety map: {error}
                  </div>
                )}

                {!loading && !error && geojson.features.length === 0 && (
                  <div className="mb-4 rounded-lg border bg-white p-4 text-sm text-gray-600">
                    No safety data available in table `grid`. Please populate `grid.safety_score` first.
                  </div>
                )}

                <div className="h-[720px] overflow-hidden rounded-lg border">
                  <MapContainer
                    center={USC_COORD}
                    zoom={11}
                    className="h-full w-full"
                    scrollWheelZoom={true}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={USC_COORD}>
                      <Popup>
                        <div className="text-sm">
                          <div className="font-semibold text-[#CE1141]">USC Campus</div>
                          <div>Reference location</div>
                        </div>
                      </Popup>
                    </Marker>
                    {geojson.features.length > 0 && (
                      <>
                        <GeoJSON
                          data={geojson as GeoJsonObject}
                          style={(feature) => getGridStyle(feature as GridSafetyFeature)}
                          onEachFeature={(feature, layer) =>
                            onEachFeature(feature as GridSafetyFeature, layer)
                          }
                        />
                        <FitGeoJsonBounds geojson={geojson} />
                      </>
                    )}
                  </MapContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Controls & Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* Selected Cell Info */}
            {selectedCell ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Grid Cell Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Safety Score</div>
                    <div className="text-3xl font-mono" style={{ 
                      color: getSafetyColor(selectedCell)
                    }}>
                      {Math.round(selectedCell.safety_score)}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Grid ID</span>
                      <span className="font-mono">{selectedCell.grid_id}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Convenience Score</span>
                      <span className="font-mono">{selectedCell.convenience_score.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Year</span>
                      <span className="font-mono">2026</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-6 text-center text-gray-500">
                  <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">Click on a grid cell to see detailed safety metrics</p>
                </CardContent>
              </Card>
            )}

            {/* Legend */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingDown className="w-4 h-4" />
                  About the Map
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 leading-relaxed">
                  This page renders GIS polygons and colors each grid cell by `safety_score` from the database `grid`
                  table. No synthetic hotspot values are generated on the frontend.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
