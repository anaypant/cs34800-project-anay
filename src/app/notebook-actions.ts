"use server";

import { revalidatePath } from "next/cache";
import { query } from "@/lib/db";
import { rememberViewer, viewerId, type TargetKind } from "@/lib/notebook";

function cleanName(value: FormDataEntryValue | null): string | null {
  if (typeof value !== "string") return null;
  const name = value.trim().replace(/\s+/g, " ");
  if (name.length < 1 || name.length > 40) return null;
  return name;
}

function cleanBody(value: FormDataEntryValue | null): string | null {
  if (typeof value !== "string") return null;
  const body = value.trim().replace(/\s+/g, " ");
  if (body.length < 1 || body.length > 500) return null;
  return body;
}

function targetFrom(formData: FormData): { season: number; kind: TargetKind; id: string } | null {
  const season = Number(formData.get("season"));
  const kind = formData.get("kind");
  const id = formData.get("target");
  if (!Number.isInteger(season) || (kind !== "team" && kind !== "player") || typeof id !== "string") {
    return null;
  }
  if (kind === "team" && !/^[A-Z]{2,3}$/.test(id)) return null;
  if (kind === "player" && !/^[A-Za-z0-9-]{1,40}$/.test(id)) return null;
  return { season, kind, id };
}

export async function saveName(formData: FormData) {
  const name = cleanName(formData.get("name"));
  if (!name) return;
  const rows = await query<{ user_id: string }>(
    "insert into notebook_user (display_name) values ($1) returning user_id::text",
    [name],
  );
  const userId = rows[0]?.user_id;
  if (!userId) return;
  await rememberViewer(userId);
  revalidatePath("/");
}

export async function toggleLike(formData: FormData) {
  const userId = await viewerId();
  const target = targetFrom(formData);
  if (!userId || !target) return;
  await query(
    `with removed as (
       delete from saved_pick
       where user_id = $1 and season = $2 and target_kind = $3 and target_id = $4
       returning pick_id
     )
     insert into saved_pick (user_id, season, target_kind, target_id)
     select $1, $2, $3, $4
     where not exists (select 1 from removed)`,
    [userId, target.season, target.kind, target.id],
  );
  revalidatePath("/");
}

export async function addNote(formData: FormData) {
  const userId = await viewerId();
  const target = targetFrom(formData);
  const body = cleanBody(formData.get("body"));
  if (!userId || !target || !body) return;
  await query(
    `insert into note (user_id, season, target_kind, target_id, body)
     values ($1, $2, $3, $4, $5)`,
    [userId, target.season, target.kind, target.id, body],
  );
  revalidatePath("/");
}

export async function updateNote(formData: FormData) {
  const userId = await viewerId();
  const noteId = formData.get("note");
  const body = cleanBody(formData.get("body"));
  if (!userId || typeof noteId !== "string" || !/^\d+$/.test(noteId) || !body) return;
  await query(
    `update note
     set body = $3, updated_at = now()
     where note_id = $1 and user_id = $2`,
    [noteId, userId, body],
  );
  revalidatePath("/");
}

export async function deleteNote(formData: FormData) {
  const userId = await viewerId();
  const noteId = formData.get("note");
  if (!userId || typeof noteId !== "string" || !/^\d+$/.test(noteId)) return;
  await query("delete from note where note_id = $1 and user_id = $2", [noteId, userId]);
  revalidatePath("/");
}
