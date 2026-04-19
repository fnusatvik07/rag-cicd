# Phase 8 - Telemetry (LangSmith)

## What is Telemetry?

Telemetry is collecting data about how your app behaves in production:
- How long does each request take?
- How many tokens are consumed per query?
- What prompts are being sent to the LLM?
- Where is the bottleneck: retrieval, reranking, or generation?
- Is the LLM hallucinating or giving bad answers?

Without telemetry, you're flying blind in production.

## Why LangSmith?

Our app uses LangChain (`langchain_openai`). LangSmith is built by the same team and integrates with zero code changes. It traces the entire RAG chain:

```
User asks "Compare Apple and Nike revenue"
  |
  v
LangSmith traces:
  [1] Agent: decompose_query (120ms, 85 tokens)
      Input:  "Compare Apple and Nike revenue"
      Output: ["What was Apple's total revenue?", "What was Nike's total revenue?"]
  
  [2] Retrieval: search("Apple revenue") (340ms)
      Results: 5 chunks, top score 0.91
  
  [3] Retrieval: search("Nike revenue") (280ms)
      Results: 5 chunks, top score 0.99
  
  [4] Reranker: rerank (450ms)
      Input: 10 chunks -> Output: 10 reranked
  
  [5] Generation: ChatOpenAI (1.2s, 350 tokens, $0.0004)
      Prompt: [system + context + question]
      Response: "Apple's revenue was $416B [1], Nike's was $46.3B [2]..."
  
  Total: 2.4s | 435 tokens | $0.0005
```

## What was added

### Zero code changes needed

LangChain automatically detects these environment variables:

```env
LANGCHAIN_TRACING_V2=true           # Enable tracing
LANGCHAIN_API_KEY=your-key          # LangSmith API key
LANGCHAIN_PROJECT=rag-classic       # Project name in dashboard
```

That's it. Every `ChatOpenAI` call, every chain, every retrieval is automatically traced.

### `app/config.py` - Added LangSmith config

```python
LANGSMITH_ENABLED: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGSMITH_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
LANGSMITH_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "rag-classic")
```

### `.env.example` - Added LangSmith variables

Shows what env vars to set for telemetry.

## Setup

1. Go to https://smith.langchain.com
2. Sign up (free tier: 5,000 traces/month)
3. Create a new API key: Settings -> API Keys -> Create
4. Add to your `.env`:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxx
LANGCHAIN_PROJECT=rag-classic
```

5. For Cloud Run, add to GitHub Secrets:
   - `LANGCHAIN_API_KEY`: your LangSmith key

6. Update deploy workflow to pass it:
```yaml
--set-env-vars "LANGCHAIN_TRACING_V2=true,LANGCHAIN_API_KEY=${{ secrets.LANGCHAIN_API_KEY }},LANGCHAIN_PROJECT=rag-classic"
```

## What the Dashboard Shows

### Trace View
Every request shows the full execution chain:
```
/chat "Compare Apple and Nike revenue"  [2.4s total]
  ├── decompose_query                   [120ms | 85 tokens]
  ├── search("Apple revenue")           [340ms]
  ├── search("Nike revenue")            [280ms]
  ├── rerank                            [450ms]
  └── ChatOpenAI.invoke                 [1.2s | 350 tokens | $0.0004]
```

### Metrics Over Time
- Request count per hour/day
- Average latency (p50, p95, p99)
- Token usage and cost
- Error rate
- Most common queries

### Debugging Bad Answers
Click any trace to see:
- Exact prompt sent to the LLM
- Exact response received
- Context chunks that were retrieved
- Reranking scores
- Whether the right context was found

## LangSmith vs Other Tools

| Tool | Best for | Pricing |
|------|----------|---------|
| **LangSmith** | LLM/chain tracing (we use LangChain) | Free: 5k traces/month |
| **Langfuse** | Same but open source, self-hostable | Free tier or self-host |
| **Datadog APM** | Infrastructure + application monitoring | $$$, enterprise |
| **Cloud Run metrics** | Basic request/latency/error dashboards | Free with GCP |
| **Helicone** | OpenAI-specific proxy logging | Free: 100k logs/month |

## Key Takeaways

1. **Zero code changes** - LangChain auto-detects env vars, no SDK to integrate
2. **Full chain visibility** - see every step: decompose, retrieve, rerank, generate
3. **Cost tracking** - know exactly how much each query costs in tokens
4. **Debug bad answers** - click a trace, see the prompt and context, find the problem
5. **Free tier is generous** - 5,000 traces/month is enough for dev and small production
6. **Enable/disable with one env var** - set `LANGCHAIN_TRACING_V2=false` to turn off
