# Fluxo interno — Portal de solicitações

Aplicação web para registrar pedidos internos e acompanhar o atendimento. Foi feita para a etapa prática de desenvolvimento da bit Soluções. A tela está em português e funciona em computador e celular.

## O que dá para fazer

- Entrar e sair com usuário e senha.
- Criar solicitações nas categorias TI, RH, Compras, Financeiro e Infraestrutura.
- Consultar detalhes, pesquisar pelo título e filtrar por categoria, status e período.
- Editar ou excluir uma solicitação enquanto ela estiver aberta.
- Acompanhar o painel com os totais de cada status.
- Acessar a área de gestão para iniciar atendimentos e concluir pedidos.

## Tecnologias

- Python 3.10 ou superior e Flask para a aplicação e a API JSON.
- python-dotenv para carregar as variáveis do arquivo `.env` durante a execução local.
- SQLite para persistência relacional, sem serviço de banco separado.
- HTML, CSS e JavaScript sem framework no navegador.
- Docker Compose e Gunicorn como opções para empacotamento e execução.

## Pré-requisitos

- Python 3.10+ e pip para execução local; ou Docker com o plugin Compose.
- Não há dependência de serviços externos para a aplicação funcionar.

## Executar localmente

No PowerShell, a partir da pasta do projeto:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Abra <http://127.0.0.1:5000>. O arquivo SQLite é criado em `instance/solicitacoes.db` na primeira inicialização. O esquema também está disponível em `database/schema.sql`.

Para rodar em macOS ou Linux, crie o ambiente virtual com `python3 -m venv .venv`, ative-o com `source .venv/bin/activate` e use `cp .env.example .env`.

## Executar com Docker

```bash
docker compose up --build
```

Acesse <http://localhost:5000>. O Compose preserva o banco em um volume chamado `portal_data`. Para encerrar, use `docker compose down`; o volume permanece salvo.

## Configuração

Copie `.env.example` para `.env` e ajuste as variáveis antes de publicar:

| Variável | Uso | Valor local |
| --- | --- | --- |
| `SECRET_KEY` | Assinatura segura da sessão | Troque por uma chave aleatória |
| `DATABASE_PATH` | Caminho do arquivo SQLite | `instance/solicitacoes.db` |
| `PORT` | Porta HTTP local | `5000` |
| `COOKIE_SECURE` | Exige HTTPS para o cookie da sessão | `false` em desenvolvimento |
| `DEMO_USER_PASSWORD` | Senha criada para `marina` | `Marina@2026` |
| `DEMO_ADMIN_PASSWORD` | Senha criada para `gestor` | `Gestor@2026` |

Os usuários de demonstração são inseridos apenas quando a tabela de usuários está vazia. Para trocar essas senhas depois da primeira execução, atualize-as no banco ou recrie o banco local.

### Contas de demonstração

| Perfil | Usuário | Senha |
| --- | --- | --- |
| Solicitante | `marina` | `Marina@2026` |
| Gestor | `gestor` | `Gestor@2026` |

## API

As rotas de leitura e escrita usam JSON. As rotas protegidas exigem sessão autenticada; operações que alteram dados também exigem o token CSRF enviado pelo navegador no cabeçalho `X-CSRF-Token`.

| Método | Rota | Acesso |
| --- | --- | --- |
| `GET` | `/api/me` | Público; retorna a sessão atual |
| `POST` | `/api/login` | Público |
| `POST` | `/api/logout` | Autenticado |
| `GET` | `/api/dashboard` | Autenticado |
| `GET` | `/api/requests` | Autenticado; aceita `q`, `category`, `status`, `start`, `end` |
| `POST` | `/api/requests` | Autenticado |
| `GET` | `/api/requests/<id>` | Autenticado |
| `PATCH` | `/api/requests/<id>` | Solicitante dono ou gestor; apenas enquanto aberta |
| `DELETE` | `/api/requests/<id>` | Solicitante dono ou gestor; apenas enquanto aberta |
| `PATCH` | `/api/requests/<id>/status` | Gestor |

O gestor pode avançar de Aberto para Em Atendimento e de Em Atendimento para Concluído. Pedidos concluídos não podem ser reabertos.

## Banco e documentação

- `database/schema.sql`: criação das tabelas, restrições e índices.
- `docs/dicionario-de-dados.md`: descrição dos campos e regras do modelo.
- `docs/MEMORIAL_TECNICO_DE_DESENVOLVIMENTO.md`: tecnologias, justificativas, arquitetura e análise crítica.

## Estrutura do projeto

```text
app.py                  API e regras de negócio
database/schema.sql     Estrutura do banco SQLite
templates/index.html    Interface da aplicação
static/                 JavaScript e estilos
docs/                   Memorial técnico e dicionário de dados
```

## Segurança e uso fora do ambiente local

As senhas são armazenadas com hash, consultas usam parâmetros, as rotas validam entrada e a sessão tem proteção CSRF nas operações de escrita. Em um deploy público, configure uma chave secreta própria, HTTPS com `COOKIE_SECURE=true`, backups do volume e gestão de credenciais adequada. O modo de demonstração não inclui recuperação de senha, gestão de usuários ou trilha de auditoria.
