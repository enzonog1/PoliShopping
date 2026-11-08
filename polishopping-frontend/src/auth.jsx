import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api.js";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [carregando, setCarregando] = useState(!!localStorage.getItem("token"));

  useEffect(() => {
    if (!localStorage.getItem("token")) return;
    api("/auth/eu/")
      .then(setUser)
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setCarregando(false));
  }, []);

  const entrar = ({ token, usuario }) => {
    localStorage.setItem("token", token);
    setUser(usuario);
  };
  const trocarToken = (token) => localStorage.setItem("token", token);
  const sair = () => {
    localStorage.removeItem("token");
    setUser(null);
  };
  return <Ctx.Provider value={{ user, carregando, entrar, sair, trocarToken }}>{children}</Ctx.Provider>;
}
