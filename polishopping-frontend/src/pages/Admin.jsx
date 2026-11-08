import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { ACOES, MODALIDADES, MOTIVOS, Paginacao, campo, reais, rotulo } from "../componentes.jsx";

// MOD001: fila de moderação
export function Moderacao() {
  const [dados, setDados] = useState(null);
  const [pagina, setPagina] = useState(1);
  const [sel, setSel] = useState({});
  const [erro, setErro] = useState("");
  const carregar = () => api("/denuncias/", { params: { status: "aberta", page: pagina } }).then(setDados).catch((x) => setErro(x.message));
  useEffect(() => { carregar(); }, [pagina]);

  const mudar = (id, k, v) => setSel({ ...sel, [id]: { tipo: "rejeitar", justificativa: "", ...sel[id], [k]: v } });
  const decidir = async (d) => {
    const s = { tipo: "rejeitar", justificativa: "", ...sel[d.id] };
    setErro("");
    try { await api("/moderacao/", { method: "POST", body: { denuncia: d.id, ...s } }); carregar(); }
    catch (x) { setErro(x.message); }
  };
  return (
    <>
      <h1>Fila de moderação</h1>
      {erro && <p className="erro">{erro}</p>}
      {dados && dados.results.length === 0 && <p>Nenhuma denúncia pendente.</p>}
      {dados?.results.map((d) => (
        <div className="card" key={d.id}>
          <p><Link to={`/anuncios/${d.anuncio}`}><b>{d.anuncio_titulo}</b></Link> · {rotulo(MOTIVOS, d.motivo)}</p>
          <p className="mut">{d.detalhamento}</p>
          <div className="row">
            <select value={sel[d.id]?.tipo || "rejeitar"} onChange={(e) => mudar(d.id, "tipo", e.target.value)}>
              {ACOES.map(([v, r]) => <option key={v} value={v}>{r}</option>)}
            </select>
            <input placeholder="Justificativa (obrigatória ao remover)" maxLength={300} value={sel[d.id]?.justificativa || ""} onChange={(e) => mudar(d.id, "justificativa", e.target.value)} />
            <button onClick={() => decidir(d)}>Aplicar</button>
          </div>
        </div>
      ))}
      <Paginacao dados={dados} pagina={pagina} setPagina={setPagina} />
    </>
  );
}

function Barras({ titulo, itens }) {
  const max = Math.max(1, ...itens.map((i) => i.total));
  return (
    <div className="card">
      <h3>{titulo}</h3>
      {itens.length === 0 && <p className="mut">Sem dados no período.</p>}
      {itens.map((i) => (
        <div className="barra" key={i.rotulo}>
          <span>{i.rotulo}</span>
          <div><i style={{ width: `${(i.total / max) * 100}%` }} /></div>
          <b>{i.total}</b>
        </div>
      ))}
    </div>
  );
}

// DASH001: entidade multidimensional (categoria × modalidade × período) com totalizações
export function Dashboard() {
  const [f, setF] = useState({ inicio: "", fim: "", categoria: "" });
  const [cats, setCats] = useState([]);
  const [d, setD] = useState(null);
  const [erro, setErro] = useState("");
  useEffect(() => { api("/categorias/").then(setCats).catch(() => {}); }, []);
  useEffect(() => { api("/dashboard/", { params: f }).then(setD).catch((x) => setErro(x.message)); }, [f]);

  if (erro) return <p className="erro">{erro}</p>;
  if (!d) return <p>Carregando…</p>;
  const nomesCat = [...new Set(d.matriz_categoria_modalidade.map((m) => m.categorias__nome))];
  const celula = (c, m) => d.matriz_categoria_modalidade.find((x) => x.categorias__nome === c && x.modalidade === m)?.total || 0;
  return (
    <>
      <h1>Dashboard</h1>
      <div className="filtros card">
        <label>De<input type="date" {...campo(f, setF, "inicio")} /></label>
        <label>Até<input type="date" {...campo(f, setF, "fim")} /></label>
        <label>Categoria
          <select {...campo(f, setF, "categoria")}>
            <option value="">Todas</option>
            {cats.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
          </select>
        </label>
      </div>
      <div className="kpis">
        <div className="card"><b>{d.usuarios_ativos}</b><span>usuários ativos</span></div>
        <div className="card"><b>{reais(d.valor_total_vendas)}</b><span>em vendas concluídas</span></div>
        <div className="card"><b>{d.denuncias_atendidas}</b><span>denúncias atendidas</span></div>
        <div className="card"><b>{d.denuncias_abertas}</b><span>denúncias abertas</span></div>
      </div>
      <div className="grade">
        <Barras titulo="Anúncios por categoria" itens={d.anuncios_por_categoria.map((i) => ({ rotulo: i.categorias__nome || "Sem categoria", total: i.total }))} />
        <Barras titulo="Anúncios por modalidade" itens={d.anuncios_por_modalidade.map((i) => ({ rotulo: rotulo(MODALIDADES, i.modalidade), total: i.total }))} />
        <Barras titulo="Negociações concluídas por mês" itens={d.negociacoes_concluidas_por_mes.map((i) => ({ rotulo: new Date(i.mes).toLocaleDateString("pt-BR", { month: "2-digit", year: "numeric" }), total: i.total }))} />
      </div>
      <div className="card tabela">
        <h3>Categoria × modalidade</h3>
        <table>
          <thead><tr><th></th>{MODALIDADES.map(([v, r]) => <th key={v}>{r}</th>)}</tr></thead>
          <tbody>
            {nomesCat.map((c) => (
              <tr key={c}><th>{c}</th>{MODALIDADES.map(([v]) => <td key={v}>{celula(c, v)}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
