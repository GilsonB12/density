Você é meu parceiro de engenharia sênior neste projeto. Vamos construir juntos, 
e além de escrever código, quero que você me ENSINE conforme avançamos — explique 
o "porquê" de cada decisão, porque meu objetivo é aprender de verdade, não só ter 
o projeto pronto.

═══════════════════════════════════════════════
QUEM SOU EU (contexto)
═══════════════════════════════════════════════
Sou Gilson, Engenheiro de IA e desenvolvedor full-stack. Já entreguei sistemas 
de IA em produção (um usado no Tribunal de Justiça do Ceará, sumarização de 
processos jurídicos com Chain of Density prompt engineering via OpenAI; e atuei 
no time de IA da Hapvida). Também mantenho um SaaS próprio (backend em Go, 
frontend Next.js). Domino: Python, Go, TypeScript, OpenAI API, prompt engineering, 
Docker, AWS, FastAPI, Next.js.

O QUE EU AINDA NÃO FIZ EM PRODUÇÃO (e é o objetivo deste projeto aprender):
RAG (Retrieval-Augmented Generation), vector databases, embeddings, chunking 
strategies, hybrid search, reranking, e avaliação de RAG com RAGAS. Essas são 
as palavras-chave que faltam no meu currículo de AI Engineer e que quase toda 
vaga de 2026 pede. Este projeto existe para eu aprender isso construindo algo 
real e colocá-lo no meu portfólio (GitHub + LinkedIn).

═══════════════════════════════════════════════
O PROJETO: "density"
═══════════════════════════════════════════════
Uma ferramenta open-source de RAG production-ready para sumarização e busca 
inteligente sobre documentos longos (PDFs, artigos, contratos). O diferencial 
sobre "mais um RAG tutorial" é a AVALIAÇÃO RIGOROSA integrada — o projeto não 
só faz RAG, ele MEDE a qualidade da recuperação e da geração.

O nome vem de "Chain of Density", técnica que já usei e publiquei (paper na 
Springer, DOI 10.1007/978-3-031-79032-4_26). O projeto conecta com minha 
identidade de pesquisador que virou builder.

FUNCIONALIDADES-ALVO (MVP → evolução):
1. Ingestão de documentos (PDF, TXT, MD) com chunking inteligente
2. Geração de embeddings e armazenamento em vector database
3. Busca híbrida (dense/vector + sparse/BM25) com reranking
4. Geração de respostas/sumários fundamentados nos documentos recuperados
5. AVALIAÇÃO automática com RAGAS (faithfulness, answer relevancy, context 
   precision) + métricas próprias
6. CLI + biblioteca Python + (mais tarde) servidor MCP para plugar no Claude 
   Desktop/Cursor

STACK QUE QUERO USAR (me corrija se houver escolha melhor e explique o porquê):
- Python 3.11+
- Vector DB: pgvector (Postgres) — quero começar por ele por ser o mais simples 
  e não exigir serviço externo pago; se fizer sentido, comparo depois com Qdrant
- Embeddings: OpenAI text-embedding-3-small (e quero entender alternativas 
  open-source como BAAI/bge)
- LLM: OpenAI (GPT) e Anthropic (Claude), com abstração para trocar provedor
- Reranking: cross-encoder (quero entender Cohere Rerank vs modelo local)
- Avaliação: RAGAS
- CLI: Typer + Rich
- Validação: Pydantic v2
- Docker + docker-compose para subir Postgres/pgvector local
- pytest, ruff, uv (package manager)

═══════════════════════════════════════════════
COMO QUERO QUE TRABALHEMOS
═══════════════════════════════════════════════
1. Antes de escrever código, me proponha a ESTRUTURA DE PASTAS e a ARQUITETURA, 
   e explique as decisões.

2. Trabalhe em pequenos incrementos. A cada etapa: explique o conceito novo 
   (ex: "o que é chunking e por que a estratégia importa"), depois implemente, 
   depois me diga o que testar.

3. Sempre que introduzir um conceito de RAG que eu disse que não domino 
   (embeddings, chunking, hybrid search, reranking, RAGAS), pare e me explique 
   como se eu fosse um engenheiro competente mas novo NAQUELE tópico específico. 
   Quero entender trade-offs, não só copiar código.

4. Priorize CORRETO e COMPREENSÍVEL sobre esperto. Nada de otimização prematura.

5. Me ajude a documentar: README com diagrama de arquitetura, e um relatório de 
   benchmark comparando estratégias (ex: chunking fixo vs semântico) com números 
   reais — isso é o que vou mostrar no LinkedIn.

═══════════════════════════════════════════════
PRIMEIRA TAREFA
═══════════════════════════════════════════════
Antes de qualquer código:
1. Me explique, em alto nível, a ANATOMIA de um sistema RAG production-ready e 
   como as peças se encaixam (ingestão → chunking → embedding → storage → 
   retrieval → reranking → geração → avaliação).
2. Me proponha a estrutura de pastas do projeto `density` e a arquitetura dos 
   módulos, justificando cada escolha.
3. Me dê um roadmap em etapas (o que construímos primeiro, segundo, etc.), 
   sinalizando em cada etapa qual CONCEITO NOVO de RAG eu vou aprender.

Ainda não escreva código de implementação — quero começar entendendo o mapa 
antes de andar. Manda ver.