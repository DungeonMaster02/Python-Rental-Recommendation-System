import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Shield, Home, MapPin, DollarSign, Database, TrendingUp } from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { useModelMetrics } from '../utils/hooks';

export function AboutPage() {
  const { data: metrics, loading: metricsLoading, error: metricsError } = useModelMetrics();

  const dataSources = [
    { name: 'LA Open Data', description: 'Crime statistics and geographic data', url: 'https://data.lacity.org' },
    { name: 'Craigslist', description: 'Real-time rental listings', url: 'https://losangeles.craigslist.org' },
    { name: 'OpenStreetMap', description: 'Points of interest and amenities', url: 'https://www.openstreetmap.org' },
    { name: 'LA GeoHub', description: 'City boundary and grid shapefiles for geospatial analysis', url: 'https://geohub.lacity.org' }
  ];

  const metricOrNA = (value: number | null | undefined, factor = 1) => {
    if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
    return (value * factor).toFixed(factor === 1 ? 3 : 1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-[#CE1141] mb-4">About USC Housing Recommendation System</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            A data-driven platform that helps USC students find the perfect housing 
            using multi-dimensional analysis and machine learning predictions
          </p>
        </div>

        {/* Project Overview */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Project Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-700 leading-relaxed">
              Finding housing near USC can be overwhelming. With hundreds of listings across Los Angeles, 
              it's difficult to balance safety, convenience, distance, and budget. Our platform 
              solves this problem by providing objective, data-driven scores for each property plus 
              flexible price range filtering.
            </p>
            <p className="text-gray-700 leading-relaxed">
              Built with React, TypeScript, and Tailwind CSS on the frontend, and powered by a Flask 
              backend with PostgreSQL database, our system processes rental data and combines 
              it with crime predictions, amenity analysis, and distance calculations to help you make 
              informed housing decisions.
            </p>
          </CardContent>
        </Card>

        {/* Scoring Methodology */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Scoring Methodology</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-[#388E3C]/10 rounded-lg flex items-center justify-center">
                    <Shield className="w-6 h-6 text-[#388E3C]" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="mb-2 text-[#CE1141]">Safety Score (0-100)</h3>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    Based on XGBoost machine learning model predictions for 2026. We analyze historical 
                    crime data from LAPD, divided into 400m × 400m grid cells. The model considers crime 
                    density, crime types (violent vs property), and temporal patterns. Scores are normalized 
                    with 100 being the safest.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-[#2196F3]/10 rounded-lg flex items-center justify-center">
                    <Home className="w-6 h-6 text-[#2196F3]" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="mb-2 text-[#CE1141]">Convenience Score (0-100)</h3>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    Convenience score is provided directly by the backend data pipeline and stored in the
                    listing/grid tables. The frontend displays this score as-is and does not recalculate it
                    on the page.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-[#FFB81C]/10 rounded-lg flex items-center justify-center">
                    <MapPin className="w-6 h-6 text-[#FFB81C]" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="mb-2 text-[#CE1141]">Distance Score (0-100)</h3>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    Distance score is computed uniformly from the straight-line distance between each listing
                    and the USC UPC campus center point, then normalized to a 0-100 scale.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-[#388E3C]/10 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-[#388E3C]" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="mb-2 text-[#CE1141]">Price Range Filter</h3>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    Affordability score has been removed from the current frontend workflow. Users now
                    control budget preference with a direct price range filter.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Sources */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-[#CE1141]" />
              Data Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dataSources.map((source, index) => (
                <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                  <h4 className="mb-1">{source.name}</h4>
                  <p className="text-sm text-gray-600 mb-2">{source.description}</p>
                  <Badge variant="secondary" className="text-xs">Active</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* ML Model Details */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#CE1141]" />
              Machine Learning Model
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-mono text-[#CE1141] mb-1">XGBoost</div>
                <div className="text-sm text-gray-600">Algorithm</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-mono text-[#CE1141] mb-1">5-Fold</div>
                <div className="text-sm text-gray-600">Cross Validation</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-mono text-[#CE1141] mb-1">
                  {metricsLoading ? '...' : `${metricOrNA(metrics?.hit_rate, 100)}%`}
                </div>
                <div className="text-sm text-gray-600">Hit Rate</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-mono text-[#CE1141] mb-1">
                  {metricsLoading ? '...' : metricOrNA(metrics?.jaccard)}
                </div>
                <div className="text-sm text-gray-600">Jaccard</div>
              </div>
            </div>
            {metricsError && (
              <p className="text-sm text-red-700">Failed to load model metrics: {metricsError}</p>
            )}
            {metrics && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="rounded-lg border bg-gray-50 p-3 text-sm">
                  Combined RMSE: <strong>{metricOrNA(metrics.combined_rmse)}</strong>
                </div>
                <div className="rounded-lg border bg-gray-50 p-3 text-sm">
                  Property RMSE: <strong>{metricOrNA(metrics.property_rmse)}</strong>
                </div>
                <div className="rounded-lg border bg-gray-50 p-3 text-sm">
                  Violence RMSE: <strong>{metricOrNA(metrics.violence_rmse)}</strong>
                </div>
              </div>
            )}
            <p className="text-sm text-gray-600 leading-relaxed">
              Our safety prediction model uses XGBoost (Extreme Gradient Boosting) trained on historical 
              crime data from 2010-2024. The model learns patterns in crime distribution across Los Angeles 
              and projects future safety scores for 2026. We validate predictions using 5-fold cross-validation 
              to ensure accuracy and prevent overfitting.
            </p>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-900">
            <strong>Disclaimer:</strong> This platform provides data-driven recommendations based on 
            statistical analysis. Always verify listing details, visit properties in person, and conduct 
            your own research before making housing decisions. Crime predictions are estimates and actual 
            safety may vary.
          </p>
        </div>
      </div>
    </div>
  );
}
