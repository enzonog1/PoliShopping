import { Link, NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import { Cadastro, Login, Perfil, Verificar } from "./pages/Auth.jsx";
import { Catalogo, Detalhe, Formulario, MeusAnuncios } from "./pages/Anuncios.jsx";
import Propostas from "./pages/Propostas.jsx";
import { Dashboard, Moderacao } from "./pages/Admin.jsx";

function Privada({ children, moderador }) {
  const { user, carregando } = useAuth();
  if (carregando) return <p>Carregando…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (moderador && !user.is_moderador) return <p className="erro">Acesso restrito a moderadores.</p>;
  return children;
}

export default function App() {
  const { user, sair } = useAuth();
  return (
    <>
      <header className="topo">
        <nav>
          <Link to="/" className="logo">PoliShopping</Link>
          <NavLink to="/">Catálogo</NavLink>
          {user && (
            <>
              <NavLink to="/novo">Novo anúncio</NavLink>
              <NavLink to="/meus">Meus anúncios</NavLink>
              <NavLink to="/propostas">Propostas</NavLink>
            </>
          )}
          {user?.is_moderador && (
            <>
              <NavLink to="/moderacao">Moderação</NavLink>
              <NavLink to="/dashboard">Dashboard</NavLink>
            </>
          )}
          <span className="espaco" />
          {user ? (
            <>
              <NavLink to="/perfil">{user.nome_completo}{user.reputacao_media ? ` ★ ${user.reputacao_media.toFixed(1)}` : ""}</NavLink>
              <button onClick={sair}>Sair</button>
            </>
          ) : (
            <>
              <NavLink to="/login">Entrar</NavLink>
              <NavLink to="/cadastro">Cadastrar</NavLink>
            </>
          )}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Catalogo />} />
          <Route path="/anuncios/:id" element={<Detalhe />} />
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route path="/verificar" element={<Verificar />} />
          <Route path="/perfil" element={<Privada><Perfil /></Privada>} />
          <Route path="/novo" element={<Privada><Formulario /></Privada>} />
          <Route path="/anuncios/:id/editar" element={<Privada><Formulario /></Privada>} />
          <Route path="/meus" element={<Privada><MeusAnuncios /></Privada>} />
          <Route path="/propostas" element={<Privada><Propostas /></Privada>} />
          <Route path="/moderacao" element={<Privada moderador><Moderacao /></Privada>} />
          <Route path="/dashboard" element={<Privada moderador><Dashboard /></Privada>} />
          <Route path="*" element={<p>Página não encontrada.</p>} />
        </Routes>
      </main>
    </>
  );
}
