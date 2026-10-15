import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
const resource = /^(auth\/(login|logout|me|password)|institutions(\/[a-f0-9-]+(\/members(\/[a-f0-9-]+)?)?)?|academic-years(\/[a-f0-9-]+)?|courses(\/[a-f0-9-]+)?|sections(\/[a-f0-9-]+)?|students(\/[a-f0-9-]+)?|enrollments(\/[a-f0-9-]+(\/transfer)?)?|teaching-assignments(\/[a-f0-9-]+)?|audit-events)$/;
const responseHeaders = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const failure = (status: number, detail: string) => Response.json({ detail }, { status, headers: responseHeaders });

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const route = path.join("/");
  if (!resource.test(route)) return failure(404, "Recurso no disponible");
  const origin = process.env.API_INTERNAL_URL;
  if (!origin) return failure(503, "Servicio no disponible; vuelve a intentar");
  const headers = new Headers();
  for (const name of ["cookie", "origin", "x-csrf-token", "x-institution-id", "content-type"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const writing = !["GET", "HEAD"].includes(request.method);
  // El backend verifica su lista explícita de orígenes; aquí no se confía en Host reenviado.
  let body: Uint8Array | undefined;
  if (writing && request.body) {
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const next = await reader.read();
      if (next.done) break;
      size += next.value.length;
      if (size > 65536) { await reader.cancel(); return failure(413, "La solicitud es demasiado grande"); }
      chunks.push(next.value);
    }
    body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.length; }
  }
  try {
    const upstream = await fetch(`${origin}/api/v1/${route}${request.nextUrl.search}`, {
      method: request.method, headers, body: body as BodyInit | undefined,
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(10000),
    });
    const outgoing = new Headers(responseHeaders);
    outgoing.set("Content-Type", upstream.headers.get("content-type") ?? "application/json");
    for (const cookie of upstream.headers.getSetCookie()) outgoing.append("Set-Cookie", cookie);
    const retry = upstream.headers.get("retry-after");
    if (retry) outgoing.set("Retry-After", retry);
    return new Response(upstream.status === 204 ? null : upstream.body, { status: upstream.status, headers: outgoing });
  } catch { return failure(503, "No se pudo conectar con el servicio. Vuelve a intentar."); }
}
export { proxy as GET, proxy as POST, proxy as PATCH };
