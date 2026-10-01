# Memorial Técnico de Desenvolvimento

## 1. Visão geral

O Fluxo interno é um portal para abertura e acompanhamento de solicitações internas. A proposta privilegia uma instalação curta e um fluxo fácil de entender: o colaborador registra o pedido, acompanha a fila e consulta o que já foi resolvido. A área de gestão pode movimentar os status.

## 2. Tecnologias e justificativas

| Tecnologia | Motivo da escolha | Benefícios e alternativas consideradas |
| --- | --- | --- |
| Python 3 | Linguagem principal do servidor. | Sintaxe direta e ecossistema maduro ajudam a manter uma aplicação pequena. Para este escopo, evita introduzir complexidade de compilação ou uma segunda linguagem no backend. |
| Flask 3 | Servidor HTTP e API JSON. | É leve e deixa explícitos os endpoints e as camadas de validação. Um framework mais opinativo, como Django, entregaria mais recursos prontos, mas não são necessários para o fluxo proposto. |
| SQLite | Banco de dados relacional. | Mantém integridade referencial e não requer instalação de um servidor de banco para a demonstração. PostgreSQL seria uma escolha natural para concorrência e operação em múltiplas instâncias. |
| HTML, CSS e JavaScript | Interface do navegador. | A interface consome a API sem etapa de build ou dependências de frontend. React ou Vue ajudariam em uma tela mais extensa, mas aumentariam o conjunto de ferramentas neste projeto pequeno. |
| Werkzeug | Hash e verificação de senhas. | Usa algoritmo de hash apropriado para senhas e já acompanha Flask, mantendo a dependência enxuta. Senhas nunca são persistidas em texto puro. |
| python-dotenv | Carregamento de configuração local. | Lê o arquivo `.env` sem exigir configuração manual no terminal durante o desenvolvimento. Em produção, as variáveis podem ser fornecidas pelo ambiente do container. |
| Gunicorn | Servidor WSGI no container. | É uma opção comum para servir Flask em Linux. O servidor integrado do Flask permanece disponível para desenvolvimento local. |
| Docker Compose | Execução empacotada e armazenamento persistente local. | Reduz diferenças de ambiente e permite iniciar a aplicação com um comando. Não substitui uma estratégia de implantação, monitoramento e backup. |

## 3. Arquitetura e organização

A aplicação é um monólito pequeno: Flask entrega a página inicial e fornece a API JSON; o navegador chama essa API usando `fetch`. A separação está organizada em responsabilidades por arquivo:

- `app.py`: rotas, validações, regras de autorização e acesso ao banco.
- `templates/index.html`: estrutura semântica da tela.
- `static/styles.css`: apresentação responsiva.
- `static/app.js`: estado da interface, chamadas HTTP, filtros e diálogos.
- `database/schema.sql`: estrutura persistente do banco.
- `docs/`: memorial e dicionário de dados.

Para o tamanho atual, manter a API num módulo evita criar abstrações que não agregariam clareza. Se o sistema crescer, rotas, serviços e repositórios podem ser extraídos para módulos próprios.

## 4. Modelagem de dados

Há duas entidades: `users` e `requests`. Cada solicitação referencia o usuário que a abriu; a exclusão desse usuário é restrita para não apagar o vínculo histórico. Status e categorias usam valores controlados no banco, além das validações na API. Índices apoiam consultas por status, categoria, data e solicitante.

Os totais do painel são calculados a partir dos registros, sem uma tabela de contadores que pudesse ficar dessincronizada. O código visível usa o identificador da solicitação com prefixo (`SOL-0001`), preservando um identificador inteiro simples no banco.

## 5. Regras e autenticação

O login consulta o usuário e verifica o hash da senha. A sessão é mantida em cookie assinado pelo Flask; o cookie é HTTP-only e SameSite Lax. O token CSRF é associado à sessão e enviado no cabeçalho das operações de escrita.

Solicitantes podem editar e excluir suas solicitações enquanto o status for Aberto. Gestores podem fazer o mesmo em solicitações abertas e mudar o status. A progressão permitida na interface é Aberto → Em Atendimento → Concluído; uma solicitação concluída não pode voltar ao fluxo. A API também verifica autorização, portanto a regra não depende apenas de controles visuais.

## 6. Interface e comunicação

O frontend é uma página servida pelo Flask. O JavaScript usa `fetch` para consumir endpoints JSON e atualiza a listagem, o painel e os diálogos sem recarregar a página. Falhas de validação aparecem junto aos formulários; falhas de operação são apresentadas em mensagens breves.

Os filtros de título, categoria, status e período são enviados à API. A API usa parâmetros SQL, valida os filtros e devolve somente as solicitações correspondentes.

## 7. Análise crítica e próximos passos

SQLite atende à demonstração local e a uma carga pequena, mas uma operação com múltiplas instâncias deve migrar para PostgreSQL e configurar migrações formais. O sistema ainda não possui redefinição de senha, cadastro administrativo de usuários, notificações, comentários, trilha de auditoria nem paginação. Também seria adequado adicionar limites contra tentativas repetidas de login, logs estruturados, backups testados e monitoramento antes de uma implantação pública.

O Compose usa uma chave local de conveniência quando nenhuma chave é informada. Em um deploy, deve-se fornecer um `SECRET_KEY` aleatório, ativar HTTPS e configurar `COOKIE_SECURE=true`. As contas demonstrativas são criadas apenas no primeiro banco vazio; credenciais de demonstração não devem ser mantidas em ambiente real.
