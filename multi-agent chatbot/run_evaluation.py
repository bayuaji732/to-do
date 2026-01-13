"""
Script to run evaluation of the multi-agent system.
"""
import logging
import json
from pathlib import Path

from app.database.manager import DatabaseManager
from app.services.orchestrator import MultiAgentOrchestrator
from app.evaluation.evaluator import EvaluationFramework
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_metrics(metrics: dict):
    """Pretty print evaluation metrics."""
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    
    print(f"\n📊 Overall Metrics:")
    print(f"  Total Queries: {metrics['total_queries']}")
    print(f"  Total Time: {metrics['total_time_seconds']:.2f}s")
    print(f"  Avg Time/Query: {metrics['avg_time_per_query']:.2f}s")
    
    print(f"\n🎯 Intent Detection:")
    print(f"  Accuracy: {metrics['intent_accuracy']*100:.1f}%")
    
    print(f"\n🏷️  Entity Extraction:")
    print(f"  Precision: {metrics['avg_entity_precision']*100:.1f}%")
    print(f"  Recall: {metrics['avg_entity_recall']*100:.1f}%")
    print(f"  F1 Score: {metrics['avg_entity_f1']*100:.1f}%")
    
    print(f"\n✅ Execution:")
    print(f"  Success Rate: {metrics['success_rate']*100:.1f}%")
    print(f"  Avg SQL Queries: {metrics['avg_sql_queries']:.1f}")
    
    print(f"\n📝 Response Quality:")
    print(f"  Avg Length: {metrics['avg_response_length']:.0f} chars")
    print(f"  Numerical Response Rate: {metrics['numerical_response_rate']*100:.1f}%")
    
    print(f"\n📂 By Category:")
    for cat, cat_metrics in metrics['by_category'].items():
        print(f"  {cat.upper()}:")
        print(f"    Count: {cat_metrics['count']}")
        print(f"    Intent Accuracy: {cat_metrics['intent_accuracy']*100:.1f}%")
        print(f"    Success Rate: {cat_metrics['success_rate']*100:.1f}%")
    
    print("\n" + "="*60 + "\n")


def main():
    """Main evaluation runner."""
    logger.info("Starting evaluation run...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager = DatabaseManager(
            csv_path=settings.dataset_path,
            db_path=settings.duckdb_path
        )
        db_manager.initialize()
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = MultiAgentOrchestrator(db_manager)
        
        # Create evaluator
        logger.info("Creating evaluation framework...")
        evaluator = EvaluationFramework(orchestrator)
        
        # Run evaluation
        logger.info("Running evaluation on test queries...")
        metrics = evaluator.run_evaluation()
        
        # Print results
        print_metrics(metrics)
        
        # Compare with baseline if exists
        baseline_path = Path("data/eval_baseline.json")
        if baseline_path.exists():
            logger.info("Comparing with baseline...")
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
            
            print("\n📈 Comparison with Baseline:")
            print(f"  Intent Accuracy: {metrics['intent_accuracy']*100:.1f}% "
                  f"(Baseline: {baseline['metrics']['intent_accuracy']*100:.1f}%)")
            print(f"  Success Rate: {metrics['success_rate']*100:.1f}% "
                  f"(Baseline: {baseline['metrics']['success_rate']*100:.1f}%)")
            print(f"  Entity F1: {metrics['avg_entity_f1']*100:.1f}% "
                  f"(Baseline: {baseline['metrics']['avg_entity_f1']*100:.1f}%)")
        else:
            # Save as baseline
            logger.info("No baseline found, saving current results as baseline...")
            with open(baseline_path, 'w') as f:
                with open("data/eval_results.json", 'r') as src:
                    baseline_data = json.load(src)
                json.dump(baseline_data, f, indent=2)
            print("\n💾 Saved as baseline for future comparisons")
        
        # Cleanup
        db_manager.close()
        
        logger.info("Evaluation complete!")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()