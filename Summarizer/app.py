import os
import argparse
import torch
from flask import Flask, request, jsonify, send_from_directory
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

# Set this environment variable BEFORE importing transformers
os.environ['TRANSFORMERS_NO_JAX'] = '1'

# --- 1. SETUP: Arguments & App Initialization ---
parser = argparse.ArgumentParser(description="Run the AI summary agent server.")
parser.add_argument('-p', '--port', type=int, default=5000, help="Port to run the server on.")
args = parser.parse_args()
app = Flask(__name__)

# --- 2. MODEL LOADING: Upgraded to Llama-3.2-1B-Instruct ---
print("Loading Llama-3.2-1B-Instruct model for synthesis... This may take several minutes.")
try:
    generator = pipeline(
        "text-generation",
        model="meta-llama/Llama-3.2-1B-Instruct",
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="auto"
    )
    print("Llama-3.2-1B-Instruct model loaded successfully!")
except Exception as e:
    print(f"FATAL ERROR: Could not load the Llama model. {e}");
    print("Ensure you have run 'huggingface-cli login' and have accepted the model's terms on its Hugging Face page.")
    exit()

# --- Semantic Search Model (for transcript extraction) ---
print("Loading Semantic Search model for extraction...")
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Semantic Search model loaded successfully!")
except Exception as e:
    print(f"FATAL ERROR: Could not load the embedding model. {e}"); exit()

# --- Transcript Pre-processing ---
TRANSCRIPT_PATH = "transcript.txt" 
transcript_sentences = []
transcript_embeddings = None

def preprocess_transcript():
    global transcript_sentences, transcript_embeddings
    print(f"Processing transcript from: {TRANSCRIPT_PATH}...")
    try:
        with open(TRANSCRIPT_PATH, 'r', encoding='utf-8') as f:
            full_text = f.read()
        sentences = [s.strip() for s in full_text.replace('\n', ' ').split('.') if len(s.strip()) > 15]
        if not sentences: print("WARNING: No sentences found in transcript."); return
        transcript_sentences = sentences
        print(f"Found {len(transcript_sentences)} sentences. Creating semantic embeddings...")
        transcript_embeddings = embedding_model.encode(transcript_sentences, convert_to_tensor=True)
        print("Transcript processed and vectorized successfully!")
    except FileNotFoundError:
        print(f"WARNING: '{TRANSCRIPT_PATH}' not found. Summaries will be generic.")
    except Exception as e:
        print(f"WARNING: Could not process transcript file. Error: {e}")

preprocess_transcript()

# --- 3. PROMPT ENGINEERING for Llama 3 Synthesis ---
def create_llama3_synthesis_prompt(topic, category, status, context):
    system_prompt = "You are an expert AI Teaching Assistant. Your task is to provide a clear, high-quality explanation of a specific academic concept."
    length_instruction = "Provide a smart explanation on the topic in 4-5 sentences."
    if context:
        user_prompt = f"""
        Use the following text from a lecture as your primary inspiration to explain the concept of '{topic}' from the subject '{category}'. The lecture text might be messy or incomplete. Synthesize this information with your own knowledge to create the best possible explanation. {length_instruction}

        Lecture Text: "{context}"
        """
    else:
        # Fallback if no context is found in the transcript
        user_prompt = f"Please provide an academic explanation the concept of '{topic}' within the subject of '{category}'. {length_instruction}"


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt.strip()},
    ]
    return generator.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


# --- 4. API ENDPOINT (Upgraded for Llama 3 Synthesis) ---
@app.route('/generate-summaries-batch', methods=['POST'])
def generate_summaries_batch():
    request_data = request.json
    print(f"Received a batch of {len(request_data)} summaries to generate.")
    try:
        prompts = []
        for item in request_data:
            topic = item.get('topic')
            status = item.get('status')
            category = item.get('category')
            context = ""
            
            if transcript_embeddings is not None and transcript_sentences:
                query_embedding = embedding_model.encode(topic, convert_to_tensor=True)
                cosine_scores = util.pytorch_cos_sim(query_embedding, transcript_embeddings)[0]
                top_results = torch.topk(cosine_scores, k=min(4, len(transcript_sentences)))
                context_sentences = [transcript_sentences[i] for i in top_results.indices]
                context = ". ".join(context_sentences)

            # Create the sophisticated Llama 3 prompt
            prompts.append(create_llama3_synthesis_prompt(topic, category, status, context))
        
        # Llama 3 pipeline handles the batch efficiently
        results = generator(prompts, max_new_tokens=512, do_sample=True, temperature=0.7, top_p=0.9)
        
        summaries = []
        for index, full_output in enumerate(results):
            generated_text = full_output[-1]['generated_text']
            summary = generated_text.replace(prompts[index], "").strip()
            summaries.append(summary)
            
        print("Batch generation complete.")
        return jsonify({"summaries": summaries})
        
    except Exception as e:
        print(f"FATAL Error during batch generation loop: {e}")
        return jsonify({"error": "An unexpected error occurred during summary generation."}), 500


# --- 5. Routes and Server Startup (Unchanged) ---
@app.route('/')
def serve_index(): return send_from_directory('.', 'index.html')
@app.route('/<path:path>')
def serve_static_files(path): return send_from_directory('.', path)
if __name__ == '__main__':
    port_to_use = args.port
    print(f"\n--- Your app is ready! Open this URL: http://127.0.0.1:{port_to_use} ---")
    app.run(host='0.0.0.0', port=port_to_use, debug=False)