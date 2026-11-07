-- Ng'ombe records: the live app behind ngombe.zamai.pro/my (v0.1, 7 Nov 2026). Self-hosted Supabase on our machine.
-- Design: every row carries its owner (auth.uid()); row-level security on every table; the browser talks to the
-- database through Supabase's REST with the user's token; the service role is used only by the WhatsApp binding
-- function. Entries are append-only (events); corrections are new events. Each event carries a hash of its content
-- and of the previous event of the same animal, so a later change shows.
-- Reversible: drop schema cattle cascade.

create schema if not exists cattle;

-- who: one profile per auth user; the phone is bound through the Zamai WhatsApp line (a code sent from that number)
create table if not exists cattle.profiles (
  id            uuid primary key references auth.users (id) on delete cascade,
  name          text not null check (length(name) between 2 and 80),
  place         text,                                      -- village or kraal, free text
  district      text,
  lang          text not null default 'to' check (lang in ('to', 'en')),
  role          text not null default 'owner' check (role in ('owner', 'herder', 'both')),
  phone         text unique check (phone ~ '^260[0-9]{9}$'),  -- set only by the binding function, never by the user
  phone_bound_at timestamptz,
  terms_version text,                                      -- the version accepted, e.g. '0.1'
  terms_accepted_at timestamptz,
  created_at    timestamptz not null default now()
);

-- the terms, versioned, in both languages; a profile is usable only when terms_version = the current version
create table if not exists cattle.terms (
  version     text primary key,
  en          text not null,
  to_         text,                                        -- Tonga, from a speaker; null until it exists
  current     boolean not null default false,
  created_at  timestamptz not null default now()
);

-- the animals
create table if not exists cattle.animals (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null references cattle.profiles (id) on delete cascade,
  name        text not null check (length(name) between 1 and 60),
  class       text not null check (class in ('calf', 'weaner', 'heifer', 'cow', 'bull', 'steer', 'ox')),
  sex         text check (sex in ('f', 'm')),
  dob         date,                                        -- exact when witnessed
  dob_kind    text check (dob_kind in ('witnessed', 'owner_estimate', 'teeth')),
  dob_year    int check (dob_year between 1990 and 2100), -- when only a year is known
  dam         uuid references cattle.animals (id),
  sire        uuid references cattle.animals (id),
  sire_kind   text check (sire_kind in ('known', 'candidate', 'unknown')),
  tag         text,                                        -- the official identifier when there is one; never invented
  colour      text,
  notes       text,
  status      text not null default 'alive' check (status in ('alive', 'sold', 'dead', 'lost')),
  created_at  timestamptz not null default now()
);
create index if not exists cattle_animals_owner_idx on cattle.animals (owner, created_at);

-- photos: stored in the Supabase bucket 'cattle-photos' under <owner>/<animal>/<id>.jpg; this row is the record
create table if not exists cattle.photos (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null references cattle.profiles (id) on delete cascade,
  animal      uuid not null references cattle.animals (id) on delete cascade,
  kind        text not null default 'side' check (kind in ('side', 'front', 'muzzle', 'other')),
  path        text not null,                               -- storage object path
  sha256      text not null,                               -- of the file, computed on the phone and checked on upload
  taken_at    timestamptz,                                 -- phone clock
  created_at  timestamptz not null default now()
);
create index if not exists cattle_photos_animal_idx on cattle.photos (animal, created_at);

-- events: append-only, hash-chained per animal
create table if not exists cattle.events (
  id          bigint generated always as identity primary key,
  owner       uuid not null references cattle.profiles (id) on delete cascade,
  animal      uuid references cattle.animals (id) on delete cascade,
  kind        text not null check (kind in ('registered', 'born', 'weaned', 'dipped', 'vaccinated', 'treated', 'sick_report', 'vet_reply', 'moved', 'sold', 'died', 'weighed', 'photo', 'correction', 'note')),
  at          timestamptz not null default now(),          -- when it happened (phone clock); created_at is when it was saved
  data        jsonb not null default '{}'::jsonb,
  source      text not null default 'app' check (source in ('app', 'whatsapp', 'recorder', 'vet')),
  prev_hash   text,
  hash        text not null,
  created_at  timestamptz not null default now()
);
create index if not exists cattle_events_animal_idx on cattle.events (animal, id);

