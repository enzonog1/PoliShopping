# PoliShopping: front-end (React + Vite)

Consome a API Django da pasta `polishopping-backend`.

```bash
npm install
npm run dev        # http://localhost:5173 (a API precisa estar em http://localhost:8000)
npm run build      # gera a pasta dist/
```
Para apontar para outro servidor, crie um arquivo `.env` com `VITE_API_URL=https://endereco-da-api/api`.

## Telas
| Rota | Tela | Caso de uso |
|---|---|---|
| `/cadastro`, `/verificar`, `/login` | cadastro, código de confirmação por e-mail e login | CAD001, AUT001 |
| `/perfil` | dados, reputação e alteração de senha | USU001 |
| `/` | catálogo com filtros | PRO003 |
| `/anuncios/:id` | detalhe, proposta e denúncia | PRO003, NEG001, DEN001 |
| `/novo`, `/anuncios/:id/editar`, `/meus` | criar, editar, pausar e excluir | PRO001, PRO002 |
| `/propostas` | recebidas e enviadas, aceitar, recusar, avaliar | NEG002, AVAL001 |
| `/moderacao` | fila de denúncias (só moderador) | MOD001 |
| `/dashboard` | totais multidimensionais (só moderador) | DASH001 |
