import { createBrowserRouter } from 'react-router';
import { Root } from './Root';
import { RouteErrorBoundary } from './components/RouteErrorBoundary';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Root,
    ErrorBoundary: RouteErrorBoundary,
    children: [
      {
        index: true,
        lazy: async () => {
          const module = await import('./pages/HomePage');
          return { Component: module.HomePage };
        },
      },
      {
        path: 'listings',
        lazy: async () => {
          const module = await import('./pages/ListingsPage');
          return { Component: module.ListingsPage };
        },
      },
      {
        path: 'recommend',
        lazy: async () => {
          const module = await import('./pages/RecommendPage');
          return { Component: module.RecommendPage };
        },
      },
      {
        path: 'safety-map',
        lazy: async () => {
          const module = await import('./pages/SafetyMapPage');
          return { Component: module.SafetyMapPage };
        },
      },
      {
        path: 'favorites',
        lazy: async () => {
          const module = await import('./pages/FavoritesPage');
          return { Component: module.FavoritesPage };
        },
      },
      {
        path: 'about',
        lazy: async () => {
          const module = await import('./pages/AboutPage');
          return { Component: module.AboutPage };
        },
      },
      {
        path: '*',
        lazy: async () => {
          const module = await import('./pages/NotFoundPage');
          return { Component: module.NotFoundPage };
        },
      },
    ],
  },
]);
