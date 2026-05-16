export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error("Request failed");
  return (await res.json()) as T;
}
