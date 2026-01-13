"""
Evaluation framework for measuring system performance.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import logging
from datetime import datetime
from pathlib import Path

from app.services.orchestrator import MultiAgentOrchestrator
from app.agents.state import QueryIntent

logger = logging.getLogger(__name__)


@dataclass
class EvaluationQuery:
    """A single evaluation query with expected results."""
    query: str
    expected_intent: QueryIntent
    expected_entities: List[str]
    ground_truth_answer: Optional[str] = None
    requires_numerical_accuracy: bool = False
    expected_sql_pattern: Optional[str] = None
    category: str = "general"


@dataclass
class EvaluationResult:
    """Result of evaluating a single query."""
    query: str
    category: str
    
    # Intent metrics
    predicted_intent: Optional[QueryIntent]
    expected_intent: QueryIntent
    intent_correct: bool
    
    # Entity extraction metrics
    predicted_entities: List[str]
    expected_entities: List[str]
    entity_precision: float
    entity_recall: float
    entity_f1: float
    
    # Execution metrics
    executed_successfully: bool
    sql_queries_generated: int
    errors: List[str]
    
    # Response quality
    response_length: int
    has_numerical_values: bool
    
    # Timing
    execution_time_seconds: float


class EvaluationFramework:
    """Framework for evaluating the multi-agent system."""
    
    def __init__(self, orchestrator: MultiAgentOrchestrator):
        self.orchestrator = orchestrator
        self.test_queries = self._load_test_queries()
    
    def _load_test_queries(self) -> List[EvaluationQuery]:
        """Load or create test queries."""
        return [
            # Lookup queries
            EvaluationQuery(
                query="What is Apple's market cap?",
                expected_intent=QueryIntent.LOOKUP,
                expected_entities=["AAPL", "Market_Cap"],
                requires_numerical_accuracy=True,
                category="lookup"
            ),
            EvaluationQuery(
                query="Show me Microsoft's revenue",
                expected_intent=QueryIntent.LOOKUP,
                expected_entities=["MSFT", "Revenue"],
                requires_numerical_accuracy=True,
                category="lookup"
            ),
            
            # Comparison queries
            EvaluationQuery(
                query="Compare the PE ratios of Apple and Microsoft",
                expected_intent=QueryIntent.COMPARISON,
                expected_entities=["AAPL", "MSFT", "PE_Ratio"],
                requires_numerical_accuracy=True,
                category="comparison"
            ),
            EvaluationQuery(
                query="Which has more employees, Google or Amazon?",
                expected_intent=QueryIntent.COMPARISON,
                expected_entities=["GOOGL", "AMZN", "Employees"],
                requires_numerical_accuracy=True,
                category="comparison"
            ),
            
            # Aggregation queries
            EvaluationQuery(
                query="What's the average market cap in the technology sector?",
                expected_intent=QueryIntent.AGGREGATION,
                expected_entities=["Market_Cap", "Sector"],
                requires_numerical_accuracy=True,
                category="aggregation"
            ),
            EvaluationQuery(
                query="How many companies are in the healthcare sector?",
                expected_intent=QueryIntent.AGGREGATION,
                expected_entities=["Sector"],
                requires_numerical_accuracy=True,
                category="aggregation"
            ),
            
            # Ranking queries
            EvaluationQuery(
                query="Show me the top 5 companies by revenue",
                expected_intent=QueryIntent.RANKING,
                expected_entities=["Revenue"],
                requires_numerical_accuracy=True,
                category="ranking"
            ),
            EvaluationQuery(
                query="Which 3 companies have the highest dividend yield?",
                expected_intent=QueryIntent.RANKING,
                expected_entities=["Dividend_Yield"],
                requires_numerical_accuracy=True,
                category="ranking"
            ),
            
            # Filter queries
            EvaluationQuery(
                query="List all companies with market cap over 1 trillion",
                expected_intent=QueryIntent.FILTER,
                expected_entities=["Market_Cap"],
                requires_numerical_accuracy=True,
                category="filter"
            ),
            EvaluationQuery(
                query="Which tech companies have PE ratio less than 20?",
                expected_intent=QueryIntent.FILTER,
                expected_entities=["Sector", "PE_Ratio"],
                requires_numerical_accuracy=True,
                category="filter"
            ),
            
            # Correlation queries
            EvaluationQuery(
                query="Is there a correlation between revenue and number of employees?",
                expected_intent=QueryIntent.CORRELATION,
                expected_entities=["Revenue", "Employees"],
                category="correlation"
            ),
        ]
    
    def run_evaluation(self) -> Dict[str, Any]:
        """
        Run full evaluation on test queries.
        
        Returns:
            Dict with evaluation metrics
        """
        logger.info("Starting evaluation...")
        
        results = []
        start_time = datetime.now()
        
        for test_query in self.test_queries:
            logger.info(f"Evaluating: {test_query.query}")
            
            # Reset conversation for each query
            self.orchestrator.reset_conversation()
            
            # Evaluate query
            result = self._evaluate_single_query(test_query)
            results.append(result)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Compute aggregate metrics
        metrics = self._compute_aggregate_metrics(results, total_time)
        
        # Save results
        self._save_results(results, metrics)
        
        logger.info("Evaluation complete")
        return metrics
    
    def _evaluate_single_query(self, test_query: EvaluationQuery) -> EvaluationResult:
        """Evaluate a single query."""
        import time
        
        start_time = time.time()
        
        try:
            # Process query
            response = self.orchestrator.process_query(test_query.query)
            
            execution_time = time.time() - start_time
            
            # Extract metrics from response
            predicted_intent_str = response.get("detected_intent")
            predicted_intent = QueryIntent(predicted_intent_str) if predicted_intent_str else None
            
            # Get entities from orchestrator state (would need to expose this)
            # For now, extract from response
            predicted_entities = self._extract_entities_from_response(response)
            
            # Compute entity metrics
            entity_metrics = self._compute_entity_metrics(
                predicted_entities,
                test_query.expected_entities
            )
            
            # Check for numerical values
            has_numerical = any(char.isdigit() for char in response.get("response", ""))
            
            result = EvaluationResult(
                query=test_query.query,
                category=test_query.category,
                predicted_intent=predicted_intent,
                expected_intent=test_query.expected_intent,
                intent_correct=(predicted_intent == test_query.expected_intent),
                predicted_entities=predicted_entities,
                expected_entities=test_query.expected_entities,
                entity_precision=entity_metrics["precision"],
                entity_recall=entity_metrics["recall"],
                entity_f1=entity_metrics["f1"],
                executed_successfully=len(response.get("errors", [])) == 0,
                sql_queries_generated=len(response.get("query_results", [])),
                errors=response.get("errors", []),
                response_length=len(response.get("response", "")),
                has_numerical_values=has_numerical,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            logger.error(f"Evaluation failed for query '{test_query.query}': {e}")
            result = EvaluationResult(
                query=test_query.query,
                category=test_query.category,
                predicted_intent=None,
                expected_intent=test_query.expected_intent,
                intent_correct=False,
                predicted_entities=[],
                expected_entities=test_query.expected_entities,
                entity_precision=0.0,
                entity_recall=0.0,
                entity_f1=0.0,
                executed_successfully=False,
                sql_queries_generated=0,
                errors=[str(e)],
                response_length=0,
                has_numerical_values=False,
                execution_time_seconds=time.time() - start_time
            )
        
        return result
    
    def _extract_entities_from_response(self, response: Dict) -> List[str]:
        """Extract entities from response (simplified)."""
        entities = []
        
        # Extract from SQL queries
        for qr in response.get("query_results", []):
            sql = qr.get("sql_query", "")
            # Simple extraction - in production would be more sophisticated
            for col in qr.get("columns", []):
                if col not in entities:
                    entities.append(col)
        
        return entities
    
    def _compute_entity_metrics(
        self, 
        predicted: List[str], 
        expected: List[str]
    ) -> Dict[str, float]:
        """Compute precision, recall, F1 for entity extraction."""
        if not expected:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        
        predicted_set = set(p.lower() for p in predicted)
        expected_set = set(e.lower() for e in expected)
        
        true_positives = len(predicted_set & expected_set)
        
        precision = true_positives / len(predicted_set) if predicted_set else 0.0
        recall = true_positives / len(expected_set) if expected_set else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    
    def _compute_aggregate_metrics(
        self, 
        results: List[EvaluationResult], 
        total_time: float
    ) -> Dict[str, Any]:
        """Compute aggregate metrics across all results."""
        total = len(results)
        
        metrics = {
            "total_queries": total,
            "total_time_seconds": total_time,
            "avg_time_per_query": total_time / total if total > 0 else 0,
            
            # Intent metrics
            "intent_accuracy": sum(r.intent_correct for r in results) / total,
            
            # Entity metrics
            "avg_entity_precision": sum(r.entity_precision for r in results) / total,
            "avg_entity_recall": sum(r.entity_recall for r in results) / total,
            "avg_entity_f1": sum(r.entity_f1 for r in results) / total,
            
            # Execution metrics
            "success_rate": sum(r.executed_successfully for r in results) / total,
            "avg_sql_queries": sum(r.sql_queries_generated for r in results) / total,
            
            # Response quality
            "avg_response_length": sum(r.response_length for r in results) / total,
            "numerical_response_rate": sum(r.has_numerical_values for r in results) / total,
            
            # By category
            "by_category": {}
        }
        
        # Category breakdowns
        categories = set(r.category for r in results)
        for cat in categories:
            cat_results = [r for r in results if r.category == cat]
            cat_total = len(cat_results)
            
            metrics["by_category"][cat] = {
                "count": cat_total,
                "intent_accuracy": sum(r.intent_correct for r in cat_results) / cat_total,
                "success_rate": sum(r.executed_successfully for r in cat_results) / cat_total,
            }
        
        return metrics
    
    def _save_results(self, results: List[EvaluationResult], metrics: Dict[str, Any]):
        """Save evaluation results to file."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "results": [
                {
                    "query": r.query,
                    "category": r.category,
                    "intent_correct": r.intent_correct,
                    "entity_f1": r.entity_f1,
                    "executed_successfully": r.executed_successfully,
                    "execution_time": r.execution_time_seconds,
                    "errors": r.errors
                }
                for r in results
            ]
        }
        
        output_path = Path("data/eval_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")