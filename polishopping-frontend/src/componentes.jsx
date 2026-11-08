export const MODALIDADES = [["venda", "Venda"], ["emprestimo", "Empréstimo/Aluguel"], ["troca", "Troca"], ["geral", "Anúncio geral"]];
export const ESTADOS = [["ativo", "Ativo"], ["em_negociacao", "Em negociação"], ["concluido", "Concluído"], ["inativo", "Inativo"], ["pendente_moderacao", "Pendente de moderação"], ["removido", "Bloqueado/Removido"]];
export const STATUS_PROPOSTA = [["pendente", "Pendente de resposta"], ["aceita", "Aceita"], ["recusada", "Recusada"], ["concluida", "Concluída"]];
export const MOTIVOS = [["improprio", "Conteúdo impróprio"], ["golpe", "Preço abusivo/golpe"], ["proibido", "Item proibido"], ["outros", "Outros"]];
export const ACOES = [["rejeitar", "Rejeitar denúncia (anúncio segue ativo)"], ["advertir", "Advertir anunciante"], ["remover", "Remover anúncio"], ["suspender", "Suspender usuário"]];

export const rotulo = (lista, v) => (lista.find((x) => x[0] === v) || [null, v])[1];
export const reais = (v) => `R$ ${Number(v).toFixed(2).replace(".", ",")}`;
// Liga um input ao estado de um formulário: <input {...campo(f, setF, "nome")} />
export const campo = (f, setF, nome) => ({ value: f[nome], onChange: (e) => setF({ ...f, [nome]: e.target.value }) });

export function Selo({ lista, valor }) {
  return <span className={`selo ${valor}`}>{rotulo(lista, valor)}</span>;
}

export function Paginacao({ dados, pagina, setPagina }) {
  if (!dados || (!dados.next && !dados.previous)) return null;
  return (
    <div className="paginacao">
      <button disabled={!dados.previous} onClick={() => setPagina(pagina - 1)}>Anterior</button>
      <span>Página {pagina}</span>
      <button disabled={!dados.next} onClick={() => setPagina(pagina + 1)}>Próxima</button>
    </div>
  );
}
