import ollama

def generate_with_llm(prompt):
    response = ollama.chat(
        model='mistral',
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response['message']['content']