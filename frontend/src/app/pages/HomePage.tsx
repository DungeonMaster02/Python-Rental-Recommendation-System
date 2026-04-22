import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Home, Shield, MapPin, DollarSign, TrendingUp } from 'lucide-react';
import { useHomeStats, useModelMetrics } from '../utils/hooks';

export function HomePage() {
  const { data: homeStats, loading: statsLoading } = useHomeStats();
  const { data: modelMetrics, loading: metricsLoading } = useModelMetrics();
  const hasDatabaseStats = homeStats?.source === 'database';
  const totalListings = homeStats?.active_listings ?? null;
  const rawHitRate = modelMetrics?.hit_rate ?? null;
  const predictionAccuracy = rawHitRate === null
    ? null
    : (rawHitRate <= 1 ? rawHitRate * 100 : rawHitRate);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-r from-[#CE1141] to-[#FFB81C] text-white py-20 px-4">
        <div className="max-w-6xl mx-auto text-center relative z-10">
          <h1 className="text-4xl md:text-6xl mb-6">
            Find Your Perfect Home Near USC
          </h1>
          <p className="text-xl md:text-2xl mb-8 opacity-90">
            Data-driven housing recommendations powered by multi-dimensional scoring
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/listings">
              <Button 
                size="lg" 
                className="bg-white text-[#CE1141] hover:bg-gray-100 text-lg px-8 py-6"
              >
                Browse Listings
              </Button>
            </Link>
            <Link to="/recommend">
              <Button 
                size="lg" 
                variant="outline"
                className="bg-transparent border-2 border-white text-white hover:bg-white/10 text-lg px-8 py-6"
              >
                Start Recommendation
              </Button>
            </Link>
          </div>
        </div>
        
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full opacity-10">
          <div className="absolute top-10 left-10 w-32 h-32 border-4 border-white rounded-full"></div>
          <div className="absolute bottom-10 right-10 w-24 h-24 border-4 border-white rounded-full"></div>
        </div>
      </section>

      {/* Value Proposition - 3 Scores + Price Range */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl text-center mb-4 text-[#CE1141]">
            Our Scoring & Budget System
          </h2>
          <p className="text-center text-gray-600 mb-12 max-w-2xl mx-auto">
            We evaluate listings with three core scores and a direct price-range filter
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border-2 hover:border-[#CE1141] transition-colors">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-[#388E3C]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-[#388E3C]" />
                </div>
                <h3 className="mb-2 text-[#CE1141]">Safety Score</h3>
                <p className="text-sm text-gray-600">
                  ML-powered crime prediction from 2010-2024 history, projected to 2026
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 hover:border-[#CE1141] transition-colors">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-[#2196F3]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Home className="w-8 h-8 text-[#2196F3]" />
                </div>
                <h3 className="mb-2 text-[#CE1141]">Convenience Score</h3>
                <p className="text-sm text-gray-600">
                  Backend-provided convenience index from the project data pipeline
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 hover:border-[#CE1141] transition-colors">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-[#FFB81C]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MapPin className="w-8 h-8 text-[#FFB81C]" />
                </div>
                <h3 className="mb-2 text-[#CE1141]">Distance Score</h3>
                <p className="text-sm text-gray-600">
                  Straight-line distance to USC UPC center, normalized to a 0-100 score
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 hover:border-[#CE1141] transition-colors">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-[#388E3C]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <DollarSign className="w-8 h-8 text-[#388E3C]" />
                </div>
                <h3 className="mb-2 text-[#CE1141]">Price Range</h3>
                <p className="text-sm text-gray-600">
                  Filter listings directly by your preferred monthly rent range
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Statistics */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-5xl mb-2 text-[#CE1141]">
                {statsLoading ? '...' : hasDatabaseStats && totalListings !== null ? totalListings : 'N/A'}
              </div>
              <div className="text-gray-600">Active Listings</div>
            </div>
            <div className="text-center">
              <div className="text-5xl mb-2 text-[#388E3C]">
                {metricsLoading ? '--' : predictionAccuracy !== null ? `${predictionAccuracy.toFixed(1)}%` : 'N/A'}
              </div>
              <div className="text-gray-600">Prediction Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-5xl mb-2 text-[#FFB81C]">LA City</div>
              <div className="text-gray-600">Coverage Area</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl text-center mb-12 text-[#CE1141]">
            How It Works
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-[#CE1141] text-white rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                1
              </div>
              <h3 className="mb-2">Browse or Search</h3>
              <p className="text-gray-600">
                Explore listings with filters or use our recommendation engine
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-[#CE1141] text-white rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                2
              </div>
              <h3 className="mb-2">Adjust Your Priorities</h3>
              <p className="text-gray-600">
                Set weights for safety, convenience, distance, then narrow by price range
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-[#CE1141] text-white rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                3
              </div>
              <h3 className="mb-2">Get Recommendations</h3>
              <p className="text-gray-600">
                Receive ranked results tailored to your unique preferences
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 bg-gradient-to-r from-[#CE1141] to-[#FFB81C] text-white">
        <div className="max-w-4xl mx-auto text-center">
          <TrendingUp className="w-16 h-16 mx-auto mb-6" />
          <h2 className="text-3xl mb-4">Ready to Find Your Perfect Home?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join hundreds of USC students who've found their ideal housing
          </p>
          <Link to="/listings">
            <Button 
              size="lg"
              className="bg-white text-[#CE1141] hover:bg-gray-100 text-lg px-8 py-6"
            >
              Get Started Now
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
