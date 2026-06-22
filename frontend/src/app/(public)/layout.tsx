/**
 * Public layout — centered card, no sidebar.
 * Covers: /login, /register, /forgot-password, /reset-password
 */
export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-100 p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="mb-8 flex items-center justify-center gap-2">
          <span className="text-2xl font-bold text-brand-700">SusDevOS</span>
        </div>
        <div className="card p-8">{children}</div>
        <p className="mt-6 text-center text-xs text-surface-400">
          © {new Date().getFullYear()} SusDevOS · GHG reporting for development projects
        </p>
      </div>
    </div>
  );
}
