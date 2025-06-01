from groq import Groq
import os

groq_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_key)

def ask_llm(context: str, question: str) -> str:
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-70b-8192",  # use your preferred model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Indian lawyer. Use the given context to answer the user's legal question "
                        "accurately and clearly. Do not answer beyond Indian law. If the answer is not in the context, say so."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {question}"
                }
            ]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ LLM error: {e}"
