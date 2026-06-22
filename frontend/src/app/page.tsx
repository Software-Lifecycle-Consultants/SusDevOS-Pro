import { redirect } from "next/navigation";

/**
 * Root route → redirect to the app dashboard.
 * The (app) layout will redirect unauthenticated users to /login.
 */
export default function RootPage() {
  redirect("/dashboard");
}
