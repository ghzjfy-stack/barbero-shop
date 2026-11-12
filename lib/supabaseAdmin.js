import { createClient } from "@supabase/supabase-js";

/**
 * Server-only Supabase client (Vercel /api).
 * Env (Production + Preview):
 *   SUPABASE_URL
 *   SUPABASE_SERVICE_ROLE_KEY  — Project Settings → API → service_role
 *
 * Never expose the service role key to the browser (no VITE_*).
 */
export function getSupabaseAdmin() {
  const url = String(process.env.SUPABASE_URL || "").trim();
  const key = String(process.env.SUPABASE_SERVICE_ROLE_KEY || "").trim();
  if (!url || !key) {
    return {
      client: null,
      missing: {
        SUPABASE_URL: !url,
        SUPABASE_SERVICE_ROLE_KEY: !key,
      },
    };
  }
  return {
    client: createClient(url, key, {
      auth: { persistSession: false, autoRefreshToken: false },
    }),
    missing: null,
  };
}
