# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Streamlit / API Client)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Server                         │
│                     (RESTful Endpoints)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Agent Orchestrator                    │
│                    (LangGraph Workflow)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Intent    │ │   Planner   │ │  Synthesis  │
│    Agent    │ │    Agent    │ │    Agent    │
└─────────────┘ └─────────────┘ └─────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    Data     │ │  Analysis   │ │    Viz      │
│   Retrieval │ │    Agent    │ │    Agent    │
└──────┬──────┘ └─────────────┘ └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│                  (DuckDB + Metadata)                         │
└─────────────────────────────────────────────────────────────┘
```

## Agent Details

### 1. Intent Agent

**Purpose**: Understand user query intent and extract entities

**Inputs**:

- User query (natural language)
- Conversation history
- Database schema

**Outputs**:

- Detected intent (lookup, comparison, aggregation, etc.)
- Extracted entities (companies, sectors, metrics)
- Ambiguities requiring clarification

**Key Responsibilities**:

- Parse natural language query
- Map to known intents
- Extract only schema-valid entities
- Identify ambiguities

### 2. Planner Agent

**Purpose**: Create execution plan to answer query

**Inputs**:

- Detected intent
- Extracted entities
- Database schema

**Outputs**:

- Step-by-step execution plan
- Agent assignments per step
- Dependencies between steps
- SQL queries (initial draft)

**Key Responsibilities**:

- Decompose complex queries
- Determine execution order
- Assign work to specialized agents
- Generate SQL templates

### 3. Data Retrieval Agent

**Purpose**: Execute SQL queries against database

**Inputs**:

- SQL queries from plan
- Database schema (for validation)

**Outputs**:

- Query results (DataFrames)
- Execution metadata
- Errors (if any)

**Key Responsibilities**:

- Validate SQL against schema
- Execute queries safely
- Return structured results
- Handle errors gracefully

### 4. Analysis Agent

**Purpose**: Perform numerical computations and analysis

**Inputs**:

- Query results from Data Retrieval
- Analysis requirements from plan

**Outputs**:

- Computed metrics (averages, sums, etc.)
- Statistical analyses
- Correlations
- Rankings

**Key Responsibilities**:

- Compute aggregations
- Perform comparisons
- Calculate statistics
- NO hallucinated math (all computed)

### 5. Visualization Agent

**Purpose**: Create charts and visualizations

**Inputs**:

- Query results
- Visualization requirements
- Data types

**Outputs**:

- Plotly chart configuration
- Chart data
- Chart HTML

**Key Responsibilities**:

- Determine appropriate chart type
- Create interactive visualizations
- Handle various data shapes
- Ensure readability

### 6. Synthesis Agent

**Purpose**: Generate final natural language response

**Inputs**:

- All query results
- Computed metrics
- User's original query

**Outputs**:

- Final response (natural language)
- Response metadata

**Key Responsibilities**:

- Combine results into coherent response
- Stay faithful to data
- Format numbers appropriately
- Provide context and explanations

## Data Flow

### Example: "What is Apple's market cap?"

```
1. User Query → Intent Agent
   └─> Intent: LOOKUP
   └─> Entities: ["AAPL", "Market_Cap"]
   └─> No ambiguities

2. Intent + Entities → Planner Agent
   └─> Step 1: DATA_RETRIEVAL
       SQL: SELECT name market_cap FROM sp500_companies WHERE Symbol = 'AAPL'
   └─> Step 2: SYNTHESIS
       Format and present result

3. Plan → Executor
   └─> Execute Step 1 (Data Retrieval Agent)
       Result: [{name: "Apple Inc.", market_Cap: 2800000}]
   └─> Execute Step 2 (Synthesis Agent)
       Generate response

4. Final Response
   └─> "Apple Inc.'s market cap is $2.8 trillion."
```

### Example: "Compare revenue of Apple and Microsoft"

```
1. User Query → Intent Agent
   └─> Intent: COMPARISON
   └─> Entities: ["AAPL", "MSFT", "Revenue"]

2. Intent + Entities → Planner Agent
   └─> Step 1: DATA_RETRIEVAL
       SQL: SELECT symbol, name, revenue FROM sp500_companies
            WHERE Symbol IN ('AAPL', 'MSFT')
   └─> Step 2: ANALYSIS
       Compare values, compute difference and percentage
   └─> Step 3: SYNTHESIS
       Present comparison

3. Plan → Executor
   └─> Step 1 results: 2 rows with revenue data
   └─> Step 2 results: {difference: X, pct_change: Y}
   └─> Step 3: Generate comparative response

4. Final Response
   └─> "Apple's revenue is $394B vs Microsoft's $212B.
        Apple's revenue is 86% higher."
```

## State Management

The system uses a shared `AgentState` TypedDict that flows through all agents:

```python
AgentState = {
    # Input
    "user_query": str,
    "conversation_history": List[Message],

    # Intent
    "detected_intent": QueryIntent,
    "entities_mentioned": List[str],
    "ambiguities": List[str],

    # Planning
    "execution_plan": List[ExecutionStep],

    # Execution
    "sql_queries": List[str],
    "query_results": List[DataFrame],
    "computed_metrics": Dict,

    # Visualization
    "chart_config": Dict,

    # Response
    "final_response": str,
    "response_metadata": Dict,

    # Error Handling
    "errors": List[str],
    "retry_count": int
}
```

## Database Layer

### Schema Metadata

- Explicitly defined in code
- Column names, types, units, descriptions
- Used by all agents for validation
- Never guessed or inferred

### DuckDB

- In-process SQL database
- Fast analytical queries
- Standard SQL support
- No external server needed

### Query Safety

- All queries validated before execution
- Only SELECT statements allowed
- Schema-aware validation
- Prevents SQL injection

## LangGraph Workflow

```python
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("intent", intent_agent)
workflow.add_node("planner", planner_agent)
workflow.add_node("executor", executor_node)
workflow.add_node("synthesis", synthesis_agent)

# Edges
workflow.set_entry_point("intent")
workflow.add_edge("intent", "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "synthesis")
workflow.add_edge("synthesis", END)
```

## Error Handling

Each agent handles errors independently:

- Errors stored in state
- Execution continues when possible
- Fallback responses provided
- User-friendly error messages

## Conversation Memory

- Stores last N messages
- Provides context to Intent Agent
- Enables follow-up questions
- Session-based (can be extended to persistent)

## Evaluation Framework

### Test Queries

- Predefined set covering all intent types
- Known expected results
- Ground truth for metrics

### Metrics

- Intent accuracy
- Entity extraction F1
- Execution success rate
- Numerical accuracy
- Response quality

### Baseline Comparison

- Save initial results as baseline
- Compare future iterations
- Track improvements
- Identify regressions

## Scalability Considerations

### Current Implementation

- Single-threaded execution
- In-memory state
- Local database
- Session-based memory

### Future Enhancements

- Parallel agent execution
- Distributed state (Redis)
- Scalable database (PostgreSQL)
- Persistent memory (Vector DB)
- Batch processing
- Caching layer

## Security

### Current Measures

- SQL injection prevention
- Query validation
- Read-only operations
- API rate limiting (can add)

### Production Additions

- Authentication/Authorization
- Audit logging
- Data encryption
- Input sanitization
- Resource quotas

## Performance

### Typical Query Latency

- Simple lookup: 1-2 seconds
- Complex analysis: 2-5 seconds
- With visualization: 3-6 seconds

### Bottlenecks

- LLM API calls (dominant)
- Multiple sequential agents
- Large result sets

### Optimizations

- Parallel agent execution where possible
- Result caching
- Prompt optimization
- Batch LLM calls
