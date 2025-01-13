
def generate_prompt(user_question, results):
    """
    Generates a prompt for OpenAI's LLM based on the user's question and retrieved documents.
    
    Args:
        user_question (str): The question posed by the user.
        results (list): A list of tuples where each tuple contains retrieved document data.
                        Example: [(id, content, distance), ...]
    
    Returns:
        str: The formatted prompt to send to OpenAI's API.
    """
    # Combine retrieved documents into a context string
    retrieved_texts = "\n\n".join([f"Document {i+1}: {result[1]}" for i, result in enumerate(results)])
    
    # Construct the prompt
    prompt = f"""
    You are a helpful assistant. Based on the following context, answer the question accurately:
    
    Context:
    {retrieved_texts}
    
    Question:
    {user_question}
    
    Answer:
    """
    return prompt

