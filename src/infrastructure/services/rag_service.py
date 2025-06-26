import threading
import time
from typing import Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import wikipedia
import ollama
import os
import tempfile
import shutil



class RAGService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RAGService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, voice_service):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.client = ollama.Client()
            self.model = "phi:latest"
            self.embedding = None
            self.initialization_thread = None
            self.is_ready = False
            self.temp_dir = tempfile.mkdtemp()
            self.wiki_cache = {}
            self.db_cache = {}
            self.voice_service = voice_service
            self.voice_service.set_interval(5)
            self.last_transcription = ""
            self.is_processing = False
            self.initialization_complete = threading.Event()
            
    def initialize(self):
        """Initialize the service in a background thread"""
        if self.initialization_thread is None or not self.initialization_thread.is_alive():
            self.initialization_thread = threading.Thread(target=self._initialize_background)
            self.initialization_thread.daemon = True
            self.initialization_thread.start()
            # Wait for initialization to complete
            self.initialization_complete.wait()
            
    def _initialize_background(self):
        """Background initialization of the service"""
        try:
            print("🔄 Initializing RAG service...")
            self.embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self.is_ready = True
            print("✅ RAG service initialized successfully")
            self.initialization_complete.set()
        except Exception as e:
            print(f"❌ Error initializing RAG service: {e}")
            self.is_ready = False
            self.initialization_complete.set()
            
    def wait_for_initialization(self, timeout=30):
        """Wait for the service to be ready"""
        if not self.initialization_complete.is_set():
            print("⏳ Waiting for service initialization...")
            if not self.initialization_complete.wait(timeout):
                raise TimeoutError("Service initialization timed out")
        if not self.is_ready:
            raise RuntimeError("Service initialization failed")
            
    def cleanup(self):
        """Clean up temporary files and resources"""
        try:
            # Clear processing state
            self.is_processing = False
            
            # Clean up temporary files
            if os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception as e:
                    print(f"⚠️ Warning: Could not remove temp directory: {e}")
                    
            # Clear caches
            self.wiki_cache.clear()
            self.db_cache.clear()
            
            # Reset state
            self.last_transcription = ""
            self.is_ready = False
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            
    def _llama_model(self, prompt: str) -> str:
        """Call the LLM model"""
        if not self.is_ready:
            return "Service is not ready yet. Please wait for initialization."
            
        try:
            print("🤖 Generating response from LLM...")
            response = self.client.generate(model=self.model, prompt=prompt)
            if isinstance(response, dict) and "response" in response:
                return response["response"]
            return str(response)
        except Exception as e:
            print(f"❌ Error in LLM: {e}")
            return "Sorry, I encountered an error while generating the answer."
        
    def _extract_topic(self, question: str) -> str:
        """Extract topic from question"""
        print(f"🔍 Extracting topic from: {question}")
        topic = question.replace("who is", "").replace("what is", "").replace("how does", "").strip()
        topic = topic.split("?")[0].strip()
        
        if len(topic.split()) > 5:
            print("🔍 Using LLM to extract topic...")
            prompt = f"i want to search in wikipedia about this question so i need you to give me the right search topic for it only 1 topic (return ONLY the topic, no other text): {question}"
            topic = self._llama_model(prompt).strip()
            
        print(f"📌 Extracted topic: {topic}")
        return topic
        
    def _get_wiki_content(self, topic: str) -> str:
        """Get Wikipedia content"""
        if topic in self.wiki_cache:
            print(f"📚 Using cached Wikipedia content for: {topic}")
            return self.wiki_cache[topic]
            
        try:
            print(f"🌐 Fetching Wikipedia content for: {topic}")
            page = wikipedia.page(topic)
            content = page.content
            self.wiki_cache[topic] = content
            return content
        except Exception as e:
            print(f"❌ Error getting Wikipedia content: {e}")
            return f"No information found about {topic}."
            
    def _get_vector_db(self, topic: str, content: str) -> Optional[Chroma]:
        """Get or create vector database"""
        if not self.is_ready:
            return None
            
        if topic in self.db_cache:
            print(f"📚 Using cached vector database for: {topic}")
            return self.db_cache[topic]
            
        try:
            print(f"🔍 Creating vector database for: {topic}")
            text_splitter = CharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
                separator="\n"
            )
            docs = text_splitter.create_documents([content])
            
            db_path = os.path.join(self.temp_dir, f"chroma_db_{topic.replace(' ', '_')}")
            vectordb = Chroma.from_documents(docs, self.embedding, persist_directory=db_path)
            self.db_cache[topic] = vectordb
            return vectordb
        except Exception as e:
            print(f"❌ Error creating vector database: {e}")
            return None
            
    def listen_for_question(self) -> str:
        """Listen for a question using voice input"""
        if not self.is_ready:
            return "Service is not ready yet. Please wait for initialization."
            
        try:
            print("👂 Listening for question...")
            self.voice_service.speak("I'm listening. Please ask your question.")
            
            # Reset state
            self.last_transcription = ""
            self.is_processing = False
            
            # Start new transcription
            self.last_transcription = self.voice_service.transcribe_live()
            print(f"📝 Detected: {self.last_transcription}")
            
            # Check if user wants to delete the transcription
            if "delete" in self.last_transcription.lower():
                print("🗑️ Deleting transcription...")
                self.last_transcription = ""
                self.voice_service.speak("Transcription deleted. Please ask your question again.")
                return self.listen_for_question()
                
            return self.last_transcription
        except Exception as e:
            print(f"❌ Error listening for question: {e}")
            return "Sorry, I encountered an error while listening for your question."
            
    def answer_question(self, question: str = None, speak: bool = True) -> str:
        """Answer a question using RAG and optionally speak the answer"""
        if not self.is_ready:
            return "Service is not ready yet. Please wait for initialization."
            
        try:
            # If no question is provided, listen for one
            if question is None:
                question = self.listen_for_question()
                if question.startswith("I couldn't hear") or question.startswith("Sorry"):
                    return question
                    
            print(f"🤔 Processing question: {question}")
            if speak:
                self.voice_service.speak("Give me a moment, I'm thinking.")
                
            # Extract topic and get content
            # topic = self._extract_topic(question)
            # wiki_content = self._get_wiki_content(topic)
            # vectordb = self._get_vector_db(topic, wiki_content)
            
            # if vectordb is None:
                # return "Error processing your question. Please try again."
                
            # Get relevant context
            # retriever = vectordb.as_retriever(search_kwargs={"k": 1})
            # relevant_docs = retriever.invoke(question)
            # context = "\n".join([doc.page_content for doc in relevant_docs])
            
            # Generate answer
            # prompt = f"""You are a helpful assistant.
            #     You are given a context and a question. You need to answer the question based on the context
            #     as you talk to your friend and make it to the point without alot of talk maximum 100 words at the worst case.
            #     Context: {context}\nQuestion: {question}"""
            
            prompt = f"""You are a helpful assistant.
                You are given a question. You need to answer the question based on the context
                as you talk to your friend and make it to the point without alot of talk maximum 30 words at the worst case.
                Question: {question}"""
            response = self.client.generate(model=self.model, prompt=prompt)
            answer = response['response'].strip()
            
            if speak:
                self.voice_service.speak(answer)
                
            return answer
            
        except Exception as e:
            print(f"❌ Error in answer_question: {e}")
            return f"Error: {str(e)}"
            
    def _thinking_feedback(self, speak: bool):
        """Provide periodic feedback while thinking"""
        while self.is_processing:
            if speak:
                self.voice_service.speak("I'm still thinking.")
            time.sleep(10)  # Wait 10 seconds before next feedback 