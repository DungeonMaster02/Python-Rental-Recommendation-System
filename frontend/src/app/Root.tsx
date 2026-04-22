import { Outlet } from 'react-router';
import { Navigation } from './components/Navigation';

export function Root() {
  return (
    <div className="min-h-screen">
      <Navigation />
      <Outlet />
    </div>
  );
}
