import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { Paginacao, STATUS_PROPOSTA, Selo } from "../componentes.jsx";

// NEG002 (aceitar ou recusar) e AVAL001 (avaliar após o encontro)
export default function Propostas() {
  const [aba, setAba] = useState("recebidas");
  const [pagina, setPagina] = useState(1);
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [aval, setAval] = useState(null);
  const [form, setForm] = useState({ nota: 5, comentario: "" });

  const carregar = () => api("/propostas/", { params: { [aba]: 1, page: pagina } }).then(setDados).catch((x) => setErro(x.message));
  useEffect(() => { setDados(null); carregar(); }, [aba, pagina]);

  const agir = async (id, acao, corpo, ok) => {
    setErro(""); setAviso("");
    try { await api(`/propostas/${id}/${acao}/`, { method: "POST", body: corpo }); setAviso(ok); setAval(null); carregar(); }
    catch (x) { setErro(x.message); }
  };
  const recusar = (id) => {
    const j = window.prompt("Justificativa (opcional):");
    if (j !== null) agir(id, "recusar", { justificativa: j }, "Proposta recusada.");
  };
  return (
    <>
      <h1>Propostas</h1>
      <div className="row">
        <button className={aba === "recebidas" ? "" : "sec"} onClick={() => { setPagina(1); setAba("recebidas"); }}>Recebidas</button>
        <button className={aba === "enviadas" ? "" : "sec"} onClick={() => { setPagina(1); setAba("enviadas"); }}>Enviadas</button>
      </div>
      {aviso && <p className="ok">{aviso}</p>}
      {erro && <p className="erro">{erro}</p>}
      {dados && dados.results.length === 0 && <p>Nenhuma proposta por aqui.</p>}
      {dados?.results.map((p) => (
        <div className="card" key={p.id}>
          <div className="linha">
            <Link to={`/anuncios/${p.anuncio}`}><b>{p.anuncio_titulo}</b></Link>
            <Selo lista={STATUS_PROPOSTA} valor={p.status} />
          </div>
          <p className="mut">De {p.interessado.nome_completo}{p.mensagem ? `: “${p.mensagem}”` : ""}</p>
          {p.justificativa_recusa && <p className="mut">Justificativa da recusa: {p.justificativa_recusa}</p>}
          {p.contato && <p>Contato para combinar o encontro: <b>{p.contato}</b></p>}
          <div className="row">
            {aba === "recebidas" && p.status === "pendente" && (
              <>
                <button onClick={() => agir(p.id, "aceitar", {}, "Proposta aceita. O contato do comprador foi liberado.")}>Aceitar</button>
                <button className="sec" onClick={() => recusar(p.id)}>Recusar</button>
              </>
            )}
            {["aceita", "concluida"].includes(p.status) && (
              <button className="sec" onClick={() => setAval(aval === p.id ? null : p.id)}>Marcar como concluído e avaliar</button>
            )}
          </div>
          {aval === p.id && (
            <form className="form" onSubmit={(e) => { e.preventDefault(); agir(p.id, "avaliar", { nota: Number(form.nota), comentario: form.comentario }, "Avaliação registrada. Obrigado!"); }}>
              <label>Nota
                <select value={form.nota} onChange={(e) => setForm({ ...form, nota: e.target.value })}>
                  {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{"★".repeat(n)}</option>)}
                </select>
              </label>
              <label>Comentário (opcional)<textarea maxLength={300} value={form.comentario} onChange={(e) => setForm({ ...form, comentario: e.target.value })} /></label>
              <button>Enviar avaliação</button>
            </form>
          )}
        </div>
      ))}
      <Paginacao dados={dados} pagina={pagina} setPagina={setPagina} />
    </>
  );
}
