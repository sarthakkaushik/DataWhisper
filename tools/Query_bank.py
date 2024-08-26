from langchain_openai import AzureOpenAIEmbeddings
import numpy as np
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()

aoai_api_key = os.getenv("AZURE_OPENAI_API_KEY") 
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
aoai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

embed_model = AzureOpenAIEmbeddings(
    model="text-embedding-ada-002",
    # deployment_name="text-embedding-ada-002",
    api_key=aoai_api_key, 
    azure_endpoint=aoai_endpoint,
    api_version=aoai_api_version,
)

class QuestionProcessor:
  def __init__(self, question_data) -> None:
      """
      Initialize the QuestionProcessor with question data and an embedding model.

      :param question_data: A list of dictionaries containing question data.
      :param embedder: An embedding model with methods `embed_documents` and `embed_query`.
      """
      self.question_data = question_data
      self.embedder = embed_model
      self.question_embeddings = self.embedder.embed_documents(
          [q["Question"] for q in self.question_data]
      )

  def find_similar_questions(self, query: str, top_n: int = 3) -> List[Dict[str, Any]]:

      query_embedding = self.embedder.embed_query(query)
      similarities = np.dot(query_embedding, np.array(self.question_embeddings).T)
      top_indices = similarities.argsort()[-top_n:][::-1]

      return [
          {
              "Id": self.question_data[i]["Id"],
              "Question": self.question_data[i]["Question"],
              "Described Steps": self.question_data[i]["Described Steps"],
              "Confidence": similarities[i]
          }
          for i in top_indices
      ]

def create_few_shot_prompt(similar_questions: List[Dict[str, Any]], confidence_threshold: float = 0.7) -> List[str]:

  return [
      f"Example: {index + 1}\nQuestion: {q['Question']}\nSteps to Find: {q['Described Steps']}"
      for index, q in enumerate(similar_questions) if q['Confidence'] > confidence_threshold
  ]

def format_examples(examples_list: List[str]) -> str:

  formatted_output = ""
  for i, example in enumerate(examples_list, 1):
      parts = example.split('\n', 2)
      question = parts[1].replace('Question:', '').strip()
      steps = parts[2].replace('Steps to Find:', '').strip()
      formatted_output += f"Example {i}:\nQuestion: {question}\nSteps to Find:\n{steps}\n\n"
  return formatted_output.strip()

