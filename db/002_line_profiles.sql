-- 002 (7 Nov 2026): profiles made from the WhatsApp line, and their merge into an app profile.
-- Chris: "You can't just receive messages from linked numbers, that's not how this needs to be set up." A herder who
-- only has WhatsApp gets a profile the moment their first cattle message arrives (created_via 'line', phone set,
-- name from WhatsApp). When the same person later opens the app and ties the number, the app profile absorbs the
-- line profile: animals, photos and events move over; the line profile is deleted.
alter table cattle.profiles add column if not exists created_via text not null default 'app' check (created_via in ('app', 'line'));

-- events are append-only, except that a merge may re-own them: the merge function sets cattle.merge = on for itself
create or replace function cattle.no_change() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and current_setting('cattle.merge', true) = 'on' and new.owner <> old.owner
     and new.animal is not distinct from old.animal and new.kind = old.kind and new.at = old.at and new.data = old.data
     and new.hash = old.hash then
    return new;
  end if;
  raise exception 'events are append-only; write a correction event';
end $$;

create or replace function cattle.merge_line_profile(line_profile uuid, app_profile uuid) returns int
language plpgsql security definer set search_path = cattle, public as $$
declare moved int;
begin
  if not exists (select 1 from cattle.profiles where id = line_profile and created_via = 'line') then
    raise exception 'not a line profile';
  end if;
  if not exists (select 1 from cattle.profiles where id = app_profile) then
    raise exception 'no such app profile';
  end if;
  perform set_config('cattle.merge', 'on', true);
  update cattle.animals set owner = app_profile where owner = line_profile;
  update cattle.photos  set owner = app_profile where owner = line_profile;
  update cattle.events  set owner = app_profile where owner = line_profile;
  get diagnostics moved = row_count;
  update cattle.profiles set phone = null where id = line_profile;
  insert into cattle.events (owner, animal, kind, data, source)
    values (app_profile, null, 'note', jsonb_build_object('note', 'records from the WhatsApp line profile merged in', 'from', line_profile::text, 'events', moved), 'whatsapp');
  delete from cattle.profiles where id = line_profile;
  return moved;
end $$;
revoke all on function cattle.merge_line_profile(uuid, uuid) from public, anon, authenticated;
