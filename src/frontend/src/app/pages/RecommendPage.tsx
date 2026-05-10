import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Slider } from '../components/ui/slider';
import { Button } from '../components/ui/button';
import { ScoreBadge } from '../components/ScoreBadge';
import { Shield, Home, MapPin, DollarSign, Heart, TrendingUp } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useRecommendations } from '../utils/hooks';
import { readFavoriteIds, writeFavoriteIds } from '../utils/favorites';

const PRICE_RANGE_MAX = 10000;

export function RecommendPage() {
  const [weights, setWeights] = useState({
    safety: 30,
    convenience: 25,
    distance: 45,
  });
  const [priceRange, setPriceRange] = useState<[number, number]>([0, PRICE_RANGE_MAX]);
  const [favorites, setFavorites] = useState<Set<number>>(() => new Set(readFavoriteIds()));

  useEffect(() => {
    writeFavoriteIds(favorites);
  }, [favorites]);

  const normalizedWeights = useMemo(() => {
    const total = weights.safety + weights.convenience + weights.distance;
    if (total <= 0) {
      return {
        safety: 30,
        convenience: 25,
        distance: 45,
      };
    }
    return {
      safety: (weights.safety / total) * 100,
      convenience: (weights.convenience / total) * 100,
      distance: (weights.distance / total) * 100,
    };
  }, [weights]);

  const updateWeight = (key: keyof typeof weights, value: number) => {
    setWeights(prev => ({ ...prev, [key]: value }));
  };

  const recommendationWeights = useMemo(
    () => ({
      safety: normalizedWeights.safety,
      convenience: normalizedWeights.convenience,
      distance: normalizedWeights.distance,
      affordability: 0,
    }),
    [normalizedWeights]
  );

  const {
    data: recommendations,
    loading,
    error,
  } = useRecommendations(recommendationWeights, 3000);

  const filteredRecommendations = useMemo(
    () =>
      recommendations
        .filter((listing) => listing.price >= priceRange[0] && listing.price <= priceRange[1])
        .slice(0, 10),
    [recommendations, priceRange]
  );

  const chartData = [
    { name: 'Safety', value: normalizedWeights.safety, color: '#388E3C' },
    { name: 'Convenience', value: normalizedWeights.convenience, color: '#2196F3' },
    { name: 'Distance', value: normalizedWeights.distance, color: '#FFB81C' },
  ];

  const toggleFavorite = (listingId: number) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(listingId)) next.delete(listingId);
      else next.add(listingId);
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-[#CE1141] mb-2">Weighted Recommendation Engine</h1>
          <p className="text-gray-600">
            Adjust the importance of each factor to get personalized housing recommendations
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Weight Controls */}
          <div className="lg:col-span-1 space-y-6">
            {/* Weight Sliders */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-[#CE1141]" />
                  Adjust Weights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Safety */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-[#388E3C]" />
                      Safety
                    </Label>
                    <span className="text-sm font-mono">
                      {normalizedWeights.safety.toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    value={[weights.safety]}
                    onValueChange={(v) => updateWeight('safety', v[0])}
                    className="[&_[role=slider]]:bg-[#388E3C]"
                  />
                </div>

                {/* Convenience */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="flex items-center gap-2">
                      <Home className="w-4 h-4 text-[#2196F3]" />
                      Convenience
                    </Label>
                    <span className="text-sm font-mono">
                      {normalizedWeights.convenience.toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    value={[weights.convenience]}
                    onValueChange={(v) => updateWeight('convenience', v[0])}
                    className="[&_[role=slider]]:bg-[#2196F3]"
                  />
                </div>

                {/* Distance */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-[#FFB81C]" />
                      Distance to USC
                    </Label>
                    <span className="text-sm font-mono">
                      {normalizedWeights.distance.toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    value={[weights.distance]}
                    onValueChange={(v) => updateWeight('distance', v[0])}
                    className="[&_[role=slider]]:bg-[#FFB81C]"
                  />
                </div>

                {/* Price Range */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-[#CE1141]" />
                      Price Range
                    </Label>
                    <span className="text-sm font-mono">
                      ${priceRange[0]} - ${priceRange[1]}
                    </span>
                  </div>
                  <Slider
                    min={0}
                    max={PRICE_RANGE_MAX}
                    step={100}
                    value={priceRange}
                    onValueChange={(v) => setPriceRange(v as [number, number])}
                    className="[&_[role=slider]]:bg-[#CE1141]"
                  />
                </div>

                {/* Reset Button */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setWeights({ safety: 30, convenience: 25, distance: 45 });
                    setPriceRange([0, PRICE_RANGE_MAX]);
                  }}
                >
                  Reset to Defaults
                </Button>
              </CardContent>
            </Card>

            {/* Weight Distribution Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Weight Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value.toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Top Recommendations */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Top 10 Recommendations</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                {loading && recommendations.length === 0 && (
                  <div className="mb-4 rounded-lg border bg-gray-50 p-4 text-sm text-gray-600">
                    Loading recommendations from backend...
                  </div>
                )}

                {error && (
                  <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    Failed to load recommendation data: {error}
                  </div>
                )}

                <div className="space-y-3">
                  {filteredRecommendations.map((listing, index) => (
                    <a
                      key={listing.listing_id}
                      href={listing.href || listing.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block"
                    >
                      <Card className="hover:shadow-md transition-shadow cursor-pointer border-2 hover:border-[#CE1141]">
                        <CardContent className="p-4">
                          <div className="flex items-start gap-4">
                            {/* Rank Badge */}
                            <div className="flex-shrink-0">
                              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white ${
                                index === 0 ? 'bg-[#FFB81C]' :
                                index === 1 ? 'bg-gray-400' :
                                index === 2 ? 'bg-[#CD7F32]' :
                                'bg-[#CE1141]'
                              }`}>
                                <span className="text-xl">#{index + 1}</span>
                              </div>
                            </div>

                            {/* Listing Info */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-4 mb-2">
                                <div className="flex-1">
                                  <h3 className="line-clamp-1">{listing.title}</h3>
                                  <p className="text-sm text-gray-600">{listing.location_text || listing.address}</p>
                                </div>
                                <div className="text-right space-y-2">
                                  <div className="text-xl text-[#CE1141]">
                                    ${listing.price.toLocaleString()}
                                  </div>
                                  <div className="text-sm text-gray-600">/month</div>
                                  <Button
                                    variant={favorites.has(listing.listing_id) ? 'default' : 'outline'}
                                    size="sm"
                                    className={favorites.has(listing.listing_id) ? 'bg-[#CE1141] hover:bg-[#CE1141]/90' : ''}
                                    onClick={(e) => {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      toggleFavorite(listing.listing_id);
                                    }}
                                  >
                                    <Heart className={`w-4 h-4 mr-1 ${favorites.has(listing.listing_id) ? 'fill-current' : ''}`} />
                                    Favorite
                                  </Button>
                                </div>
                              </div>

                              {/* Weighted Score */}
                              <div className="mb-3 p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-gray-600">Weighted Score</span>
                                  <span className="text-2xl font-mono text-[#CE1141]">
                                    {listing.weighted_score.toFixed(1)}
                                  </span>
                                </div>
                              </div>

                              {/* Individual Scores */}
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                <ScoreBadge
                                  score={listing.safety_score}
                                  label="Safety"
                                  type="safety"
                                  showScore={true}
                                />
                                <ScoreBadge
                                  score={listing.convenience_score}
                                  label="Conv"
                                  type="convenience"
                                  showScore={true}
                                />
                                <ScoreBadge
                                  score={listing.distance_score}
                                  label="Dist"
                                  type="distance"
                                  showScore={true}
                                />
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </a>
                  ))}

                  {!loading && filteredRecommendations.length === 0 && (
                    <div className="rounded-lg border bg-white p-8 text-center text-gray-600">
                      No recommendation data available.
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
