import tempfile
import streamlit as st
from langchain.document_loaders import PyMuPDFLoader
from tools.llama2 import loadllama
from tools.googlevertex import loadvertex
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import VertexAIEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.chains import SequentialChain



DB_FAISS_PATH = 'vectorstore/db_faiss'
DB_FAISS_PATH2 = 'vectorstore/db_faiss2'

class RAG:

    def __init__(self,uploaded_file, llm_choice):
        
        
        self.uploaded_file = uploaded_file
        self.llm_name = llm_choice

    def handlefileandingest(self):
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(self.uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        loader = PyMuPDFLoader(file_path=tmp_file_path)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=2046, chunk_overlap=512)
        data = text_splitter.split_documents(documents)

        if self.llm_name == "LLaMA :llama:":
            embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        elif self.llm_name == "PaLM :palm_tree:":
            api_k = 'Your API'
            embeddings = VertexAIEmbeddings(google_api_key=api_k,project="kpmg-poc")


        # Create a FAISS vector store and save embeddings
        db = FAISS.from_documents(data, embeddings)
        db.save_local(DB_FAISS_PATH)

        return 0
    
    
            
    def conversational_chat(self,query,top_k,max_o_t,tempr):
        
        if self.llm_name == "LLaMA :llama:":
            embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        elif self.llm_name == "PaLM :palm_tree:":
<<<<<<< HEAD
            api_k = 'Your API'
=======
            api_k = 'Your API KEY'
>>>>>>> dev
            embeddings = VertexAIEmbeddings(google_api_key=api_k,project="kpmg-poc")
        

        db = FAISS.load_local(DB_FAISS_PATH, embeddings)
        similarity_data = db.similarity_search(query)

        db_s_f = FAISS.from_texts([similarity_data[0].page_content] , embeddings)
        
        for i in range(top_k-1):
            db_s_i = FAISS.from_texts([similarity_data[i+1].page_content] , embeddings)
            db_s_f.merge_from(db_s_i)
        
        retriever = db_s_f.as_retriever()

        template = """Answer the question based only on the following legal document:
                          {context}

                        Question: {question}

                    Note to be specfic to the question and try to break down the problem 
                    in to small steps.

                    your answers are important for the success of our company
                        """
        prompt = ChatPromptTemplate.from_template(template)
        

        if self.llm_name == "LLaMA :llama:":
            model = loadllama.load_llm()
        elif self.llm_name == "PaLM :palm_tree:":
            model = loadvertex.load_llm(max_o_t,tempr)
        

        chain = (
                    {"context": retriever, "question": RunnablePassthrough()}
                    | prompt
                    | model
                    | StrOutputParser()
                    )
        answer = chain.invoke(query)
        
        return answer
    
    def tree_of_thought_risk_def(self,top_k,max_o_t,tempr):

        if self.llm_name == "LLaMA :llama:":
            embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        elif self.llm_name == "PaLM :palm_tree:":
            api_k = 'Your API'
            embeddings = VertexAIEmbeddings(google_api_key=api_k,project="kpmg-poc")
    
        db = FAISS.load_local(DB_FAISS_PATH, embeddings)
        
        similarity_data = db.similarity_search("Analyze risk assoicated with respect to defendent,(Please find the name of the defandant)")

        db_s_f = FAISS.from_texts([similarity_data[0].page_content] , embeddings)
        
        for i in range(top_k-1):
            db_s_i = FAISS.from_texts([similarity_data[i+1].page_content] , embeddings)
            db_s_f.merge_from(db_s_i)
        
        retriever1 = db_s_f.as_retriever()

        if self.llm_name == "LLaMA :llama:":
            model = loadllama.load_llm()
        elif self.llm_name == "PaLM :palm_tree:":
            model = loadvertex.load_llm(max_o_t,tempr)

        template ="""
                First State the name of the defendant, and the task is to analyze risk point w.r.t defandant POV :
                
                Analyze risk with respect to defandant POV {context}. 
                
                Indentify and list all risk factors involved in decending order of impact to the defandant.
                A:
                """

        prompt = PromptTemplate(
                    input_variables=["context"],
                    template = template                      
                )

        chain1 = LLMChain(
                    llm= model,
                    prompt=prompt,
                    output_key="Defendant_POV"
                )

        template ="""
                Step 2:
                Please refer to the following context: {context} while answering
                For each of the proposed risk factors, evaluate their potential. Consider their pros and cons, initial effort needed, implementation difficulty, potential challenges, and the expected outcomes. Assign a probability of success and a confidence level to each option based on these factors

                {Defendant_POV}

                A:"""

        prompt = PromptTemplate(
                    input_variables=["Defendant_POV","context"],
                    template = template                      
                )

        chain2 = LLMChain(
                    llm= model,
                    prompt=prompt,
                    output_key="review"
                )

        template ="""
                Step 3:
                Please refer to the following context: {context} while answering
                For each solution, deepen the thought process. Generate potential scenarios, strategies for implementation, any necessary partnerships or resources, and how potential obstacles might be overcome. Also, consider any potential unexpected outcomes and how they might be handled.

                {review}
                

                A:"""

        prompt = PromptTemplate(
                    input_variables=["review","context"],
                    template = template                      
                )

        chain3 = LLMChain(
                    llm= model,
                    prompt=prompt,
                    output_key="deepen_thought_process"
                )

        template ="""
                Final Conclusion:

                Based on the evaluations and scenarios, rank the solutions in order of promise. Provide a justification for each ranking and offer any final thoughts or considerations for each solution
                {deepen_thought_process}, with respect to the {context}

                A:"""

        prompt = PromptTemplate(
                    input_variables=["deepen_thought_process","context"],
                    template = template                      
                )

        chain4 = LLMChain(
                    llm= model,
                    prompt=prompt,
                    output_key="ranked_solutions"
                )

        overall_chain = SequentialChain(
                        chains=[chain1, chain2, chain3, chain4],
                        input_variables=["context"],
                        output_variables=["ranked_solutions"],
                        verbose=True
                        )
        context = similarity_data[0].page_content + similarity_data[1].page_content + similarity_data[2].page_content
        output = overall_chain.run({"context" : context})

        return output

        

        
        