-- WhatsApp binding: the app shows a six-digit code; the user sends it to the Zamai line from their own number;
-- the binding function finds the message in the line's table and writes profiles.phone. Codes expire after 15 minutes.
create table if not exists cattle.phone_codes (
  code        text primary key check (code ~ '^[0-9]{6}$'),
  profile     uuid not null references cattle.profiles (id) on delete cascade,
  created_at  timestamptz not null default now(),
  used_at     timestamptz
);

-- the hash chain, computed in the database so the app cannot skip it
create or replace function cattle.event_hash() returns trigger language plpgsql as $$
declare prev text;
begin
  select e.hash into prev from cattle.events e where e.animal is not distinct from new.animal order by e.id desc limit 1;
  new.prev_hash := prev;
  new.hash := encode(sha256(convert_to(coalesce(prev, '') || '|' || new.owner::text || '|' || coalesce(new.animal::text, '') || '|' || new.kind || '|' || new.at::text || '|' || new.data::text, 'utf8')), 'hex');
  return new;
end $$;
drop trigger if exists cattle_events_hash on cattle.events;
create trigger cattle_events_hash before insert on cattle.events for each row execute function cattle.event_hash();

-- no updates or deletes on events, by anyone but the service role
create or replace function cattle.no_change() returns trigger language plpgsql as $$
begin raise exception 'events are append-only; write a correction event'; end $$;
drop trigger if exists cattle_events_immutable on cattle.events;
create trigger cattle_events_immutable before update or delete on cattle.events for each row execute function cattle.no_change();

-- row-level security: the owner sees and writes only their own rows
alter table cattle.profiles    enable row level security;
alter table cattle.animals     enable row level security;
alter table cattle.photos      enable row level security;
alter table cattle.events      enable row level security;
alter table cattle.phone_codes enable row level security;
alter table cattle.terms       enable row level security;

create policy profiles_own   on cattle.profiles    for all    using (id = auth.uid()) with check (id = auth.uid());
create policy animals_own    on cattle.animals     for all    using (owner = auth.uid()) with check (owner = auth.uid());
create policy photos_own     on cattle.photos      for all    using (owner = auth.uid()) with check (owner = auth.uid());
create policy events_own_r   on cattle.events      for select using (owner = auth.uid());
create policy events_own_w   on cattle.events      for insert with check (owner = auth.uid());
create policy codes_own      on cattle.phone_codes for all    using (profile = auth.uid()) with check (profile = auth.uid());
create policy terms_read     on cattle.terms       for select using (true);

-- the phone column is written only by the binding function (service role): users cannot set it themselves
revoke update (phone, phone_bound_at) on cattle.profiles from authenticated;

-- expose the schema through the API
grant usage on schema cattle to anon, authenticated, service_role;
grant select on cattle.terms to anon, authenticated;
grant select, insert, update on cattle.profiles to authenticated;
grant select, insert, update on cattle.animals to authenticated;
grant select, insert on cattle.photos, cattle.events, cattle.phone_codes to authenticated;
grant all on all tables in schema cattle to service_role;
grant usage, select on all sequences in schema cattle to authenticated, service_role;

-- storage: private bucket, each user under their own folder
insert into storage.buckets (id, name, public) values ('cattle-photos', 'cattle-photos', false) on conflict do nothing;
create policy cattle_photos_own on storage.objects for all
  using (bucket_id = 'cattle-photos' and (storage.foldername(name))[1] = auth.uid()::text)
  with check (bucket_id = 'cattle-photos' and (storage.foldername(name))[1] = auth.uid()::text);

-- the first terms (English; the Tonga comes from a speaker)
insert into cattle.terms (version, en, current) values ('0.1', '{{TERMS_EN}}', true) on conflict (version) do nothing;
