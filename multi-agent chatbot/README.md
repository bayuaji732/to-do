# Multi-Agent GenAI Chatbot over S&P 500 Dataset

A production-grade, multi-agent GenAI system for querying S&P 500 financial data using natural language.

## 🎯 Features

- **Multi-Agent Architecture**: Specialized agents for intent understanding, planning, data retrieval, analysis, visualization, and synthesis
- **Schema-Aware Querying**: Never hallucinates column names or makes up data
- **Conversation Memory**: Handles follow-up questions with context
- **Evaluation Framework**: Built-in evaluation system with test queries and metrics
- **RESTful API**: FastAPI backend for easy integration
- **Interactive UI**: Streamlit frontend for demo and testing
- **Visualization Support**: Automatic chart generation when appropriate

## 🏗️ Architecture

```
User Query
    ↓
Intent Agent (Understands user intent, extracts entities)
    ↓
Planning Agent (Creates execution plan)
    ↓
Execution Agents:
  - Data Retrieval Agent (Executes SQL queries)
  - Analysis Agent (Performs calculations)
  - Visualization Agent (Creates charts)
    ↓
Synthesis Agent (Generates final response)
    ↓
Response + Visualization
```

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key
- S&P 500 dataset from Kaggle

## 🚀 Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd multi-agent-chatbot
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Download dataset**

- Download from: https://www.kaggle.com/datasets/paytonfisher/sp-500-companies-with-financial-information
- Place `sp500_companies.csv` in `./data/` directory

5. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 🔧 Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
DATASET_PATH=./data/sp500_companies.csv
DUCKDB_PATH=./data/sp500.duckdb
API_HOST=0.0.0.0
API_PORT=8000
```

## 🏃 Running the System

**Terminal 1 - Start API:**

```bash
uvicorn app.main:app --reload
```

**Terminal 2 - Start Streamlit:**

```bash
streamlit run streamlit_app.py
```

Access the UI at: http://localhost:8501

## 📊 Example Queries

### Simple Lookup

- "What is Apple's market cap?"
- "Show me Microsoft's revenue"

### Comparisons

- "Compare revenue of Apple and Microsoft"
- "Which has more employees, Google or Amazon?"

### Aggregations

- "What's the average PE ratio in the technology sector?"
- "How many companies are in the healthcare sector?"

### Rankings

- "Top 5 companies by revenue"
- "Which 3 companies have the highest dividend yield?"

### Filtering

- "List all companies with market cap over 1 trillion"
- "Which tech companies have PE ratio less than 20?"

### Correlations

- "Is there a correlation between revenue and number of employees?"

### Visualizations

- "Show me a chart of top 10 companies by market cap"

## 🧪 Evaluation

Run the evaluation framework:

```bash
python run_evaluation.py
```

This will:

1. Execute test queries across different categories
2. Measure intent accuracy, entity extraction, and execution success
3. Save results to `data/eval_results.json`

### Evaluation Metrics

- **Intent Accuracy**: % of queries where intent was correctly identified
- **Entity F1 Score**: Precision and recall of entity extraction
- **Success Rate**: % of queries that executed without errors
- **Numerical Accuracy**: Whether responses contain expected numerical values

### Baseline Results (Iteration 0)

Results from initial evaluation will be saved and can be compared against future iterations.

## 📁 Project Structure

```
.
├── agents/
│   ├── state.py              # State definitions
│   ├── intent_agent.py       # Intent understanding
│   ├── planner_agent.py      # Query planning
│   ├── data_agent.py         # Data retrieval
│   ├── analysis_agent.py     # Numerical analysis
│   ├── visualization_agent.py # Chart generation
│   └── synthesis_agent.py    # Response generation
├── database/
│   ├── metadata.py           # Schema metadata
│   └── manager.py            # Database operations
├── evaluation/
│   └── evaluator.py          # Evaluation framework
├── api/
│   └── main.py              # FastAPI application
├── config.py                 # Configuration management
├── orchestrator.py           # Multi-agent orchestrator
├── streamlit_app.py          # Streamlit frontend
├── run_evaluation.py         # Evaluation runner
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🔍 Design Decisions

### 1. Multi-Agent Architecture

- **Separation of Concerns**: Each agent has a single, clear responsibility
- **Modularity**: Agents can be improved independently
- **Debuggability**: Easy to trace which agent caused issues

### 2. Schema-Aware Design

- **Explicit Metadata**: Complete schema defined in code
- **Validation**: All queries validated against schema before execution
- **No Hallucination**: LLM never guesses column names

### 3. LangGraph Orchestration

- **State Management**: Centralized state flows through all agents
- **Conditional Execution**: Agents execute based on dependencies
- **Error Recovery**: Errors captured at each step

### 4. DuckDB Backend

- **Performance**: Fast analytical queries
- **Simplicity**: No external database server needed
- **SQL Compatibility**: Standard SQL with extensions

### 5. Evaluation-First

- **Baseline**: Establish metrics from day one
- **Iteration**: Track improvements across versions
- **Objectivity**: Quantitative measures of quality

## 🎯 Success Criteria

✅ Correctly answers diverse queries about S&P 500 data  
✅ Handles follow-up questions with context  
✅ Never hallucinates financial data  
✅ Provides explainable responses with data sources  
✅ Measurable performance through evaluation framework

## 🔄 Iteration Process

1. **Run Evaluation**: `python run_evaluation.py`
2. **Analyze Results**: Review `data/eval_results.json`
3. **Identify Issues**: Look at failed queries and low-scoring categories
4. **Make Improvements**: Update agent prompts, add validation, enhance logic
5. **Re-evaluate**: Compare new results to baseline
6. **Document**: Track what changed and impact on metrics

## 🛡️ Guardrails

- SQL injection prevention (validated queries only)
- No destructive operations (SELECT only)
- Schema validation before execution
- Error handling at each agent
- Rate limiting (can be added via API)

## 🐛 Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View agent execution:

- Check console logs for each agent's decisions
- Review SQL queries in API response
- Examine `execution_plan` in state

## 📈 Future Enhancements

- [ ] Multi-turn complex queries
- [ ] Time-series analysis
- [ ] Company comparison matrices
- [ ] Export to PDF/Excel
- [ ] Real-time data updates
- [ ] User preferences/personalization
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run evaluation to ensure no regression
5. Submit pull request

## 📄 License

MIT License - see LICENSE file

## 👥 Authors

Built as a demonstration of production-grade GenAI system design principles.

## 🙏 Acknowledgments

- S&P 500 dataset from Kaggle
- OpenAI for LLM capabilities
- LangChain/LangGraph for agent orchestration
