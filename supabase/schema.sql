-- BARBERO — run once in Supabase → SQL Editor
-- Creates/repairs customers + orders so checkout + Telegram buttons stay in sync.

-- ---------- customers ----------
create table if not exists public.customers (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  name text,
  phone text,
  email text,
  city text,
  address text,
  unit text,
  postal text,
  notes text,
  last_order_number text
);

-- Repair legacy columns from the first connect (Name / Phone-as-time / Email-as-phone).
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'customers' and column_name = 'Name'
  ) and not exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'customers' and column_name = 'name'
  ) then
    alter table public.customers rename column "Name" to name;
  end if;
exception when others then null;
end $$;

alter table public.customers add column if not exists name text;
alter table public.customers add column if not exists phone text;
alter table public.customers add column if not exists email text;
alter table public.customers add column if not exists city text;
alter table public.customers add column if not exists address text;
alter table public.customers add column if not exists unit text;
alter table public.customers add column if not exists postal text;
alter table public.customers add column if not exists notes text;
alter table public.customers add column if not exists last_order_number text;
alter table public.customers add column if not exists updated_at timestamptz default now();

create unique index if not exists customers_phone_uidx
  on public.customers (phone)
  where phone is not null and length(trim(phone)) > 0;

-- ---------- orders (full checkout snapshot) ----------
create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  order_number text not null unique,
  status text not null default 'ממתין לביט',
  paid text not null default 'No',
  payment text,
  total numeric,
  subtotal numeric,
  shipping numeric,
  discount numeric,
  coupon text,
  customer_name text,
  customer_phone text,
  customer_email text,
  city text,
  address text,
  unit text,
  postal text,
  notes text,
  items text,
  lines jsonb,
  raw jsonb
);

create index if not exists orders_status_idx on public.orders (status);
create index if not exists orders_phone_idx on public.orders (customer_phone);
create index if not exists orders_created_idx on public.orders (created_at desc);

-- Service role from Vercel bypasses RLS; keep tables locked to anon.
alter table public.customers enable row level security;
alter table public.orders enable row level security;
