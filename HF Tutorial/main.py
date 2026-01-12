from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers.utils.logging import set_verbosity_error

# Hide unnecessary warnings
set_verbosity_error()

# 1. Setup the Map for Length
# BART models need integer token counts for length control
length_map = {
    "short": {"max": 50, "min": 20},
    "medium": {"max": 100, "min": 40},
    "long": {"max": 200, "min": 80}
}

# 2. Initialize Pipelines
# Note: device=1 as per your original setup for GPU
summarization_pipeline = pipeline(
    "summarization", 
    model="facebook/bart-large-cnn", 
    device=1,
    do_sample=False
)
summarizer = HuggingFacePipeline(pipeline=summarization_pipeline)

qa_pipeline = pipeline(
    "question-answering", 
    model="deepset/roberta-base-squad2", 
    device=1
)

# 3. Create a clean chain
# We skip the "Refiner" step here because double-summarizing often causes 
# the repetitive "AI Engineer" bug you saw.
summary_template = PromptTemplate.from_template("{text}")
summarization_chain = summary_template | summarizer | StrOutputParser()

# --- INPUT SECTION ---
print("\n--- AI Document Assistant ---")
text_to_summarize = input("Enter text to summarize:\n> ")
length_input = input("\nEnter the length (short/medium/long): ").lower().strip()

# Default to medium if input is weird
lengths = length_map.get(length_input, length_map["medium"])

print("\n--- Processing Summary... ---")

# 4. Generate Summary with dynamic length
# We pass the max/min lengths directly to the model call
summary = summarization_chain.invoke(
    {"text": text_to_summarize},
    config={"max_length": lengths["max"], "min_length": lengths["min"]}
)

print("\n🔹 **Generated Summary:**")
print(summary)

# 5. Question & Answer Loop
print("\n--- Q&A Session (type 'exit' to quit) ---")
while True:
    question = input("\nAsk a question about the summary:\n> ")
    
    if question.lower() == "exit":
        print("Goodbye!")
        break

    if not question.strip():
        continue

    # Get answer from context
    qa_result = qa_pipeline(question=question, context=summary)

    print(f"\n🔹 **Answer:** {qa_result['answer']}")
    print(f" (Confidence: {round(qa_result['score'] * 100, 2)}%)")