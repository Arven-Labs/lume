# Desmontagem do Lume — Inventário e Opções de Migração

> Criado: 2026-10-14 (Sessão 22). Origem: `SPEC-lume-desmontagem.md` (raiz) + `SPEC-anchor-autossuficiencia.md`
> (repo do Anchor). **Só mapeamento** — nenhuma decisão de arquitetura foi confirmada com o dono do
> projeto; itens **[DIREÇÃO]** são hipóteses. Nada foi migrado, arquivado ou apagado.
> Levantado lendo o código dos dois repos (Lume e Anchor) e as docs do `project/` do Anchor/Warden.

---

## 1. O que o Lume é hoje

**Stack**: Python 3.14 + FastAPI, SQLAlchemy 2 + Alembic, `requests`. Banco: PostgreSQL 17 (Docker
Compose) **ou** SQLite (modo sidecar, mesma história de migrations; `services/db_dialect.py` escolhe
o `INSERT … ON CONFLICT` certo). Auth: lista estática de chaves em `API_KEYS` (header `X-API-Key`),
sem tabela/admin de chaves. Licença MIT.

**Componentes do repo**:
| Pasta | O que é | Tamanho aprox. |
|---|---|---|
| `api/app/` | FastAPI: 13 routers, ~14 services, ~25 módulos de `sources/`, 13 modelos (38 tabelas), schemas | ~7k linhas (sem testes) |
| `api/migrations/` | 10 migrations Alembic | |
| `api/tests/` | 41 arquivos de teste (pytest, fontes mockadas) | |
| `api/sidecar_main.py` | entrypoint do binário PyInstaller: roda migrations, escolhe porta livre, imprime `SIDECAR_PORT=<n>` | 75 linhas |
| `docs/` | site Next.js + Fumadocs; referência gerada do `/openapi.json` | |
| `docker-compose.yml` | `db` (Postgres), `api` (porta 8000), `docs` (porta 3000) | |
| `project/` | documentação do projeto (sessões 1–22) | |

**Padrão de cache**: cache-through sob demanda (sem scheduler). Três helpers genéricos —
`single_row_cache`, `append_only_list_cache`, `macro_series_service` — com TTL por categoria
(`config.py`: 1h padrão, cotação ação/cripto 5min, fundamentos 24h, opções 24h). Resposta sempre
traz `source`, `cached`, `stale`, `fetched_at`. Fonte fora do ar + cache vencido → devolve `stale`.

### 1.1 Capacidades expostas (contrato HTTP `/v1/...`)

| Domínio | Endpoints | Fonte(s) | Anchor consome? |
|---|---|---|---|
| Séries macro | `macro-series/{CDI\|IPCA…}` | BCB SGS | ✅ |
| Taxas | `rates/selic/{code}`, `rates/di-futures-curve/{data}` | BCB SGS, B3 taxa swap | ❌ |
| Ação BR | `stocks/{t}/quote, technicals, dividends-avg, price-history, dividend-payments, bolsai-fundamentals` | Yahoo, bolsai (chave) | ✅ |
| Empresas CVM | `companies/{cvm}/roe, payout, dcf-fundamentals, dividend-notices` | CVM DFP / IPE | ✅ |
| FII | `fiis/{cnpj}/monthly-indicators, properties`, `fiis/resolve/{ticker}` | CVM FII | ✅ |
| Ação/ETF/REIT EUA | `us-stocks/{t}/quote, technicals, dividends-avg, price-history, dividend-payments, fundamentals, dcf-fundamentals, payout, reit-fundamentals` | Yahoo, SEC EDGAR | ✅ |
| Cripto | `crypto/{sym}/quote, price-history`, `crypto/eth-indicators/{code}`, `crypto/fear-greed` | CoinGecko, DefiLlama, Coin Metrics, ultrasound.money, alternative.me | ✅ |
| Metais | `metals/{code}/quote, price-history` | Yahoo | ✅ |
| Índices B3 | `b3-indexes/{IFIX\|SMLL\|IDIV}/history` | B3 | ✅ |
| Câmbio | `currencies/{par}/quote, price-history` | Yahoo (`EURUSD=X`, confirmado) | ❌ |
| Opções | `options/{underlying}/series`, `options/{series}/greeks` | B3 séries + COTAHIST, Black-Scholes próprio | ❌ |
| Regras de IR | `tax-rules/br` | tabela estática no código | ❌ |
| Operacional | `GET /healthz` | — | usado só pelo sidecar |

