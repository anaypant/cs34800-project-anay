-- Alteration applied with SQL after the warehouse load.
-- The NFL fact tables stay read-only. These tables are the rows a person inserts,
-- updates, and deletes: a name, a like, and a note on one team or one player.

create table notebook_user (
  user_id uuid primary key default gen_random_uuid(),
  display_name text not null check (char_length(btrim(display_name)) between 1 and 40),
  created_at timestamptz not null default now()
);

create table saved_pick (
  pick_id bigint generated always as identity primary key,
  user_id uuid not null references notebook_user (user_id) on delete cascade,
  season integer not null,
  target_kind text not null check (target_kind in ('team', 'player')),
  target_id text not null,
  created_at timestamptz not null default now(),
  unique (user_id, season, target_kind, target_id)
);

create table note (
  note_id bigint generated always as identity primary key,
  user_id uuid not null references notebook_user (user_id) on delete cascade,
  season integer not null,
  target_kind text not null check (target_kind in ('team', 'player')),
  target_id text not null,
  body text not null check (char_length(btrim(body)) between 1 and 500),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index saved_pick_user_idx on saved_pick (user_id);
create index saved_pick_target_idx on saved_pick (season, target_kind, target_id);
create index note_user_idx on note (user_id);
create index note_target_idx on note (season, target_kind, target_id);

create or replace function assert_notebook_target()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  -- A foreign key would lock the season row, and the read-only warehouse rejects
  -- that lock. A plain lookup keeps the NFL tables unchanged.
  if not exists (select 1 from seasons where season = new.season) then
    raise exception 'unknown season';
  end if;
  if new.target_kind = 'team' then
    if not exists (
      select 1 from v_team_reg
      where season = new.season and team_abbr = new.target_id
    ) then
      raise exception 'that team did not play in this season';
    end if;
  elsif new.target_kind = 'player' then
    if not exists (
      select 1 from v_player_reg
      where season = new.season and player_id = new.target_id
    ) then
      raise exception 'that player did not play in this season';
    end if;
  else
    raise exception 'unknown notebook target';
  end if;
  return new;
end;
$$;

create trigger saved_pick_target
  before insert on saved_pick
  for each row execute function assert_notebook_target();

create trigger note_target
  before insert or update of season, target_kind, target_id on note
  for each row execute function assert_notebook_target();

alter table notebook_user enable row level security;
alter table saved_pick enable row level security;
alter table note enable row level security;
alter table notebook_user force row level security;
alter table saved_pick force row level security;
alter table note force row level security;

create policy notebook_user_read on notebook_user for select using (true);
create policy notebook_user_insert on notebook_user for insert to nfl_app with check (true);
create policy notebook_user_delete on notebook_user for delete to nfl_app using (true);
create policy saved_pick_read on saved_pick for select using (true);
create policy saved_pick_insert on saved_pick for insert to nfl_app with check (true);
create policy saved_pick_delete on saved_pick for delete to nfl_app using (true);
create policy note_read on note for select using (true);
create policy note_insert on note for insert to nfl_app with check (true);
create policy note_update on note for update to nfl_app using (true) with check (true);
create policy note_delete on note for delete to nfl_app using (true);

revoke all on notebook_user, saved_pick, note from public, anon, authenticated;
grant select on notebook_user, saved_pick, note to anon, authenticated;
revoke all on function assert_notebook_target() from public, anon, authenticated;
