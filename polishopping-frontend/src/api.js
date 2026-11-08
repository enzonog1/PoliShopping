// Endereço da API Django. Para mudar: crie .env com VITE_API_URL=https://seu-servidor/api
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function achatar(d) {
  if (!d) return "Erro de conexão com o servidor.";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map(achatar).join(" ");
  return Object.entries(d)
    .map(([k, v]) => (k === "detail" || k === "non_field_errors" ? "" : `${k}: `) + achatar(v))
    .join(" ");
}

export async function api(caminho, { method = "GET", body, params = {} } = {}) {
  const url = new URL(BASE + caminho);
  for (const [k, v] of Object.entries(params)) {
    for (const x of [].concat(v)) if (x !== "" && x != null) url.searchParams.append(k, x);
  }
  const token = localStorage.getItem("token");
  const ehForm = body instanceof FormData;   // upload de foto: o navegador define o Content-Type
  const headers = ehForm ? {} : { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Token ${token}`;
  let r;
  try {
    r = await fetch(url, { method, headers, body: body ? (ehForm ? body : JSON.stringify(body)) : undefined });
  } catch {
    throw new Error("Não foi possível falar com o servidor.");
  }
  const dados = r.status === 204 ? null : await r.json().catch(() => null);
  if (r.status === 401 && token) localStorage.removeItem("token");
  if (!r.ok) throw new Error(achatar(dados));
  return dados;
}
