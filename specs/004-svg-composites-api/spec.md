# Feature Specification: SVG Composites & Image Generation API

**Feature Branch**: `004-svg-composites-api`  
**Created**: 2026-04-13  
**Status**: Draft  
**Phase**: 2.5 — Visual Richness  
**Input**: Phase 2.5 specification (SVG Composites + Image Generation API)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — SVG Composite Engine Automático (Priority: P1)

Desenvolvedores e agentes AI necessitam de composições SVG automáticas coerentes com o tema para evitar que apresentações fiquem visualmente vazias ou monótonas.

**Why this priority**: Composições SVG são a base visual offline-first que não depende de APIs externas. P1 porque sem composições, slides genéricos carecem de riqueza visual.

**Independent Test**: Um slide qualquer pode ser renderizado com fundo SVG coerente (cores da paleta, padrão baseado em seção 10 de DESIGN.md). Isso entrega valor mesmo sem image generation estar implementado.

**Acceptance Scenarios**:

1. **Given** um slide de tipo "content" com tema "linear", **When** SVGComposer.compose("section-divider", theme, slide_context) é invocado, **Then** retorna SVG válido contendo gradiente mesh de 2 cores da paleta + padrão geométrico (≤20 KB gzip)
2. **Given** um slide de tipo "title" com tema "linear", **When** SVGComposer.compose("hero-background", theme, ...) é invocado, **Then** retorna SVG com wave abstrata minimalista respeitando paleta
3. **Given** um erro na renderização (ex: path inválido), **When** SVGComposer.compose() captura exceção, **Then** retorna SVG mínimo (fundo sólido + gradiente simples), loga warning, e build continua

---

### User Story 2 — Image Generation API Engine (Priority: P2)

Agentes AI e usuários CLI necessitam gerar imagens automaticamente para slides via API gratuita (Pollinations) ou paga (OpenAI) ou gratuita (Unsplash) para que apresentações ganhem fotografias e ilustrações relevantes sem trabalho manual.

**Why this priority**: P2 porque enriquece visualmente além de composições SVG, mas Pollinations free é suficiente para MVP; OpenAI/Stability são opt-in. Requer caching para reutilização eficiente.

**Independent Test**: Um deck com --enrich flag pode gerar imagens via Pollinations (gratuito, sem API key). Cache funciona: rebuild subsequente é 95% mais rápido. Fallback SVG é usado quando API falha.

**Acceptance Scenarios**:

1. **Given** um deck "marketing" com 10 slides e nenhum --image-provider especificado, **When** `aio build slides.md --enrich` executa, **Then** Pollinations.ai é acionado para slides enriquecíveis (título, comparação), cache é populado em `.aio/cache/images/`, build completa em ~15–30s
2. **Given** mesmo deck sem alterações, **When** rebuild executa, **Then** 8/8 imagens vêm do cache, build completa em <2s
3. **Given** Pollinations.ai indisponível (timeout > 5s), **When** enrich engine tenta gerar imagem, **Then** SVGComposer.compose("feature-illustration", ...) é acionado automaticamente, slide continua com elemento visual coerente, build não é bloqueado
4. **Given** --enrich --image-provider openai com OPENAI_API_KEY exportada, **When** build executa, **Then** DALL-E 3 é acionado, prompt_builder cria prompts aprimorados, imagens são cacheadas, budget estimado é mostrado antes de executar

---

### User Story 3 — Theme Integration: DESIGN.md Section 10 (Priority: P3)

Designers de temas necessitam definir preferências visuais (geométrico/orgânico/tech/minimal) em DESIGN.md seção 10 para que SVGComposer gere composições alinhadas à identidade visual do tema.

**Why this priority**: P3 porque customization de estilo é melhoria sobre defaults. MVP funciona com defaults (tech/geometric/sharp); seção 10 permite diferenciação.

**Independent Test**: Dois temas com seções 10 diferentes (linear: tech/geometric; dribble: organic/flowing) geram composições visualmente distintas ao mesmo tempo que respeitam suas paletas.

**Acceptance Scenarios**:

1. **Given** DESIGN.md seção 10 para tema "linear" (Visual Style Preference: tech, Pattern: geometric, Curvature: sharp), **When** SVGComposer.compose("abstract-art", linear_theme) executa, **Then** retorna padrão grid + retos (ângulos 90°)
2. **Given** DESIGN.md seção 10 para tema "dribble" (Visual Style Preference: organic, Pattern: flowing, Curvature: soft), **When** SVGComposer.compose("abstract-art", dribble_theme) executa, **Then** retorna ondas + círculos suavizados (bezier curves)
3. **Given** arquivo DESIGN.md com seção 10 formatada corretamente, **When** theme_loader.py lê arquivo, **Then** extrai Visual Style Preference, Pattern, Curvature, Animation Preference em theme_metadata['visual_config']

---

### User Story 4 — Caching & Performance (Priority: P4)

Usuários CLI necessitam que rebuilds subsequentes reutilizem imagens e composições em cache para que decks sejam regenerados rapidamente sem re-chamar APIs.

