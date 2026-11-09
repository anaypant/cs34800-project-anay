import { Pool } from "pg";

const globalForPg = globalThis as typeof globalThis & { nflPool?: Pool };

export function getPool(): Pool {
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error("DATABASE_URL is not set");
  }
  if (!globalForPg.nflPool) {
    // node-pg treats sslmode=require as full certificate verification. The pooler
    // certificate is not in Node's trust store, so verification is turned off here.
    const url = new URL(connectionString);
    url.searchParams.delete("sslmode");
    globalForPg.nflPool = new Pool({
      connectionString: url.toString(),
      max: 4,
      ssl: { rejectUnauthorized: false },
    });
  }
  return globalForPg.nflPool;
}

export async function query<T extends Record<string, unknown>>(
  text: string,
  params: unknown[] = [],
): Promise<T[]> {
  const result = await getPool().query(text, params);
  return result.rows as T[];
}
