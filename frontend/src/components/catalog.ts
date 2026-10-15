export type Row = { id: string; version: number; status: string; [key: string]: string | number | null };
export type Field = { name: string; label: string; type?: string; optional?: boolean; source?: string; immutable?: boolean; max?: number };
export type Catalog = { title: string; singular: string; description: string; fields: Field[] };
export const roles: Record<string, string> = { ADMIN: "Administrador", COORDINATOR: "Coordinador", TEACHER: "Docente", VIEWER: "Consulta", TECHNICAL: "Técnico" };
export const catalogs: Record<string, Catalog> = {
  "academic-years": { title: "Años escolares", singular: "año escolar", description: "Define el período al que pertenecen las secciones y las matrículas.", fields: [
    { name: "name", label: "Nombre", max: 100 }, { name: "start_date", label: "Fecha inicial", type: "date" }, { name: "end_date", label: "Fecha final", type: "date" }] },
  courses: { title: "Cursos", singular: "curso", description: "Organiza los niveles de tu institución antes de crear sus secciones.", fields: [
    { name: "name", label: "Nombre", max: 100 }, { name: "grade_level", label: "Grado", max: 50 }] },
  sections: { title: "Secciones", singular: "sección", description: "Cada sección pertenece a un curso y un año escolar.", fields: [
    { name: "name", label: "Nombre", max: 80 }, { name: "course_id", label: "Curso", source: "courses", immutable: true }, { name: "academic_year_id", label: "Año escolar", source: "academic-years", immutable: true }] },
  students: { title: "Estudiantes", singular: "estudiante", description: "Conserva un registro por estudiante y su historial de matrículas.", fields: [
    { name: "full_name", label: "Nombre completo", max: 160 }, { name: "student_code", label: "Código del estudiante", optional: true, max: 50 }] },
  enrollments: { title: "Matrículas", singular: "matrícula", description: "Vincula estudiantes con sus secciones. Los traslados conservan la matrícula anterior.", fields: [
    { name: "student_id", label: "Estudiante", source: "students", immutable: true }, { name: "section_id", label: "Sección", source: "sections", immutable: true }, { name: "start_date", label: "Fecha inicial", type: "date" }, { name: "end_date", label: "Fecha final", type: "date", optional: true }] },
  "teaching-assignments": { title: "Asignaciones docentes", singular: "asignación docente", description: "Los docentes consultan únicamente los grupos que tienen asignados.", fields: [
    { name: "teacher_id", label: "Docente", source: "members", immutable: true }, { name: "section_id", label: "Sección", source: "sections", immutable: true }, { name: "academic_year_id", label: "Año escolar", source: "academic-years", immutable: true }, { name: "subject", label: "Asignatura", max: 100 }] },
  members: { title: "Equipo y permisos", singular: "miembro", description: "Asigna un rol por institución. Para vincular una cuenta existente, deja la contraseña inicial vacía.", fields: [
    { name: "full_name", label: "Nombre completo", max: 160 }, { name: "email", label: "Correo electrónico", type: "email", max: 254 }, { name: "role", label: "Rol", source: "roles" }, { name: "initial_password", label: "Contraseña inicial", type: "password", optional: true, max: 128 }] },
};
export function label(row: Row): string { return String(row.full_name ?? row.name ?? row.subject ?? row.id); }
