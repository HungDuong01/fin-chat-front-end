from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from tqdm import tqdm
import concurrent
import PyPDF2
import os
import pandas as pd
import base64
from dotenv import load_dotenv
from pathlib import Path

# === Cách 1: Tự động trỏ đến .env nằm cùng thư mục
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)
api_key=os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

MAIN_STORE_ID = os.getenv("MAIN_STORE_ID")
USAGE_STORE_ID = os.getenv("USAGE_STORE_ID")
PRICING_STORE_ID = os.getenv("PRICING_STORE_ID")

current_dir = Path(__file__).parent.resolve()
dir_pdfs = current_dir / "pdfs"  # Thư mục chứa các file PDF
pdf_files = [os.path.join(dir_pdfs, f) for f in os.listdir(dir_pdfs)]


def search_pdf_with_query(query: str, vector_id):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": query}],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_id],
                "max_num_results": 5
            }],
            tool_choice="required"
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Lỗi khi tìm kiếm file:", e)
        return "Xin lỗi, mình không tìm được thông tin phù hợp từ tài liệu."

























































"""def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def generate_questions(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    prompt = (
        "Can you generate a question that can only be answered from this document?:\n"
        f"{text}\n\n"
    )

    response = client.responses.create(
        input=prompt,
        model="gpt-4o",
    )

    question = response.output[0].content[0].text

    return question

print(generate_questions(pdf_files[0]))

# Generate questions for each PDF and store in a dictionary
questions_dict = {}
#for pdf_path in pdf_files:
questions = generate_questions(pdf_files[0])
questions_dict[os.path.basename(pdf_files[0])] = questions
    

rows = []
for filename, query in questions_dict.items():
    rows.append({"query": query, "_id": filename.replace(".pdf", "")})

# Metrics evaluation parameters
k = 3
total_queries = len(rows)
correct_retrievals_at_k = 0
reciprocal_ranks = []
average_precisions = []

def process_query(row):
    query = row['query']
    expected_filename = row['_id'] + '.pdf'
    # Call file_search via Responses API
    response = client.responses.create(
        input=query,
        model="gpt-4o-mini",
        tools=[{
            "type": "file_search",
            "vector_store_ids": [MAIN_STORE_ID],
            "max_num_results": 3,
        }],
        tool_choice="required" # it will force the file_search, while not necessary, it's better to enforce it as this is what we're testing
    )
    # Extract annotations from the response
    annotations = None
    if hasattr(response.output[1], 'content') and response.output[1].content:
        annotations = response.output[1].content[0].annotations
    elif hasattr(response.output[1], 'annotations'):
        annotations = response.output[1].annotations

    if annotations is None:
        print(f"No annotations for query: {query}")
        return False, 0, 0

    # Get top-k retrieved filenames
    retrieved_files = [result.filename for result in annotations[:k]]
    if expected_filename in retrieved_files:
        rank = retrieved_files.index(expected_filename) + 1
        rr = 1 / rank
        correct = True
    else:
        rr = 0
        correct = False

    # Calculate Average Precision
    precisions = []
    num_relevant = 0
    for i, fname in enumerate(retrieved_files):
        if fname == expected_filename:
            num_relevant += 1
            precisions.append(num_relevant / (i + 1))
    avg_precision = sum(precisions) / len(precisions) if precisions else 0
    
    if expected_filename not in retrieved_files:
        print("Expected file NOT found in the retrieved files!")
        
    if retrieved_files and retrieved_files[0] != expected_filename:
        print(f"Query: {query}")
        print(f"Expected file: {expected_filename}")
        print(f"First retrieved file: {retrieved_files[0]}")
        print(f"Retrieved files: {retrieved_files}")
        print("-" * 50)
    
    
    return correct, rr, avg_precision


with ThreadPoolExecutor() as executor:
    results = list(tqdm(executor.map(process_query, rows), total=total_queries))

correct_retrievals_at_k = 0
reciprocal_ranks = []
average_precisions = []

for correct, rr, avg_precision in results:
    if correct:
        correct_retrievals_at_k += 1
    reciprocal_ranks.append(rr)
    average_precisions.append(avg_precision)

recall_at_k = correct_retrievals_at_k / total_queries
precision_at_k = recall_at_k  # In this context, same as recall
mrr = sum(reciprocal_ranks) / total_queries
map_score = sum(average_precisions) / total_queries

# Print the metrics with k
print(f"Metrics at k={k}:")
print(f"Recall@{k}: {recall_at_k:.4f}")
print(f"Precision@{k}: {precision_at_k:.4f}")
print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")
print(f"Mean Average Precision (MAP): {map_score:.4f}")"""