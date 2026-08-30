interface EmptyStateProps {
  message: string;
  /**
   * Optional call to action.
   *
   * Most empty states open a create form that lives on the same page, so the action
   * needs a handler rather than a destination. The union makes that explicit: pass
   * `onClick` for in-page actions or `href` to navigate, never both.
   *
   * Previously this accepted only `href`, so every caller passed `href: "#"` and the
   * button rendered as an anchor that did nothing — the page-level "New …" button
   * worked while the identical one in the empty state silently failed.
   */
  action?:
    | { label: string; onClick: () => void; href?: never }
    | { label: string; href: string; onClick?: never };
}

export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-sm text-surface-500">{message}</p>
      {action &&
        (action.onClick ? (
          <button type="button" onClick={action.onClick} className="btn-primary mt-4">
            {action.label}
          </button>
        ) : (
          <a href={action.href} className="btn-primary mt-4">
            {action.label}
          </a>
        ))}
    </div>
  );
}
