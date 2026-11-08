# PoliShopping: back-end (Django + Django REST Framework)

API que o front-end em React vai consumir (a entrega final exige API + framework JavaScript).

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations marketplace
python manage.py migrate
python manage.py createsuperuser   # pede e-mail, nome completo e NUSP
python manage.py runserver         # API em http://localhost:8000/api/
python manage.py test              # roda os testes de fluxo
```
Em desenvolvimento, os e-mails (inclusive o código de verificação) aparecem no terminal do `runserver`.

No admin (`/admin/`), crie as categorias e marque `is_moderador` nos moderadores.

## Rotas principais
| Rota | O que faz | Caso de uso |
|---|---|---|
| `POST /api/auth/registro/` | cadastro só com @usp.br; envia código de 6 dígitos por e-mail | CAD001 |
| `POST /api/auth/verificar/` · `POST /api/auth/reenviar-codigo/` | confirma o código (devolve o token) e reenvia | CAD001 |
| `POST /api/auth/login/` | login por e-mail e senha, devolve token | AUT001 |
| `GET /api/auth/eu/` · `POST /api/auth/senha/` | perfil do usuário logado e alteração de senha | USU001 |
| `GET /api/anuncios/?q=&categoria=&modalidade=&preco_min=&preco_max=` | catálogo com filtros | PRO003 |
| `POST /api/anuncios/` · `PUT/DELETE /api/anuncios/{id}/` · `POST .../pausar/` | criar, editar, excluir, pausar | PRO001, PRO002 |
| `POST /api/anuncios/{id}/fotos/` (multipart, campo `arquivo`) · `DELETE .../fotos/{foto_id}/` | enviar e remover fotos (até 3, 5 MB) | PRO001, PRO002 |
| `POST /api/propostas/` · `POST .../aceitar/` · `.../recusar/` | negociação | NEG001, NEG002 |
| `POST /api/propostas/{id}/avaliar/` | avaliação e conclusão | AVAL001 |
| `POST /api/denuncias/` | denunciar anúncio (3 denúncias ocultam) | DEN001 |
| `GET/POST /api/moderacao/` | ações do moderador (rejeitar, advertir, remover, suspender) | MOD001 |
| `GET /api/dashboard/?inicio=&fim=&categoria=` | totais por categoria, modalidade e mês | DASH001 |

O React envia o token no cabeçalho: `Authorization: Token <token>`.

## Ainda falta
- Recuperação de senha esquecida, expiração de sessão por inatividade e exportação do dashboard.
- Exclusão lógica de anúncio (hoje o DELETE apaga o registro).
