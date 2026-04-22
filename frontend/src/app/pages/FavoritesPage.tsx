import { useEffect, useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { ListingCard } from '../components/ListingCard';
import { Button } from '../components/ui/button';
import { Heart } from 'lucide-react';
import { Link } from 'react-router';
import { useListings } from '../utils/hooks';
import { readFavoriteIds, writeFavoriteIds } from '../utils/favorites';

export function FavoritesPage() {
  const { data: listings, loading, error } = useListings(500);
  const [favorites, setFavorites] = useState<Set<number>>(() => new Set(readFavoriteIds()));

  useEffect(() => {
    writeFavoriteIds(favorites);
  }, [favorites]);

  const favoriteListings = listings.filter((listing) => favorites.has(listing.listing_id));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-[#CE1141] mb-2">My Favorites</h1>
          <p className="text-gray-600">
            Manage your saved listings
          </p>
        </div>

        {loading && (
          <Card className="mb-4">
            <CardContent className="p-6 text-center text-gray-600">
              Loading favorite listings...
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="mb-4 border-red-200 bg-red-50">
            <CardContent className="p-4 text-sm text-red-700">
              Failed to load listing data: {error}
            </CardContent>
          </Card>
        )}

        {favoriteListings.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {favoriteListings.map((listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
                onFavorite={(id) => {
                  setFavorites((prev) => {
                    const next = new Set(prev);
                    if (next.has(id)) {
                      next.delete(id);
                    } else {
                      next.add(id);
                    }
                    return next;
                  });
                }}
                isFavorited={true}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <Heart className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="mb-2">No Favorites Yet</h3>
              <p className="text-gray-600 mb-4">
                Start exploring listings and save your favorites
              </p>
              <Link to="/listings">
                <Button className="bg-[#CE1141] hover:bg-[#CE1141]/90">
                  Browse Listings
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
