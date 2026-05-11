from agents.qa_agent import QAAgent
from agents.summariser import SummariserAgent
from agents.reader import ReaderAgent

context = """
The Python programming language is known for its simplicity and readability. 
It was created by Guido van Rossum in 1989 and first released in 1991. 
Python supports multiple programming paradigms including object-oriented, 
functional, and procedural programming. The language has a large standard 
library and is widely used in web development, data science, artificial 
intelligence, and scientific computing. Python's syntax emphasizes code 
readability and allows developers to express concepts in fewer lines of code.
"""

print("=== Testing QAAgent ===")
qa_agent = QAAgent()
response = qa_agent.run("What is this document about?", context=context)
print(f"Question: What is this document about?")
print(f"Answer: {response}\n")

response2 = qa_agent.run("Who created Python and when?", context=context)
print(f"Question: Who created Python and when?")
print(f"Answer: {response2}\n")

response3 = qa_agent.run("What is the capital of France?", context=context)
print(f"Question: What is the capital of France?")
print(f"Answer: {response3}\n")

print("\n=== Testing SummariserAgent ===")
summariser = SummariserAgent()
summary = summariser.run("Summarize the provided content", context=context)
print(f"Summary:\n{summary}\n")

print("\n=== Testing ReaderAgent ===")
reader = ReaderAgent()
chunks = [
    {"text": "Section 1: Python Basics\nPython is simple.", "page_number": 1},
    {"text": "Section 2: Applications\nUsed in AI and web.", "page_number": 2},
]
extracted = reader.extract(chunks)
print(f"Extracted content:\n{extracted}\n")

print("[OK] All agent tests completed!")
