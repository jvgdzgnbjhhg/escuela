"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { catalogs, Field, label, roles, Row } from "./catalog";

type Session = { user: { full_name: string }; institutions: { id: string; name: string; role: string }[]; csrf_token: string };
type Page = { items: Row[]; total: number };
type Api = <T>(path: string, method?: string, data?: unknown) => Promise<T>;
class ApiError extends Error { constructor(message: string, public status: number) { super(message); } }
async function request<T>(path: string, method = "GET", data?: unknown, csrf?: string, tenant?: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1/${path}`, { method, cache: "no-store", credentials: "same-origin",
      headers: { ...(data ? { "Content-Type": "application/json" } : {}), ...(csrf ? { "X-CSRF-Token": csrf } : {}), ...(tenant ? { "X-Institution-ID": tenant } : {}) },
      body: data ? JSON.stringify(data) : undefined });
  } catch { throw new ApiError("Sin conexión. Conserva el formulario y vuelve a intentar.", 0); }
  if (response.status === 204) return undefined as T;
  const body = await response.json();
  if (!response.ok) throw new ApiError(typeof body.detail === "string" ? body.detail : "Revisa los campos y sus fechas antes de guardar.", response.status);
  return body as T;
}
const message = (error: unknown) => error instanceof Error ? error.message : "No se pudo completar la operación.";

export default function Workspace() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tenant, setTenant] = useState("");
  const [tab, setTab] = useState("students");
  const [account, setAccount] = useState(false);
  const [institutionEditor, setInstitutionEditor] = useState(false);
  const generation = useRef(0);
  const login = useForm<{ email: string; password: string }>();
  const refresh = useCallback(async () => {
    try {
      const value = await request<Session>("auth/me");
      setSession(value); setTenant(value.institutions[0]?.id ?? ""); setError("");
    } catch (e) { if (!(e instanceof ApiError && e.status === 401)) setError(message(e)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    let active = true;
    request<Session>("auth/me").then(value => {
      if (active) { setSession(value); setTenant(value.institutions[0]?.id ?? ""); }
    }).catch(e => {
      if (active && !(e instanceof ApiError && e.status === 401)) setError(message(e));
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const api = useCallback<Api>(async (path, method, data) => {
    const current = generation.current;
    try { return await request(path, method, data, session?.csrf_token, tenant); }
    catch (e) {
      if (current === generation.current && e instanceof ApiError && e.status === 401) {
        setSession(null); setTenant(""); setError("La sesión terminó. Vuelve a iniciar sesión."); generation.current++;
      }
      throw e;
    }
  }, [session, tenant]);
  const institution = session?.institutions.find(item => item.id === tenant);
  const admin = institution?.role === "ADMIN";
  return <div className="workspace">
    <header className="masthead"><Link className="brand" href="/" aria-label="Evaluación académica, inicio"><span className="brand-mark" aria-hidden="true">ea</span><span>Evaluación académica</span></Link>
      {session && <div className="account-actions"><span>{session.user.full_name}</span><button onClick={() => setAccount(!account)}>Mi cuenta</button><button onClick={async () => {
        try { await api("auth/logout", "POST"); generation.current++; setSession(null); setTenant(""); setAccount(false); setError(""); }
        catch (e) { setError(message(e)); }
      }}>Cerrar sesión</button></div>}
    </header>
    {error && <p className="error" role="alert">{error}</p>}
    {loading ? <main className="admin-main"><p role="status">Comprobando acceso…</p></main> : !session ?
      <main id="contenido"><div className="intro"><h1>Cada avance<br />cuenta.</h1><p className="lead">Tu centro, tus grupos y el aprendizaje de cada estudiante.</p></div>
        <section className="notice" aria-labelledby="access-title"><h2 id="access-title">Entra a tu espacio</h2>
          <form className="data-form" onSubmit={login.handleSubmit(async values => {
            setError("");
            try { await request("auth/login", "POST", values); login.reset(); await refresh(); }
            catch (e) { setError(message(e)); }
          })}><label>Correo electrónico<input type="email" autoComplete="username" required {...login.register("email")} /></label>
          <label>Contraseña<input type="password" autoComplete="current-password" required maxLength={128} {...login.register("password")} /></label>
          <button className="primary" disabled={login.formState.isSubmitting}>{login.formState.isSubmitting ? "Entrando…" : "Iniciar sesión"}</button></form>
          <p className="help">Solicita acceso al administrador de tu centro.</p>
        </section></main> : <main className="admin-main" id="contenido">
        <div className="context-bar"><label>Institución<select value={tenant} onChange={e => { generation.current++; setTenant(e.target.value); setTab("students"); setError(""); }}>
          {session.institutions.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
        </select></label><span className="role">{institution ? roles[institution.role] : "Sin institución asignada"}</span>
          {admin && <button onClick={() => setInstitutionEditor(!institutionEditor)}>Gestionar institución</button>}</div>
        {institutionEditor && admin && institution && <InstitutionForm key={tenant} name={institution.name} api={api} tenant={tenant} onDone={async () => { setInstitutionEditor(false); const value = await api<Session>("auth/me"); setSession(value); }} /> }
        {account && <PasswordForm api={api} onDone={() => { generation.current++; setSession(null); setAccount(false); setTenant(""); setError("Contraseña actualizada. Inicia sesión de nuevo."); }} />}
        {!institution ? <p>Tu cuenta no tiene una institución activa. Contacta al administrador.</p> : institution.role === "TECHNICAL" ? <p>Tu rol técnico no tiene acceso al contenido académico.</p> : <>
          <nav className="tabs" aria-label="Gestión académica">{Object.entries(catalogs).filter(([key]) => key !== "members" || admin).map(([key, value]) => <button key={key} aria-current={tab === key ? "page" : undefined} onClick={() => setTab(key)}>{value.title}</button>)}</nav>
          <CatalogView key={`${tenant}:${tab}`} resource={tab} api={api} tenant={tenant} admin={admin} />
        </>}
      </main>}
    <footer>Plataforma de Evaluación Académica<span>Gestión institucional</span></footer>
  </div>;
}

function PasswordForm({ api, onDone }: { api: Api; onDone: () => void }) {
  const form = useForm<{ current_password: string; new_password: string }>();
  const [error, setError] = useState("");
  return <section className="editor"><h2>Cambiar contraseña</h2><form className="data-form" onSubmit={form.handleSubmit(async values => {
    try { await api("auth/password", "POST", values); form.reset(); onDone(); } catch (e) { setError(message(e)); }
  })}>
    <label>Contraseña actual<input type="password" autoComplete="current-password" required {...form.register("current_password")} /></label>
    <label>Nueva contraseña<input type="password" autoComplete="new-password" minLength={12} maxLength={128} required {...form.register("new_password")} /></label>
    {error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={form.formState.isSubmitting}>Cambiar contraseña</button>
  </form></section>;
}

function CatalogView({ resource, api, tenant, admin }: { resource: string; api: Api; tenant: string; admin: boolean }) {
  const config = catalogs[resource];
  const path = resource === "members" ? `institutions/${tenant}/members` : resource;
  const [page, setPage] = useState<Page | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [revision, setRevision] = useState(0);
  const [editing, setEditing] = useState<Row | "new" | null>(null);
  const [transfer, setTransfer] = useState<Row | null>(null);
  const [lookups, setLookups] = useState<Record<string, Row[]>>({});
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const result = await api<Page>(`${path}?limit=25&offset=${offset}&q=${encodeURIComponent(query)}`);
        const sources = [...new Set(config.fields.map(f => f.source).filter((s): s is string => Boolean(s) && s !== "roles" && (s !== "members" || admin)))];
        const entries = await Promise.all(sources.map(async source => {
          const url = source === "members" ? `institutions/${tenant}/members` : source;
          const values: Row[] = [];
          // Paginar también los selectores: no ocultar registros tras los primeros 200.
          let start = 0;
          while (true) {
            const batch = await api<Page>(`${url}?limit=200&offset=${start}`);
            values.push(...batch.items); start += batch.items.length;
            if (start >= batch.total || batch.items.length === 0 || !active) break;
          }
          return [source, values] as const;
        }));
        if (active) { setPage(result); setLookups(Object.fromEntries(entries)); setError(""); }
      } catch (e) { if (active) setError(message(e)); }
    }
    void load();
    return () => { active = false; };
  }, [api, path, offset, query, revision, config, tenant, admin]);
  function reload() { setPage(null); setRevision(v => v + 1); }
  function display(field: Field, value: Row[string]) {
    if (field.name === "initial_password") return "";
    if (field.source === "roles") return roles[String(value)];
    const found = field.source && lookups[field.source]?.find(r => (field.source === "members" ? r.user_id : r.id) === value);
    return found ? label(found) : value ? String(value) : "—";
  }
  return <section className="catalog" aria-labelledby="catalog-title"><div className="catalog-heading"><div><h1 id="catalog-title">{config.title}</h1><p>{config.description}</p></div>
    {admin && <button className="primary" disabled={busy || editing !== null || transfer !== null} onClick={() => { setEditing("new"); setNotice(""); }}>Crear {config.singular}</button>}</div>
    {error && <p role="alert" className="error">{error} <button onClick={reload}>Volver a intentar</button></p>}
    {notice && <p role="status" className="success">{notice}</p>}
    {editing && <RecordForm key={editing === "new" ? "new" : editing.id} resource={resource} row={editing === "new" ? null : editing} lookups={lookups} onCancel={() => setEditing(null)} onSave={async values => {
      await api(editing === "new" ? path : `${path}/${editing.id}`, editing === "new" ? "POST" : "PATCH", values);
      setEditing(null); setNotice("Registro guardado."); reload();
    }} />}
    {transfer && <TransferForm row={transfer} sections={lookups.sections ?? []} onCancel={() => setTransfer(null)} onSave={async values => {
      await api(`enrollments/${transfer.id}/transfer`, "POST", values); setTransfer(null); setNotice("Traslado registrado. Se conservó la matrícula anterior."); reload();
    }} />}
    {["students", "courses", "sections", "academic-years"].includes(resource) && <form className="search" onSubmit={e => { e.preventDefault(); setPage(null); setOffset(0); setQuery(search); setRevision(v => v + 1); }}><label>Buscar por nombre<input type="search" maxLength={100} value={search} onChange={e => setSearch(e.target.value)} /></label><button>Buscar</button></form>}
    {!page ? <p role="status">Cargando registros…</p> : page.items.length === 0 ? <div className="empty"><h2>{query ? "Sin coincidencias" : `Todavía no hay ${config.title.toLowerCase()}`}</h2><p>{query ? "Prueba con otro nombre." : admin ? `Usa «Crear ${config.singular}» para comenzar.` : "Los registros aparecerán cuando el administrador los asigne."}</p></div> :
      <div className="table-scroll"><table><caption className="sr-only">{config.title}</caption><thead><tr>{config.fields.filter(f => f.type !== "password").map(f => <th key={f.name} scope="col">{f.label}</th>)}<th scope="col">Estado</th>{admin && <th scope="col">Acciones</th>}</tr></thead>
      <tbody>{page.items.map(row => <tr key={row.id}>{config.fields.filter(f => f.type !== "password").map(f => <td key={f.name}>{display(f, row[f.name])}</td>)}<td><span className={`badge ${row.status === "ACTIVE" ? "active" : ""}`}>{row.status === "ACTIVE" ? "Activo" : row.status === "REVOKED" ? "Revocado" : "Archivado"}</span></td>
        {admin && <td><div className="row-actions"><button disabled={busy || editing !== null || transfer !== null} onClick={() => { setEditing(row); setNotice(""); }}>Editar</button>
        {resource === "enrollments" && row.status === "ACTIVE" && <button disabled={busy || editing !== null || transfer !== null} onClick={() => setTransfer(row)}>Trasladar</button>}
        {resource !== "members" && row.status === "ACTIVE" && <button disabled={busy || editing !== null || transfer !== null} onClick={async () => {
          if (!window.confirm(`¿Archivar este registro de ${config.singular}? Su historial se conservará.`)) return;
          setBusy(true); setError("");
          try { const values = Object.fromEntries(config.fields.map(f => [f.name, row[f.name]])); await api(`${path}/${row.id}`, "PATCH", { ...values, status: "ARCHIVED", version: row.version }); setNotice("Registro archivado."); reload(); }
          catch (e) { setError(message(e)); } finally { setBusy(false); }
        }}>Archivar</button>}</div></td>}
      </tr>)}</tbody></table></div>}
    {page && <div className="pagination"><span>{page.total} registros</span><button disabled={offset === 0 || busy} onClick={() => { setPage(null); setOffset(Math.max(0, offset - 25)); }}>Anterior</button><button disabled={offset + 25 >= page.total || busy} onClick={() => { setPage(null); setOffset(offset + 25); }}>Siguiente</button></div>}
  </section>;
}

function RecordForm({ resource, row, lookups, onSave, onCancel }: { resource: string; row: Row | null; lookups: Record<string, Row[]>; onSave: (values: unknown) => Promise<void>; onCancel: () => void }) {
  const config = catalogs[resource];
  const fields = resource === "members" && row ? config.fields.filter(f => f.name === "role") : config.fields;
  const defaults = Object.fromEntries(fields.map(f => [f.name, String(row?.[f.name] ?? "")]));
  if (row) defaults.status = row.status;
  const form = useForm<Record<string, string>>({ defaultValues: defaults });
  const [error, setError] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);
  return <section className="editor"><h2 ref={heading} tabIndex={-1}>{row ? "Editar" : "Crear"} {config.singular}</h2><form className="data-form" onSubmit={form.handleSubmit(async values => {
    setError("");
    const rules: Record<string, z.ZodType> = {};
    for (const field of fields) {
      let rule = z.string().max(field.max ?? 254);
      if (!field.optional) rule = rule.min(1, `Completa ${field.label.toLowerCase()}.`);
      rules[field.name] = rule;
    }
    const valid = z.object(rules).safeParse(values);
    if (!valid.success) { setError(valid.error.issues[0].message); return; }
    const payload: Record<string, unknown> = { ...valid.data };
    for (const field of fields) if (field.optional && payload[field.name] === "") payload[field.name] = null;
    if (row) { payload.version = row.version; payload.status = values.status; }
    try { await onSave(payload); } catch (e) { setError(message(e)); }
  })}>
    {fields.map(field => <label key={field.name}>{field.label}{field.optional && <span className="optional"> (opcional)</span>}
      {field.source ? <select {...form.register(field.name)} required={!field.optional} aria-readonly={Boolean(row && field.immutable)}>
        {!(row && field.immutable) && <option value="">Selecciona una opción</option>}
        {field.source === "roles" ? Object.entries(roles).map(([value, name]) => <option key={value} value={value}>{name}</option>) : (lookups[field.source] ?? []).filter(item => row && field.immutable ? (field.source === "members" ? item.user_id : item.id) === row[field.name] : item.status === "ACTIVE" && (field.source !== "members" || item.role === "TEACHER")).map(item => <option key={item.id} value={String(field.source === "members" ? item.user_id : item.id)}>{label(item)}</option>)}
      </select> : <input {...form.register(field.name)} type={field.type ?? "text"} required={!field.optional} maxLength={field.max} minLength={field.type === "password" ? 12 : undefined} autoComplete={field.type === "password" ? "new-password" : "off"} />}
    </label>)}
    {row && <label>Estado<select {...form.register("status")}><option value="ACTIVE">Activo</option><option value={resource === "members" ? "REVOKED" : "ARCHIVED"}>{resource === "members" ? "Revocado" : "Archivado"}</option></select></label>}
    {error && <p className="error" role="alert">{error}</p>}<div className="form-actions"><button className="primary" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Guardando…" : "Guardar"}</button><button type="button" disabled={form.formState.isSubmitting} onClick={onCancel}>Cancelar</button></div>
  </form></section>;
}
function TransferForm({ row, sections, onSave, onCancel }: { row: Row; sections: Row[]; onSave: (values: unknown) => Promise<void>; onCancel: () => void }) {
  const form = useForm<{ section_id: string; start_date: string }>();
  const [error, setError] = useState("");
  return <section className="editor"><h2>Trasladar estudiante</h2><form className="data-form" onSubmit={form.handleSubmit(async values => {
    try { await onSave({ ...values, version: row.version }); } catch (e) { setError(message(e)); }
  })}><label>Sección de destino<select required {...form.register("section_id")}><option value="">Selecciona una sección</option>{sections.filter(s => s.status === "ACTIVE" && s.id !== row.section_id).map(s => <option key={s.id} value={s.id}>{label(s)}</option>)}</select></label>
    <label>Fecha del traslado<input type="date" required {...form.register("start_date")} /></label>{error && <p role="alert" className="error">{error}</p>}<div className="form-actions"><button className="primary" disabled={form.formState.isSubmitting}>Registrar traslado</button><button type="button" disabled={form.formState.isSubmitting} onClick={onCancel}>Cancelar</button></div></form></section>;
}

function InstitutionForm({ name, api, tenant, onDone }: { name: string; api: Api; tenant: string; onDone: () => Promise<void> }) {
  const form = useForm<{ name: string; mode: string }>({ defaultValues: { name, mode: "rename" } });
  const [error, setError] = useState("");
  return <section className="editor"><h2>Gestionar institución</h2><form className="data-form" onSubmit={form.handleSubmit(async values => {
    try { await api(values.mode === "create" ? "institutions" : `institutions/${tenant}`, values.mode === "create" ? "POST" : "PATCH", { name: values.name }); await onDone(); }
    catch (e) { setError(message(e)); }
  })}>
    <label>Operación<select {...form.register("mode")}><option value="rename">Renombrar institución actual</option><option value="create">Crear otra institución</option></select></label>
    <label>Nombre de la institución<input required maxLength={160} {...form.register("name")} /></label>
    {error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={form.formState.isSubmitting}>Guardar institución</button>
  </form></section>;
}
