import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { MODALIDADES, MOTIVOS, ESTADOS, Paginacao, Selo, campo, reais, rotulo } from "../componentes.jsx";

function Cartao({ a }) {
  return (
    <Link to={`/anuncios/${a.id}`} className="card anuncio">
      {a.fotos[0] && <img src={a.fotos[0].arquivo} alt="" />}
      <h3>{a.titulo}</h3>
      <p className="mut">{rotulo(MODALIDADES, a.modalidade)}{a.preco != null && ` · ${reais(a.preco)}`}</p>
      <p className="mut">{a.ponto_encontro} · {a.dono.nome_completo}</p>
      <Selo lista={ESTADOS} valor={a.estado} />
    </Link>
  );
}

// PRO003: catálogo com busca e filtros
export function Catalogo() {
  const vazio = { q: "", categoria: "", modalidade: "", preco_min: "", preco_max: "" };
  const [cats, setCats] = useState([]);
  const [f, setF] = useState(vazio);
  const [pagina, setPagina] = useState(1);
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => { api("/categorias/").then(setCats).catch(() => {}); }, []);
  useEffect(() => {
    api("/anuncios/", { params: { ...f, page: pagina } }).then(setDados).catch((x) => setErro(x.message));
  }, [f, pagina]);

  const mudar = (k, v) => { setPagina(1); setF({ ...f, [k]: v }); };
  return (
    <>
      <h1>Catálogo</h1>
      <div className="filtros card">
        <input placeholder="Buscar por título ou descrição" value={f.q} onChange={(e) => mudar("q", e.target.value)} />
        <select value={f.categoria} onChange={(e) => mudar("categoria", e.target.value)}>
          <option value="">Todas as categorias</option>
          {cats.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
        </select>
        <select value={f.modalidade} onChange={(e) => mudar("modalidade", e.target.value)}>
          <option value="">Todas as modalidades</option>
          {MODALIDADES.map(([v, r]) => <option key={v} value={v}>{r}</option>)}
        </select>
        <input type="number" min="0" placeholder="Preço mín." value={f.preco_min} onChange={(e) => mudar("preco_min", e.target.value)} />
        <input type="number" min="0" placeholder="Preço máx." value={f.preco_max} onChange={(e) => mudar("preco_max", e.target.value)} />
      </div>
      {erro && <p className="erro">{erro}</p>}
      {dados && dados.results.length === 0 && (
        <p>Nenhum anúncio foi encontrado com os critérios selecionados. <button onClick={() => { setPagina(1); setF(vazio); }}>Limpar filtros</button></p>
      )}
      <div className="grade">{dados?.results.map((a) => <Cartao key={a.id} a={a} />)}</div>
      <Paginacao dados={dados} pagina={pagina} setPagina={setPagina} />
    </>
  );
}

