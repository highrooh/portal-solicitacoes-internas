# Dicionário de dados

Banco relacional SQLite. As chaves estrangeiras são habilitadas pela aplicação ao abrir cada conexão.

## `users`

| Campo | Tipo | Obrigatório | Regra / finalidade |
| --- | --- | --- | --- |
| `id` | INTEGER | Sim | Chave primária autoincremental. |
| `name` | TEXT | Sim | Nome de exibição, entre 2 e 120 caracteres. |
| `username` | TEXT | Sim | Identificador único de login, entre 3 e 60 caracteres. |
| `password_hash` | TEXT | Sim | Hash de senha gerado pelo Werkzeug; nunca armazena senha em texto puro. |
| `role` | TEXT | Sim | `solicitante` ou `gestor`; padrão `solicitante`. |
| `created_at` | TEXT | Sim | Data e hora de cadastro; padrão do SQLite. |

## `requests`

| Campo | Tipo | Obrigatório | Regra / finalidade |
| --- | --- | --- | --- |
| `id` | INTEGER | Sim | Chave primária; exibida como código `SOL-0001`. |
| `title` | TEXT | Sim | Título com até 120 caracteres. |
| `description` | TEXT | Sim | Descrição com até 4.000 caracteres. |
| `category` | TEXT | Sim | Uma das categorias previstas: TI, RH, Compras, Financeiro ou Infraestrutura. |
| `status` | TEXT | Sim | Aberto, Em Atendimento ou Concluído; começa como Aberto. |
| `user_id` | INTEGER | Sim | Chave estrangeira para `users.id`, identifica o solicitante. Exclusão do usuário é restrita. |
| `created_at` | TEXT | Sim | Data e hora UTC em ISO 8601 da criação. |
| `updated_at` | TEXT | Sim | Data e hora UTC em ISO 8601 da alteração mais recente. |

## Índices

`idx_requests_status`, `idx_requests_category`, `idx_requests_created_at` e `idx_requests_user_id` apoiam os filtros e a relação com o solicitante.
