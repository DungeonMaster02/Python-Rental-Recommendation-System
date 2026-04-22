import type { MouseEvent } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { ScoreBadge } from './ScoreBadge';
import type { Listing } from '../utils/types';
import { Shield, MapPin, Home, Heart, Share2, ExternalLink, Bed } from 'lucide-react';

interface ListingCardProps {
  listing: Listing;
  onFavorite?: (id: number) => void;
  isFavorited?: boolean;
}

const FIXED_PLACEHOLDER_IMAGE =
  'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80';

export function ListingCard({ listing, onFavorite, isFavorited = false }: ListingCardProps) {
  const listingHref = listing.href || listing.url || 'https://losangeles.craigslist.org/search/apa';

  const handleFavorite = (e: MouseEvent) => {
    e.preventDefault();
    onFavorite?.(listing.listing_id);
  };

  const handleShare = (e: MouseEvent) => {
    e.preventDefault();
    // Share functionality
    if (navigator.share) {
      navigator.share({
        title: listing.title,
        text: `Check out this listing: ${listing.title}`,
        url: listingHref,
      });
    }
  };

  return (
    <Card className="flex h-full flex-col overflow-hidden transition-shadow hover:shadow-lg">
      <div className="relative h-48 overflow-hidden bg-gray-200">
        <img
          src={FIXED_PLACEHOLDER_IMAGE}
          alt="listing placeholder"
          className="h-full w-full object-cover"
        />
      </div>

      <CardContent className="flex flex-1 flex-col p-4">
        <div className="mb-3">
          <h3 className="mb-1 line-clamp-2">{listing.title}</h3>
          <div className="flex items-center justify-between">
            <div className="text-2xl text-[#CE1141]">${listing.price.toLocaleString()}/mo</div>
            <div className="flex items-center gap-1 text-sm text-gray-600">
              <Bed className="h-4 w-4" />
              <span>{listing.bedroom_number || 0} bed</span>
            </div>
          </div>
          <p className="mt-1 text-sm text-gray-600">{listing.location_text}</p>
        </div>

        <div className="mb-4 grid grid-cols-3 gap-2">
          <ScoreBadge
            score={listing.safety_score}
            label="Safety"
            icon={<Shield className="h-3 w-3" />}
            type="safety"
          />
          <ScoreBadge
            score={listing.convenience_score}
            label="Conv"
            icon={<Home className="h-3 w-3" />}
            type="convenience"
          />
          <ScoreBadge
            score={listing.distance_score}
            label="Dist"
            icon={<MapPin className="h-3 w-3" />}
            type="distance"
          />
        </div>

        <div className="mt-auto flex gap-2">
          <Button
            variant="default"
            className="flex-1 bg-[#CE1141] hover:bg-[#CE1141]/90"
            onClick={() => window.open(listingHref, '_blank')}
          >
            Open Listing
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={handleFavorite}
            className={isFavorited ? 'text-red-500 border-red-500' : ''}
          >
            <Heart className={`h-4 w-4 ${isFavorited ? 'fill-current' : ''}`} />
          </Button>
          <Button variant="outline" size="icon" onClick={handleShare}>
            <Share2 className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => window.open(listingHref, '_blank')}>
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