**Fontes externas (13 hosts)**: api.bcb.gov.br, query1.finance.yahoo.com, dados.cvm.gov.br,
data.sec.gov / www.sec.gov, api.coingecko.com, api.llama.fi, community-api.coinmetrics.io,
ultrasound.money, api.alternative.me, www.b3.com.br / sistemaswebb3-listados.b3.com.br /
bvmf.bmfbovespa.com.br, api.usebolsai.com.
**Configuração sensível**: `BOLSAI_API_KEY` (única fonte paga/com chave), `SEC_EDGAR_CONTACT_EMAIL`
(exigido pela SEC no User-Agent), `API_KEYS`, `DATABASE_URL`.

---

## 2. Como o Anchor consome o Lume hoje (verificado no código)

Anchor = Tauri 2 (Rust, SeaORM, **SQLite**) + React (`desktop/`) + Flutter (`mobile/`).

- **Cliente tipado em Rust**: `desktop/src-tauri/src/finance_api/` (`client.rs` 757 linhas, um método
  por endpoint + DTOs; módulos por classe de ativo `stocks, us_stock, reit, fii, crypto, metals,
  benchmark`). `commands/collector.rs` e `commands/fii.rs` chamam esse client e **gravam no
  `anchor.db`** (o Anchor persiste o resultado; o cache do Lume é um segundo cache por baixo).
- **Ciclo de vida do sidecar** (`finance_api/sidecar.rs`):
  - *dev*: não sobe nada; assume `docker compose up` do Lume em `http://localhost:8000` com chave fixa
    `local-dev-key-change-me` (hardcoded; Anchor roda com `network_mode: host`).
  - *release*: spawna o binário `anchor-finance-api` (PyInstaller do `api/sidecar_main.py`), gera
    chave aleatória de 40 chars, banco **SQLite próprio** `finance_api.db` em `app_data_dir`, lê
    `SIDECAR_PORT=` do stdout, espera `/healthz` (15s), mata no `ExitRequested`.
- **CI**: `build.yml` do Anchor faz checkout do repo do Lume **fixado por SHA** (`.easybusiness-version`)
  e compila o sidecar. ← **dependência de build direta do repo do Lume.**
- **Settings Local/Remote** (Fase 14.3): tabela `finance_api_settings` + chave remota no keyring +
  UI em `FinanceApiSettingsSection.tsx`. **Gravada mas não lida** por `sidecar::init` (decisão
  consciente de escopo na época).
- **Fallback para instância do Warden** (Fase 21 do Anchor): decidido em direção, **não implementado**;
  "mecanismo de descoberta em aberto". Conflita com a porta dinâmica do sidecar.
- **Histórico**: o Anchor tinha um `data-collector/` Python; a Fase 14 (Sessões 89–92) o apagou
  inteiro e passou tudo para HTTP→Lume. A migração de agora é, em parte, o caminho inverso.
- **Mobile Flutter**: **não usa o Lume**; busca Yahoo/CoinGecko direto (`yahoo_quote_service.dart`,
  `coingecko_quote_service.dart`).
- **Contrato de erro que o Anchor depende**: 404 = "não tem esse dado" (vira `FinanceApiNotFound`, pulado
  por ticker); resto propaga. `fetched_at` precisa ser UTC (bug serde+chrono achado ao vivo).

### 2.1 Outros dependentes do Lume
- **Warden**: nenhuma referência no código; só docs (`CONTEXT.md` o chama de "outro produto";
  `SPEC-warden-router-e-futuro.md` confirma que o roteador de modelos **não** vai para o Lume). A
  expectativa de consumo é **via Anchor** (MCP ou HTTP — aberto).
- **TruthID**: nenhum.
- Respondendo a questão da spec ("algo além do Anchor depende?"): **código, não**. Só o Anchor.

---

## 3. Lacunas e riscos

1. **Divergência de linguagem** — Lume é Python/Postgres-ou-SQLite/SQLAlchemy; Anchor é Rust/SeaORM/
   SQLite. "Migrar" ≠ mover arquivos. É o ponto central da decisão (seção 4).
2. **Quatro domínios do Lume sem consumidor** (rates/DI, câmbio, opções+greeks, tax-rules): ou entram
   no escopo da migração, ou são descartados — decidir um a um.
3. **Cache duplicado**: Lume (cache-through com TTL e `stale`) + `anchor.db`. Na fusão, definir um só dono.
4. **Dev e CI acoplados** ao repo do Lume (porta 8000, chave fixa, SHA no CI). Qualquer caminho exige
   mexer nisso.
5. **Settings Local/Remote** e **fallback Warden** ficam sem sentido ou mudam de forma conforme o caminho.
6. **Docs públicas** (`docs/`, Fumadocs) — a API pública deixa de existir como produto? Pendente (req. 1/3 da
   spec do Anchor pedem API headless e hospedagem futura).
