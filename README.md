# Groq chatbots

    pip install -r requirements.txt
    cp .env.example .env      # then paste your key from console.groq.com

Simple chatbot:   python chatbot.py        (add --web for a browser page)

RAG chatbot:
    python rag_chatbot.py --index          (after adding files to docs/)
    python rag_chatbot.py                  (or --web)

Try: "What did Asha build at her internship?" then "What is her favourite food?"
The second one should get "I don't have that in my documents."