**Why this priority**: P4 porque otimização de performance não bloqueia funcionalidade base; cache hit reduz tempo em 95% mas MVP sem cache é aceitável.

**Independent Test**: Deck típico com cache hit completa rebuild em <2s vs. ~30s sem cache. Comando `aio build --cache-stats` mostra taxa de hit, tamanho, idade.

**Acceptance Scenarios**:

1. **Given** deck "quarterly-results.md" com 12 slides e primeira execução `aio build --enrich`, **When** build completa, **Then** 8 imagens são geradas via Pollinations (~20s total), cache salvo em `.aio/cache/images/`, arquivo `.aio/meta.json` registra hashes
2. **Given** mesmo deck sem alteração, **When** `aio build --enrich` executa segunda vez, **Then** enrich engine compara hashes de prompts contra cache, 8/8 hits encontrados, build completa em <2s, logs mostram "8 images from cache"
3. **Given** cache com 15 imagens antigas, **When** usuário executa `aio build --enrich --cache-clear-images`, **Then** `.aio/cache/images/` é esvaziado, próximo build regenera todas
4. **Given** cache populado para tema "linear" e usuário muda theme para "stripe", **When** `aio build --enrich` executa, **Then** prompts são idênticos (baseados em content, não theme), cache ainda é reutilizado, SVG composites são regenerados

---

### Edge Cases

- **Imagem extremamente grande (>5 MB raw)**: Truncar a 800px, JPEG 75% fallback para reduzir tamanho
- **Prompt vazio ou muito curto**: Usar default genérico ("Abstract business concept")
- **Timeout de rede durante enrich**: Log warning + fallback SVG, não falha build
- **Concorrência: 2 instâncias rodando enrich simultaneamente**: Usar file lock em `.aio/cache/` para evitar race conditions
- **Tema com paleta muito restrita**: SVGComposer reduz diversidade de padrões (graceful degradation)
- **Slide detectado como enriquecível, mas prompt_builder não consegue extrair contexto válido**: Fallback para SVG composite genérico
- **Provider Unsplash atinge rate limit**: Fall back para Pollinations, não para SVG

---

## Requirements *(mandatory)*

### Functional Requirements

**P1 — SVG Composite Engine**

- **FR-401**: SVGComposer deve suportar ≥8 composições: hero-background, feature-illustration, stat-decoration, section-divider, abstract-art, process-steps, comparison-split, grid-showcase
- **FR-402**: Cada primitiva (círculo, retângulo, path, wave, grid) deve aceitar dimensões e cores parametrizadas
- **FR-403**: Gradientes devem ser construídos dinamicamente a partir da paleta DESIGN.md (seção 3: Color Palette)
- **FR-404**: Padrões (dots, lines, mesh, noise) devem ser deterministicamente gerados (seed baseado em tema + tipo)
- **FR-405**: SVGComposer.compose() retorna string SVG válida ou raises VisualsException com fallback automático
- **FR-406**: Composições são inseridas via `<svg>` inline ou data-URI; máximo 20 KB por SVG
- **FR-407**: DESIGN.md seção 10 (Visual Style Preference) controla: geometric/organic/tech/minimal aplicado a padrões
- **FR-408**: Cada composição funciona como fundo (opacity/z-index gerido pelo CSS de tema)

**P2 — Image Generation API Engine**

- **FR-410**: Base ImageProvider abstrata com interface: check_api(), generate(prompt) → bytes
- **FR-411**: Provider Pollinations: GET image.pollinations.ai?prompt=X&width=800&height=450 (sem API key)
- **FR-412**: Provider OpenAI: POST /v1/images/generations com auth Bearer $OPENAI_API_KEY; sistema estima budget upfront (cost per image × N slides), exibe aviso ao usuário, e requer confirmação antes de gerar (resposta: Q1-A)
- **FR-413**: Provider Unsplash: photo search via API key, retry 3x, fallback a SVG ou Pollinations
- **FR-414**: Cache engine: SHA256(prompt + provider_name) → `.aio/cache/images/{hash}.jpg`
- **FR-415**: Prompt_builder analisa slide (título, bullets, contexto) → prompt estruturado
- **FR-416**: Embedder redimensiona (max 800px), converte JPEG 85%, embarca como data-URI
- **FR-417**: Enrich engine: heurística identifica slides enriquecíveis (tipos + contexto) via identify_enrichable_slides(deck)
- **FR-418**: Timeout 10s por imagem; 3 retries com backoff exponencial; fallback order é hardcoded: Pollinations (free) → OpenAI (paid) → Unsplash (free) → SVG composite (resposta: Q2-A, Q4-A)
- **FR-419**: Fallback automático para SVG composite se API indisponível ou falha
- **FR-420**: CLI flags: `--enrich`, `--image-provider {pollinations|openai|unsplash}`, `--cache-clear`, `--cache-stats`, `--cache-clear-images`

**P3 — Theme Integration**

