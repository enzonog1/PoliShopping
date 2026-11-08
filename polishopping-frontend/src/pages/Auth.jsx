import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { campo } from "../componentes.jsx";

export function Login() {
  const { entrar } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ email: "", password: "" });
  const [erro, setErro] = useState("");

  const enviar = async (e) => {
    e.preventDefault();
    try {
      entrar(await api("/auth/login/", { method: "POST", body: f }));
      nav("/");
    } catch (x) {
      setErro(x.message);
    }
  };
  return (
    <form className="card form" onSubmit={enviar}>
      <h2>Entrar</h2>
      <label>E-mail USP<input type="email" required {...campo(f, setF, "email")} /></label>
      <label>Senha<input type="password" required {...campo(f, setF, "password")} /></label>
      {erro && <p className="erro">{erro}</p>}
      <button>Entrar</button>
      <p>Ainda não tem conta? <Link to="/cadastro">Cadastre-se</Link></p>
      <p>Recebeu um código por e-mail? <Link to="/verificar">Confirmar e-mail</Link></p>
    </form>
  );
}

export function Cadastro() {
  const { entrar } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ nome_completo: "", email: "", nusp: "", password: "", confirmacao: "" });
  const [erro, setErro] = useState("");

  const enviar = async (e) => {
    e.preventDefault();
    if (f.password !== f.confirmacao) return setErro("A confirmação de senha não confere.");
    try {
      const { confirmacao, ...corpo } = f;
      await api("/auth/registro/", { method: "POST", body: { ...corpo, nusp: Number(f.nusp) } });
      nav(`/verificar?email=${encodeURIComponent(f.email)}`);
    } catch (x) {
      setErro(x.message);
    }
  };
  return (
    <form className="card form" onSubmit={enviar}>
      <h2>Cadastrar</h2>
      <label>Nome completo<input required maxLength={150} {...campo(f, setF, "nome_completo")} /></label>
      <label>E-mail USP (@usp.br)<input type="email" required maxLength={100} {...campo(f, setF, "email")} /></label>
      <label>Número USP (8 dígitos)<input required pattern="\d{8}" {...campo(f, setF, "nusp")} /></label>
      <label>Senha (mínimo 8, com letras e números)<input type="password" required minLength={8} {...campo(f, setF, "password")} /></label>
      <label>Confirmação de senha<input type="password" required {...campo(f, setF, "confirmacao")} /></label>
      {erro && <p className="erro">{erro}</p>}
      <button>Criar conta</button>
    </form>
  );
}

// CAD001: confirmação do e-mail USP com o código de 6 dígitos
export function Verificar() {
  const { entrar } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [f, setF] = useState({ email: params.get("email") || "", codigo: "" });
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState(params.get("email") ? "Enviamos um código de 6 dígitos para o seu e-mail USP." : "");

  const enviar = async (e) => {
    e.preventDefault();
    setErro("");
    try {
      entrar(await api("/auth/verificar/", { method: "POST", body: f }));
      nav("/");
    } catch (x) {
      setErro(x.message);
    }
  };
  const reenviar = async () => {
    setErro("");
    try {
      const r = await api("/auth/reenviar-codigo/", { method: "POST", body: { email: f.email } });
      setAviso(r.detail);
    } catch (x) {
      setErro(x.message);
    }
  };
  return (
    <form className="card form" onSubmit={enviar}>
      <h2>Confirmar e-mail USP</h2>
      {aviso && <p className="ok">{aviso}</p>}
      <label>E-mail USP<input type="email" required {...campo(f, setF, "email")} /></label>
      <label>Código de 6 dígitos<input required inputMode="numeric" pattern="\d{6}" maxLength={6} {...campo(f, setF, "codigo")} /></label>
      {erro && <p className="erro">{erro}</p>}
      <button>Confirmar</button>
      <button type="button" className="sec" onClick={reenviar} disabled={!f.email}>Reenviar código</button>
    </form>
  );
}

// USU001: perfil, reputação e alteração de senha
export function Perfil() {
  const { user, trocarToken } = useAuth();
  const vazio = { senha_atual: "", nova_senha: "", confirmacao: "" };
  const [f, setF] = useState(vazio);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  const enviar = async (e) => {
    e.preventDefault();
    setErro("");
    setAviso("");
    try {
      const r = await api("/auth/senha/", { method: "POST", body: f });
      trocarToken(r.token);
      setF(vazio);
      setAviso("Senha atualizada.");
    } catch (x) {
      setErro(x.message);
    }
  };
  return (
    <>
      <h1>Meu perfil</h1>
      <div className="card">
        <dl>
          <dt>Nome</dt><dd>{user.nome_completo}</dd>
          <dt>E-mail USP</dt><dd>{user.email}</dd>
          <dt>NUSP</dt><dd>{user.nusp}</dd>
          <dt>Reputação</dt><dd>{user.reputacao_media ? `★ ${user.reputacao_media.toFixed(1)}` : "Sem avaliações ainda"}</dd>
        </dl>
        <p><Link to="/propostas">Ver histórico de negociações</Link></p>
      </div>
      <form className="card form" onSubmit={enviar}>
        <h2>Alterar senha</h2>
        <label>Senha atual<input type="password" required {...campo(f, setF, "senha_atual")} /></label>
        <label>Nova senha (mínimo 8, com letras e números)<input type="password" required minLength={8} {...campo(f, setF, "nova_senha")} /></label>
        <label>Confirmação da nova senha<input type="password" required {...campo(f, setF, "confirmacao")} /></label>
        {aviso && <p className="ok">{aviso}</p>}
        {erro && <p className="erro">{erro}</p>}
        <button>Salvar nova senha</button>
      </form>
    </>
  );
}
