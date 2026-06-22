interface EmptyStateProps {
  message: string;
  action?: { label: string; href: string };
}

export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-sm text-surface-500">{message}</p>
      {action && (
        <a href={action.href} className="btn-primary mt-4">
          {action.label}
        </a>
      )}
    </div>
  );
}