- **FR-425**: DESIGN.md seção 10 deve incluir campos: Visual Style Preference (geometric/organic/tech/minimal), Pattern (grid/dots/lines/mesh/noise), Curvature (sharp/soft/mixed), Animation Preference (static/subtle/dynamic); para temas legados (sem seção 10), system auto-gera com defaults (tech/geometric/sharp/static)
- **FR-426**: Theme loader extrai seção 10 em dicionário estruturado theme_metadata['visual_config']
- **FR-427**: SVGComposer lê visual_config e aplica heurísticas (ex: tech → ângulos retos, organic → bezier curves)
- **FR-428**: Fallback: se seção 10 ausente, defaults são tech/geometric/sharp

**P4 — Caching & Performance**

- **FR-430**: Cache estrutura: `.aio/cache/images/{sha256_of_prompt}.jpg`, `.aio/cache/composites/{theme}_{type}.svg`
- **FR-431**: Metadata caching: `.aio/meta.json` rastreia versões de tema, prompt builder, versão AIO
- **FR-432**: Invalidação: se versão_aio muda, cache é descartado (breaking changes)
- **FR-433**: CLI: `--cache-clear`, `--cache-clear-images`, `--cache-stats`
- **FR-434**: Paralelização: até 4 requisições simultâneas a APIs (rate limiting), configurável via `.aio/config.yaml` como `parallel_requests: 4` (resposta: Q3-B)

### Key Entities

- **SVGComposite**: Representa uma composição SVG gerada — tipo (hero-background, etc.), tema, dimensões, conteúdo SVG
- **EnrichContext**: Per-slide enrichment state — prompt, seed, image_bytes, is_placeholder flag
- **ImageProvider**: Abstração para provedores de imagem — Pollinations, OpenAI, Unsplash
- **CacheEntry**: Cache metadata — hash do prompt, timestamp, tamanho, versão AIO que gerou

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

**P1 — SVG Composite Engine**

- **SC-401**: Todas as 8 composições renderizam sem erro em 100% dos 64 temas (0 falhas)
- **SC-402**: SVG output é válido segundo W3C (xmllint ou validador SVG online)
- **SC-403**: Tamanho médio composição ≤18 KB; 95º percentil ≤25 KB
- **SC-404**: Cores extraídas de paleta DESIGN.md com 100% precisão (hex match)
- **SC-405**: 8 SVG composite types renderizam consistentemente em todos 64 temas (visual diffs <1% pixel variation com baseline) — via automated SVG diffing (SVG → PNG → pixel comparison)
- **SC-406**: Performance: SVGComposer.compose() executa em <50 ms (P95)

**P2 — Image Generation API Engine**

- **SC-410**: Pollinations API responde em <8s (P95) e produz imagens 800x450 válidas
- **SC-411**: OpenAI DALL-E retorna B64 decodável em <30s; custo por imagem ≤$0.15
- **SC-412**: Cache hit reduz tempo em 95% (<100 ms vs. ~30s sem cache)
- **SC-414**: Fallback SVG é acionado em <500ms sem bloqueio
- **SC-415**: Deck 10-slide com Pollinations completa em <45s; OpenAI em <120s
- **SC-416**: Data-URIs base64 geram tamanho final <3 MB (10-slide deck típico)

**P3 — Theme Integration**

- **SC-425**: Todos os 64 temas contêm seção 10 completa (metadata visual_config extraível); legacy temas auto-generate defaults (tech/geometric/sharp/static), novo temas criados em Phase 2.5+ incluem seção 10 obrigatória
- **SC-426**: Visual config extraído com 100% precisão

**P4 — Caching & Performance**

- **SC-430**: Cache hit reduz rebuild time em 95% (<2s para deck típico vs. ~30s sem cache)
- **SC-431**: Cache size permanece <100 MB para 50+ decks (limpeza automática LRU)

---

## Assumptions

- **Pollinations.ai permanece gratuito e sem autenticação** — status monitorado; fallback a SVG se API descontinuar
- **OpenAI API requer chave válida em env ($OPENAI_API_KEY)** — documentado em README
- **Imagens geradas são adequadas sem moderação adicional** — assume prompts sensatos
- **Offline-first ainda é requisito** — data URIs base64 garantem acesso offline; cache local é confiável
- **Temas legados (sem seção 10 de DESIGN.md) recebem defaults automáticos** — sem breaking changes
- **SVG Composite rendering usa apenas primitivas puras (sem `<script>` tags)** — restrição de segurança Art. II mantida
- **Cache é local ao projeto** (`.aio/cache/`) — sem sincronização remota ou shared state
- **Estilo inferência da paleta**: Se theme não especifica visual config, defaults são tech/geometric/sharp

---

## Clarifications

### Session 2026-04-13

- Q1: Visual Regression Testing → A: 8 SVG types renderizam consistentemente em todos 64 temas (visual diffs <1% com baseline via SVG → PNG pixel comparison)
- Q2: SVG Composite MVP Scope → A: Todas 8 composições entregues em Phase 2.5 (hero-background, feature-illustration, stat-decoration, section-divider, abstract-art, process-steps, comparison-split, grid-showcase)
- Q3: Theme Legacy Migration → A: Geração automática com defaults (tech/geometric/sharp/static) para 64 temas legados; sem manual migration pré-requisite
- Q4: Third Image Provider → A: Unsplash (photo search API, free key) para complementar Pollinations (free) e OpenAI (paid)

---
