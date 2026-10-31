import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      <div className="max-w-md rounded-lg bg-surface p-8 shadow-md border border-border">
        <h1 className="text-2xl font-bold tracking-tight text-fg mb-2">
          Clinic Token & Queue SaaS
        </h1>
        <p className="text-sm text-fg-muted mb-6">
          Online tokens, live queue, reception panel, doctor console, and waiting room TV.
        </p>
        <div className="flex flex-col gap-3">
          <Link
            href="/login"
            className="inline-flex h-9 items-center justify-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-fg-inverse hover:bg-accent-hover transition-colors"
          >
            Staff Login
          </Link>
        </div>
      </div>
    </main>
  );
}
