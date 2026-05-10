import { useEffect, useMemo, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import { ListingCard } from '../components/ListingCard';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Slider } from '../components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '../components/ui/sheet';
import { SlidersHorizontal, Grid3x3, Map, Search } from 'lucide-react';
import { useListings } from '../utils/hooks';
import { readFavoriteIds, writeFavoriteIds } from '../utils/favorites';
import { ensureLeafletMarkerIcons } from '../utils/leaflet';

ensureLeafletMarkerIcons();

type SortOption = 'newest' | 'price-low' | 'price-high' | 'distance' | 'safety';
const PRICE_RANGE_MAX = 10000;

export function ListingsPage() {
  const { data: listings, loading, error } = useListings(1000);
  const [view, setView] = useState<'grid' | 'map'>('grid');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [searchQuery, setSearchQuery] = useState('');

  const [priceRange, setPriceRange] = useState<[number, number]>([0, PRICE_RANGE_MAX]);
  const [minSafety, setMinSafety] = useState(0);
  const [maxDistanceKm, setMaxDistanceKm] = useState(12);
  const [favorites, setFavorites] = useState<Set<number>>(() => new Set(readFavoriteIds()));

  useEffect(() => {
    writeFavoriteIds(favorites);
  }, [favorites]);

  const filteredListings = useMemo(() => {
    const filtered = listings.filter((listing) => {
      if (listing.price < priceRange[0] || listing.price > priceRange[1]) return false;
      if (listing.safety_score < minSafety) return false;

      const distanceKm = (12 * (100 - listing.distance_score)) / 100;
      if (distanceKm > maxDistanceKm) return false;

      const query = searchQuery.trim().toLowerCase();
      if (!query) return true;
      return (
        listing.title.toLowerCase().includes(query)
        || listing.location_text.toLowerCase().includes(query)
      );
    });

    switch (sortBy) {
      case 'newest':
        filtered.sort((a, b) => b.listing_id - a.listing_id);
        break;
      case 'price-low':
        filtered.sort((a, b) => a.price - b.price);
        break;
      case 'price-high':
        filtered.sort((a, b) => b.price - a.price);
        break;
      case 'distance':
        filtered.sort((a, b) => b.distance_score - a.distance_score);
        break;
      case 'safety':
        filtered.sort((a, b) => b.safety_score - a.safety_score);
        break;
    }

    return filtered;
  }, [listings, priceRange, minSafety, maxDistanceKm, searchQuery, sortBy]);

  const mapListings = useMemo(() => filteredListings.slice(0, 250), [filteredListings]);
  const mapCenter = useMemo<[number, number]>(() => {
    if (mapListings.length === 0) return [34.0224, -118.2851];
    const latAvg = mapListings.reduce((sum, listing) => sum + listing.latitude, 0) / mapListings.length;
    const lonAvg = mapListings.reduce((sum, listing) => sum + listing.longitude, 0) / mapListings.length;
    return [latAvg, lonAvg];
  }, [mapListings]);

  const handleFavorite = (id: number) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const resetFilters = () => {
    setPriceRange([0, PRICE_RANGE_MAX]);
    setMinSafety(0);
    setMaxDistanceKm(12);
    setSearchQuery('');
  };

  const activeFilterCount =
    (priceRange[0] > 0 || priceRange[1] < PRICE_RANGE_MAX ? 1 : 0)
    + (minSafety > 0 ? 1 : 0)
    + (maxDistanceKm < 12 ? 1 : 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="sticky top-16 z-40 border-b bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
            <div>
              <h1 className="mb-1 text-[#CE1141]">Listings</h1>
              <p className="text-sm text-gray-600">{filteredListings.length} properties found</p>
            </div>

            <div className="flex w-full flex-wrap gap-2 md:w-auto">
              <div className="relative flex-1 md:w-72">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search title / location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
                <SelectTrigger className="w-[190px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest (listing_id)</SelectItem>
                  <SelectItem value="price-low">Price: Low to High</SelectItem>
                  <SelectItem value="price-high">Price: High to Low</SelectItem>
                  <SelectItem value="distance">Distance Score</SelectItem>
                  <SelectItem value="safety">Safety Score</SelectItem>
                </SelectContent>
              </Select>

              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" className="relative">
                    <SlidersHorizontal className="mr-2 h-4 w-4" />
                    Filters
                    {activeFilterCount > 0 && (
                      <span className="ml-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#CE1141] text-xs text-white">
                        {activeFilterCount}
                      </span>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent className="overflow-y-auto">
                  <SheetHeader>
                    <SheetTitle>Filters</SheetTitle>
                  </SheetHeader>

                  <div className="space-y-6 py-6">
                    <div>
                      <Label>Price Range</Label>
                      <div className="pt-4">
                        <Slider
                          min={0}
                          max={PRICE_RANGE_MAX}
                          step={100}
                          value={priceRange}
                          onValueChange={(v) => setPriceRange(v as [number, number])}
                          className="mb-2"
                        />
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>${priceRange[0]}</span>
                          <span>${priceRange[1]}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <Label>Minimum Safety Score</Label>
                      <div className="pt-4">
                        <Slider
                          min={0}
                          max={100}
                          step={5}
                          value={[minSafety]}
                          onValueChange={(v) => setMinSafety(v[0])}
                          className="mb-2"
                        />
                        <div className="text-sm text-gray-600">{minSafety}</div>
                      </div>
                    </div>

                    <div>
                      <Label>Maximum Distance to USC (km)</Label>
                      <div className="pt-4">
                        <Slider
                          min={0.5}
                          max={12}
                          step={0.5}
                          value={[maxDistanceKm]}
                          onValueChange={(v) => setMaxDistanceKm(v[0])}
                          className="mb-2"
                        />
                        <div className="text-sm text-gray-600">{maxDistanceKm.toFixed(1)} km</div>
                      </div>
                    </div>

                    <Button variant="outline" onClick={resetFilters} className="w-full">
                      Reset Filters
                    </Button>
                  </div>
                </SheetContent>
              </Sheet>

              <div className="flex gap-1 rounded-lg border p-1">
                <Button
                  variant={view === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setView('grid')}
                  className={view === 'grid' ? 'bg-[#CE1141]' : ''}
                >
                  <Grid3x3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={view === 'map' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setView('map')}
                  className={view === 'map' ? 'bg-[#CE1141]' : ''}
                >
                  <Map className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8">
        {loading && (
          <div className="mb-6 rounded-lg bg-white p-8 text-center text-gray-600">
            Loading listings from backend...
          </div>
        )}

        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            Failed to load listings: {error}
          </div>
        )}

        {view === 'grid' ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredListings.map((listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
                onFavorite={handleFavorite}
                isFavorited={favorites.has(listing.listing_id)}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border bg-white p-2">
            <div className="h-[620px] w-full overflow-hidden rounded-md">
              <MapContainer center={mapCenter} zoom={12} className="h-full w-full">
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Marker position={[34.0224, -118.2851]}>
                  <Popup>
                    <div className="text-sm">
                      <div className="font-semibold text-[#CE1141]">USC Campus</div>
                      <div>Reference point for distance score.</div>
                    </div>
                  </Popup>
                </Marker>

                {mapListings.map((listing) => {
                  const listingHref = listing.href || listing.url || 'https://losangeles.craigslist.org/search/apa';
                  return (
                    <Marker key={listing.listing_id} position={[listing.latitude, listing.longitude]}>
                      <Popup>
                        <div className="space-y-1 text-sm">
                          <div className="font-semibold">{listing.title}</div>
                          <div className="font-medium text-[#CE1141]">${listing.price.toLocaleString()}/mo</div>
                          <div className="text-gray-600">{listing.location_text}</div>
                          <a
                            href={listingHref}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-block rounded bg-[#CE1141] px-2 py-1 text-xs text-white hover:bg-[#CE1141]/90"
                          >
                            Open Listing
                          </a>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
            </div>
            <div className="px-2 py-3 text-sm text-gray-600">
              Showing {mapListings.length} markers ({filteredListings.length} filtered listings).
            </div>
          </div>
        )}

        {filteredListings.length === 0 && (
          <div className="rounded-lg bg-white p-12 text-center">
            <h3 className="mb-2 text-gray-900">No listings found</h3>
            <p className="mb-4 text-gray-600">Try adjusting your filters or search query.</p>
            <Button onClick={resetFilters} variant="outline">
              Reset Filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
