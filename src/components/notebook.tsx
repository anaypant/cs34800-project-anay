import { addNote, deleteNote, saveName, toggleLike, updateNote } from "@/app/notebook-actions";
import type { NotebookState, TargetKind } from "@/lib/notebook";

export function Notebook({
  title,
  season,
  targetKind,
  targetId,
  state,
}: {
  title: string;
  season: number;
  targetKind: TargetKind;
  targetId: string;
  state: NotebookState;
}) {
  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="text-sm font-medium text-zinc-100">{title}</h3>
        <p className="text-xs text-zinc-500 tabular-nums">
          {state.likeCount} {state.likeCount === 1 ? "like" : "likes"}
        </p>
      </div>
      {state.viewerName ? (
        <div className="mt-3 flex flex-col gap-4">
          <form action={toggleLike}>
            <input type="hidden" name="season" value={season} />
            <input type="hidden" name="kind" value={targetKind} />
            <input type="hidden" name="target" value={targetId} />
            <button
              type="submit"
              className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-100 hover:border-zinc-500"
            >
              {state.liked ? "Unlike" : "Like"} {targetKind === "team" ? "this team" : "this player"}
            </button>
            <span className="ml-3 text-xs text-zinc-500">Signed in as {state.viewerName}</span>
          </form>
          <form action={addNote} className="flex flex-col gap-2">
            <input type="hidden" name="season" value={season} />
            <input type="hidden" name="kind" value={targetKind} />
            <input type="hidden" name="target" value={targetId} />
            <label className="text-xs font-medium tracking-wide text-zinc-400 uppercase" htmlFor={`note-${targetKind}-${targetId}`}>
              Note
              <textarea
                id={`note-${targetKind}-${targetId}`}
                name="body"
                required
                maxLength={500}
                rows={3}
                placeholder="What stood out in this season?"
                className="mt-1 block w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm font-normal normal-case tracking-normal text-zinc-100"
              />
            </label>
            <button
              type="submit"
              className="self-start rounded-md bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-950"
            >
              Save note
            </button>
          </form>
          <ul className="flex flex-col gap-3">
            {state.notes.map((note) => (
              <li key={note.noteId} className="rounded-md border border-zinc-800 px-3 py-2">
                <p className="text-xs text-zinc-500">
                  {note.displayName} · {note.updatedAt}
                </p>
                {note.mine ? (
                  <form action={updateNote} className="mt-2 flex flex-col gap-2">
                    <input type="hidden" name="note" value={note.noteId} />
                    <textarea
                      name="body"
                      required
                      maxLength={500}
                      rows={2}
                      defaultValue={note.body}
                      className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
                    />
                    <div className="flex gap-2">
                      <button type="submit" className="rounded-md border border-zinc-700 px-3 py-1 text-sm">
                        Update
                      </button>
                      <button
                        type="submit"
                        formAction={deleteNote}
                        className="rounded-md border border-zinc-800 px-3 py-1 text-sm text-zinc-400"
                      >
                        Delete
                      </button>
                    </div>
                  </form>
                ) : (
                  <p className="mt-1 text-sm text-zinc-200">{note.body}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <form action={saveName} className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end">
          <label className="block flex-1 text-xs font-medium tracking-wide text-zinc-400 uppercase">
            Your name
            <input
              name="name"
              required
              maxLength={40}
              placeholder="Name for likes and notes"
              className="mt-1 block w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm font-normal normal-case tracking-normal text-zinc-100"
            />
          </label>
          <button
            type="submit"
            className="rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950"
          >
            Start notebook
          </button>
        </form>
      )}
    </section>
  );
}
