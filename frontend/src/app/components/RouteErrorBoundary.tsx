import { isRouteErrorResponse, Link, useRouteError } from 'react-router';
import { Button } from './ui/button';

export function RouteErrorBoundary() {
  const error = useRouteError();

  let title = 'Page Error';
  let message = 'An unexpected error occurred while loading this page.';

  if (isRouteErrorResponse(error)) {
    title = `${error.status} ${error.statusText}`;
    message = typeof error.data === 'string' ? error.data : message;
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-xl border bg-white p-6 shadow-sm">
        <h1 className="mb-2 text-2xl text-[#CE1141]">{title}</h1>
        <p className="mb-6 text-sm text-gray-700">{message}</p>
        <div className="flex gap-3">
          <Link to="/">
            <Button className="bg-[#CE1141] hover:bg-[#CE1141]/90">Back Home</Button>
          </Link>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Reload
          </Button>
        </div>
      </div>
    </div>
  );
}