7. **Auth/hospedagem**: Lume tem só chave estática; o "tier hospedado pago" da spec do Anchor exigiria
   chave por consumidor/entitlement — hoje inexistente.
8. **Propriedade intelectual embutida em decisões**: lógica de negócio sutil acumulada (CNPJ só dígitos,
   retry por janela no BCB, mapeamento de taxonomia SEC, travas de catálogo). Reescrever sem portar os
   testes perde esses achados.
9. **Brainstorms** do `ROADMAP.md` (reposicionamento, régua de escopo, ingestão agendada, `DataProvider`)
   ficam em suspenso; decidir o que vira nota no Anchor.

---

## 4. Opções de migração (para discutir — nenhuma escolhida)

### Opção A — Mover o `api/` Python para dentro do repo do Anchor (monorepo, sem reescrever)
Estrutura **[DIREÇÃO]**: `anchor/{core-data (Python), desktop, mobile}`; o sidecar continua igual, mas o
build sai do mesmo repo (some o SHA e o checkout cruzado).
- ✅ Menor risco e esforço; preserva 41 testes e todos os achados; Anchor funciona sem mudar o client Rust.
- ✅ Respeita "poucos repositórios"; API headless já existe (é FastAPI).
- ❌ Anchor continua com dois runtimes (Rust + Python embutido) — o que a Fase 14 do Anchor justamente
  evitou localmente; binário PyInstaller pesado e CI mais lento.
- ❌ "Autossuficiente" só no sentido de repo, não de stack.

### Opção B — Reescrever o núcleo de dados em Rust (crate dentro do Anchor)
`anchor/crates/finance-core` (fontes + cache + modelos), `finance-server` (axum, API/MCP headless),
`desktop` consumindo o crate direto (sem HTTP interno).
- ✅ Um runtime só, sem sidecar/porta/chave/PyInstaller; some o fallback complicado; casa com SeaORM/SQLite.
- ✅ Núcleo sem dependência de UI (bate com a [DIREÇÃO] da spec do Anchor) e extraível depois.
- ❌ Maior esforço: ~7k linhas Python + 38 tabelas + parsers CVM/SEC; risco de regressão — mitigável
  portando os testes e comparando saídas lado a lado contra o Lume vivo.
- ❌ Perde o ecossistema Python (pandas, etc.) se o backtesting/quant (Fase 22 do Anchor) quiser.

### Opção C — Híbrido faseado
Passo 1: Opção A (consolida repos rápido, Lume já pode ser arquivado). Passo 2: reescrever em Rust por
domínio, na ordem de uso pelo Anchor, aposentando o sidecar aos poucos.
- ✅ Entrega a organização cedo e adia o custo grande; reversível.
- ❌ Dois estados intermediários para manter; precisa disciplina para o passo 2 acontecer.

### Decisões ortogonais (valem para qualquer opção)
- **Armazenamento**: banco próprio (`finance_api.db`) vs. tabelas dentro do `anchor.db` vs. só cache em memória/arquivo.
- **Exposição ao Warden**: MCP, HTTP ou ambos (Warden já tem client MCP pronto, P13).
- **Domínios sem consumidor** (seção 3.2): migrar, adiar ou descartar.
- **`DataProvider`** (grátis → BYO-key → premium): padrão a nascer já na migração ou depois?
  Hoje só bolsai usa chave; o resto é fonte pública fixa por service.
- **Settings Local/Remote** e **detecção de instância compartilhada**: provavelmente somem em B, ficam
  parcialmente em A/C.

---

## 5. Questões abertas da spec (estado)

| Questão | Estado |
|---|---|
| Preservar `DataProvider`? | Em aberto — só bolsai tem chave hoje; decidir junto com a opção A/B/C |
| Renomeação EasyBusiness → Lume | Provavelmente sem sentido (repo será descartado); **confirmar**. Observação: repo já migrou no GitHub para `Arven-Labs/lume`, e o código do Anchor ainda diz "easybusiness" em comentários/CI |
| Outro dependente além do Anchor | Verificado: nenhum em código (seção 2.1) |
| README com aviso de desmontagem | **Não feito — aguardando confirmação** |
| Arquivar/apagar o repo | Decisão exclusiva do dono, depois de validar o Anchor sozinho |

## 6. Próximos passos sugeridos
1. Dono escolhe A / B / C (ou outra) e responde as decisões ortogonais.
2. Detalhar o plano da opção escolhida (ordem por domínio, critérios de paridade, o que testar lado a lado).
3. Passar o plano ao agente do Anchor (a outra metade, alinhada com `SPEC-anchor-autossuficiencia.md`).
4. Só depois: aviso no README, validação por tempo, decisão de arquivar.