// PRO003 (detalhes), NEG001 (proposta) e DEN001 (denúncia)
export function Detalhe() {
  const { id } = useParams();
  const { user } = useAuth();
  const [a, setA] = useState(null);
  const [nomes, setNomes] = useState({});
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [painel, setPainel] = useState("");
  const [msg, setMsg] = useState("");
  const [den, setDen] = useState({ motivo: "improprio", detalhamento: "" });

  useEffect(() => {
    api(`/anuncios/${id}/`).then(setA).catch((x) => setErro(x.message));
    api("/categorias/").then((cs) => setNomes(Object.fromEntries(cs.map((c) => [c.id, c.nome])))).catch(() => {});
  }, [id]);

  const enviar = async (caminho, corpo, ok) => {
    setErro(""); setAviso("");
    try { await api(caminho, { method: "POST", body: corpo }); setAviso(ok); setPainel(""); }
    catch (x) { setErro(x.message); }
  };
  if (!a) return erro ? <p className="erro">{erro}</p> : <p>Carregando…</p>;
  const dono = user && user.id === a.dono.id;
  return (
    <article className="card detalhe">
      <h1>{a.titulo} <Selo lista={ESTADOS} valor={a.estado} /></h1>
      <div className="fotos">{a.fotos.map((f) => <img key={f.id} src={f.arquivo} alt="" />)}</div>
      <p>{a.descricao}</p>
      <dl>
        <dt>Modalidade</dt><dd>{rotulo(MODALIDADES, a.modalidade)}</dd>
        {a.preco != null && <><dt>Preço</dt><dd>{reais(a.preco)}</dd></>}
        <dt>Quantidade</dt><dd>{a.quantidade}</dd>
        <dt>Categorias</dt><dd>{a.categorias.map((c) => nomes[c]).filter(Boolean).join(", ")}</dd>
        <dt>Encontro presencial na Poli</dt><dd>{a.ponto_encontro}</dd>
        <dt>Anunciante</dt><dd>{a.dono.nome_completo}{a.dono.reputacao_media ? ` ★ ${a.dono.reputacao_media.toFixed(1)}` : " (sem avaliações)"}</dd>
      </dl>
      {aviso && <p className="ok">{aviso}</p>}
      {erro && <p className="erro">{erro}</p>}
      {!user && <p><Link to="/login">Entre</Link> para negociar ou denunciar.</p>}
      {dono && <p>Você é o dono deste anúncio. <Link to={`/anuncios/${a.id}/editar`}>Editar</Link></p>}
      {user && !dono && (
        <div className="row">
          {a.estado === "ativo" && (
            <button onClick={() => setPainel("proposta")}>
              {a.modalidade === "emprestimo" ? "Solicitar empréstimo" : "Tenho interesse"}
            </button>
          )}
          <button className="sec" onClick={() => setPainel("denuncia")}>Denunciar anúncio</button>
        </div>
      )}
      {painel === "proposta" && (
        <form className="form" onSubmit={(e) => { e.preventDefault(); enviar("/propostas/", { anuncio: a.id, mensagem: msg }, "Solicitação enviada! O anunciante foi notificado."); }}>
          <p>Sugestão de encontro: <b>{a.ponto_encontro}</b></p>
          <label>Mensagem (opcional)<textarea maxLength={500} value={msg} onChange={(e) => setMsg(e.target.value)} /></label>
          <button>Confirmar proposta</button>
        </form>
      )}
      {painel === "denuncia" && (
        <form className="form" onSubmit={(e) => { e.preventDefault(); enviar("/denuncias/", { anuncio: a.id, ...den }, "Obrigado. Sua denúncia foi enviada para análise da equipe de moderação."); }}>
          <label>Motivo
            <select {...campo(den, setDen, "motivo")}>{MOTIVOS.map(([v, r]) => <option key={v} value={v}>{r}</option>)}</select>
          </label>
          <label>Detalhamento<textarea required maxLength={500} {...campo(den, setDen, "detalhamento")} /></label>
          <button>Enviar denúncia</button>
        </form>
      )}
    </article>
  );
}

// PRO002: editar, pausar e excluir os próprios anúncios
export function MeusAnuncios() {
  const [dados, setDados] = useState(null);
  const [pagina, setPagina] = useState(1);
  const [erro, setErro] = useState("");
  const carregar = () => api("/anuncios/", { params: { meus: 1, page: pagina } }).then(setDados).catch((x) => setErro(x.message));
  useEffect(() => { carregar(); }, [pagina]);

  const agir = async (caminho, opcoes) => {
    setErro("");
    try { await api(caminho, opcoes); carregar(); } catch (x) { setErro(x.message); }
  };
  return (
    <>
      <h1>Meus anúncios</h1>
      {erro && <p className="erro">{erro}</p>}
      {dados && dados.results.length === 0 && <p>Você ainda não tem anúncios. <Link to="/novo">Criar o primeiro</Link></p>}
      {dados?.results.map((a) => (
        <div className="card linha" key={a.id}>
          <div><Link to={`/anuncios/${a.id}`}><b>{a.titulo}</b></Link> <Selo lista={ESTADOS} valor={a.estado} /></div>
          <div className="row">
            <Link to={`/anuncios/${a.id}/editar`}>Editar</Link>
            {["ativo", "inativo"].includes(a.estado) && (
              <button className="sec" onClick={() => agir(`/anuncios/${a.id}/pausar/`, { method: "POST" })}>
                {a.estado === "ativo" ? "Pausar" : "Reativar"}
              </button>
            )}
            <button className="perigo" onClick={() => window.confirm("Excluir este anúncio?") && agir(`/anuncios/${a.id}/`, { method: "DELETE" })}>Excluir</button>
          </div>
        </div>
      ))}
      <Paginacao dados={dados} pagina={pagina} setPagina={setPagina} />
    </>
  );
}

