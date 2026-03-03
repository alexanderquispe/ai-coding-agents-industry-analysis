import Link from 'next/link'
import { Home } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <h1 className="text-6xl font-bold text-zinc-100 mb-4">404</h1>
      <h2 className="text-2xl font-semibold text-zinc-300 mb-2">Page Not Found</h2>
      <p className="text-zinc-400 mb-8 text-center max-w-md">
        The page you're looking for doesn't exist or the agent hasn't been added yet.
      </p>
      <Link
        href="/"
        className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors"
      >
        <Home className="h-4 w-4" />
        Back to Home
      </Link>
    </div>
  )
}
