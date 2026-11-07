-- 003 (7 Nov 2026): closing a profile (erasure), and the record that an erasure happened.
-- The append-only guard on events admits a DELETE only inside cattle.close_profile, which sets cattle.erase = on for
-- itself. The function removes the person's events, photos rows, animals, codes and profile; the storage objects and
-- the auth user are removed by the admin function that calls it (storage API, auth admin API). What stays is one row
-- in cattle.erasures: when, which profile id, how many rows, no name, no number.
create table if not exists cattle.erasures (
  id        bigserial primary key,
  at        timestamptz not null default now(),
  profile   uuid not null,
  animals   int not null,
  events    int not null,
  photos    int not null,
  note      text
);

create or replace function cattle.no_change() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and current_setting('cattle.merge', true) = 'on' and new.owner <> old.owner
     and new.animal is not distinct from old.animal and new.kind = old.kind and new.at = old.at and new.data = old.data
     and new.hash = old.hash then
    return new;
  end if;
  if tg_op = 'DELETE' and current_setting('cattle.erase', true) = 'on' then
    return old;
  end if;
  raise exception 'events are append-only; write a correction event';
end $$;

create or replace function cattle.close_profile(p uuid, why text) returns jsonb
language plpgsql security definer set search_path = cattle, public as $$
declare na int; ne int; np int;
begin
  if not exists (select 1 from cattle.profiles where id = p) then
    raise exception 'no such profile';
  end if;
  perform set_config('cattle.erase', 'on', true);
  select count(*) into na from cattle.animals where owner = p;
  select count(*) into ne from cattle.events  where owner = p;
  select count(*) into np from cattle.photos  where owner = p;
  delete from cattle.events      where owner = p;
  delete from cattle.photos      where owner = p;
  delete from cattle.animals     where owner = p;
  delete from cattle.phone_codes where profile = p;
  delete from cattle.profiles    where id = p;
  insert into cattle.erasures (profile, animals, events, photos, note) values (p, na, ne, np, why);
  return jsonb_build_object('animals', na, 'events', ne, 'photos', np);
end $$;
revoke all on function cattle.close_profile(uuid, text) from public, anon, authenticated;

-- grants for the service role (the admin function and the watcher use it)
grant select on cattle.erasures to service_role;
grant execute on function cattle.close_profile(uuid, text) to service_role;
grant execute on function cattle.merge_line_profile(uuid, uuid) to service_role;