// PRO001 e PRO002: formulário de criação e edição, com envio de até 3 fotos
export function Formulario() {
  const { id } = useParams();
  const nav = useNavigate();
  const [f, setF] = useState({ titulo: "", descricao: "", modalidade: "venda", preco: "", quantidade: 1, ponto_encontro: "", categorias: [] });
  const [cats, setCats] = useState([]);
  const [fotos, setFotos] = useState([]); // já salvas no servidor
  const [novas, setNovas] = useState([]); // escolhidas agora, ainda não enviadas
  const [erro, setErro] = useState("");
  const semPreco = ["troca", "geral"].includes(f.modalidade);

  useEffect(() => {
    api("/categorias/").then(setCats).catch(() => {});
    if (id) {
      api(`/anuncios/${id}/`).then((a) => {
        setF({
          titulo: a.titulo, descricao: a.descricao, modalidade: a.modalidade, preco: a.preco ?? "",
          quantidade: a.quantidade, ponto_encontro: a.ponto_encontro, categorias: a.categorias,
        });
        setFotos(a.fotos);
      }).catch((x) => setErro(x.message));
    }
  }, [id]);

  const alternar = (c) => setF({ ...f, categorias: f.categorias.includes(c) ? f.categorias.filter((x) => x !== c) : [...f.categorias, c] });
  const escolher = (e) => {
    const arqs = [...e.target.files];
    if (arqs.some((a) => a.size > 5 * 1024 * 1024)) return setErro("Cada foto pode ter no máximo 5 MB.");
    if (fotos.length + arqs.length > 3) return setErro("Cada anúncio aceita no máximo 3 fotos.");
    setErro("");
    setNovas(arqs);
  };
  const removerFoto = async (fid) => {
    try {
      await api(`/anuncios/${id}/fotos/${fid}/`, { method: "DELETE" });
      setFotos(fotos.filter((x) => x.id !== fid));
    } catch (x) {
      setErro(x.message);
    }
  };
  const enviar = async (e) => {
    e.preventDefault();
    if (f.categorias.length === 0) return setErro("Escolha ao menos uma categoria.");
    let r;
    try {
      const corpo = { ...f, quantidade: Number(f.quantidade), preco: semPreco ? null : f.preco };
      r = await api(id ? `/anuncios/${id}/` : "/anuncios/", { method: id ? "PUT" : "POST", body: corpo });
    } catch (x) {
      return setErro(x.message);
    }
    try {
      for (const arq of novas) {
        const dados = new FormData();
        dados.append("arquivo", arq);
        await api(`/anuncios/${r.id}/fotos/`, { method: "POST", body: dados });
      }
    } catch (x) {
      window.alert(`O anúncio foi salvo, mas uma foto falhou: ${x.message}`);
      return nav(`/anuncios/${r.id}/editar`);
    }
    nav(`/anuncios/${r.id}`);
  };
  return (
    <form className="card form" onSubmit={enviar}>
      <h2>{id ? "Editar anúncio" : "Novo anúncio"}</h2>
      <label>Título<input required maxLength={150} {...campo(f, setF, "titulo")} /></label>
      <label>Descrição<textarea required maxLength={1000} {...campo(f, setF, "descricao")} /></label>
      <label>Modalidade
        <select {...campo(f, setF, "modalidade")}>{MODALIDADES.map(([v, r]) => <option key={v} value={v}>{r}</option>)}</select>
      </label>
      <fieldset>
        <legend>Categorias</legend>
        {cats.map((c) => (
          <label key={c.id} className="inline"><input type="checkbox" checked={f.categorias.includes(c.id)} onChange={() => alternar(c.id)} /> {c.nome}</label>
        ))}
      </fieldset>
      <fieldset>
        <legend>Fotos (até 3, de até 5 MB cada)</legend>
        <div className="fotos">
          {fotos.map((ft) => (
            <div className="foto" key={ft.id}>
              <img src={ft.arquivo} alt="" />
              <button type="button" className="perigo" onClick={() => removerFoto(ft.id)}>Remover</button>
            </div>
          ))}
        </div>
        {fotos.length < 3 && <input type="file" accept="image/*" multiple onChange={escolher} />}
        {novas.length > 0 && <p className="mut">Serão enviadas ao salvar: {novas.map((n) => n.name).join(", ")}</p>}
      </fieldset>
      <label>Preço ou valor da diária (R$)
        <input type="number" step="0.01" min="0" disabled={semPreco} required={!semPreco} {...campo(f, setF, "preco")} />
      </label>
      <label>Quantidade<input type="number" min="1" required {...campo(f, setF, "quantidade")} /></label>
      <label>Ponto de encontro na Poli (local público)<input required maxLength={100} {...campo(f, setF, "ponto_encontro")} /></label>
      {erro && <p className="erro">{erro}</p>}
      <button>{id ? "Salvar" : "Publicar"}</button>
    </form>
  );
}
