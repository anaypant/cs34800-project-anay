import { cookies } from "next/headers";
import { query } from "@/lib/db";

export type TargetKind = "team" | "player";

export type NotebookNote = {
  noteId: string;
  body: string;
  displayName: string;
  mine: boolean;
  updatedAt: string;
};

export type NotebookState = {
  viewerName: string | null;
  likeCount: number;
  liked: boolean;
  notes: NotebookNote[];
};

const cookieName = "notebook_user";

export async function viewerId(): Promise<string | null> {
  const value = (await cookies()).get(cookieName)?.value ?? "";
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)
    ? value
    : null;
}

export async function rememberViewer(userId: string) {
  const jar = await cookies();
  jar.set(cookieName, userId, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    secure: process.env.NODE_ENV === "production",
  });
}

export async function viewerName(userId: string | null): Promise<string | null> {
  if (!userId) return null;
  const rows = await query<{ display_name: string }>(
    "select display_name from notebook_user where user_id = $1",
    [userId],
  );
  return rows[0]?.display_name ?? null;
}

export async function notebookFor(
  season: number,
  targetKind: TargetKind,
  targetId: string,
  userId: string | null,
): Promise<NotebookState> {
  const [counts, notes, name] = await Promise.all([
    query<{ likes: number; liked: boolean }>(
      `select count(*)::int as likes,
              coalesce(bool_or(user_id = $4::uuid), false) as liked
       from saved_pick
       where season = $1 and target_kind = $2 and target_id = $3`,
      [season, targetKind, targetId, userId],
    ),
    query<{ note_id: string; body: string; display_name: string; mine: boolean; updated_at: Date }>(
      `select n.note_id::text as note_id,
              n.body,
              u.display_name,
              (u.user_id = $4::uuid) as mine,
              n.updated_at
       from note n
       join notebook_user u on u.user_id = n.user_id
       where n.season = $1 and n.target_kind = $2 and n.target_id = $3
       order by n.created_at desc`,
      [season, targetKind, targetId, userId],
    ),
    viewerName(userId),
  ]);
  return {
    viewerName: name,
    likeCount: counts[0]?.likes ?? 0,
    liked: counts[0]?.liked ?? false,
    notes: notes.map((note) => ({
      noteId: note.note_id,
      body: note.body,
      displayName: note.display_name,
      mine: note.mine,
      updatedAt: new Date(note.updated_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }),
    })),
  };
}
