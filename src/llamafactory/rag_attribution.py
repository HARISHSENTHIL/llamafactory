import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr
import matplotlib.pyplot as plt
import re
from llamafactory.webui.utils import create_ds_config
from llamafactory.webui.common import save_config


class Config:
    def __init__(self):
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
        self.QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
        self.DATASETS_BASE_DIR = os.getenv("DATASETS_BASE_DIR", "src/llamafactory/data2/datasets")

    def get_collection_name(self, dataset_name: str) -> str:
        """Generate unique collection name for each dataset"""
        return f"signals_collection_{dataset_name}"

    @classmethod
    def setup(cls):
        """Setup OpenAI client"""
        config = cls()
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        return OpenAI(api_key=config.OPENAI_API_KEY)

# Data Manager Class
class DataManager:
    def __init__(self, datasets_dir: str):
        self.datasets_dir = Path(datasets_dir)
        self.datasets = {}
        self.load_available_datasets()

    def load_available_datasets(self) -> Dict[str, str]:
        """Load all available JSON datasets"""
        if not self.datasets_dir.exists():
            os.makedirs(self.datasets_dir)
            
        self.datasets = {
            f.stem: str(f) for f in self.datasets_dir.glob("*.json")
        }
        return self.datasets

    def get_dataset_path(self, dataset_name: str) -> Optional[str]:
        """Get path for a specific dataset"""
        return self.datasets.get(dataset_name)

    def load_dataset_content(self, dataset_name: str) -> List[Dict]:
        """Load and validate dataset content"""
        dataset_path = self.get_dataset_path(dataset_name)
        if not dataset_path:
            raise ValueError(f"Dataset {dataset_name} not found")

        try:
            with open(dataset_path, 'r') as f:
                signals = json.load(f)
                if not isinstance(signals, list):
                    raise ValueError(f"Dataset {dataset_name} is not a valid JSON array")

                # Validate and format signals
                formatted_signals = []
                for signal in signals:
                    if not isinstance(signal, dict) or not all(key in signal for key in ['content', 'user', 'channel']):
                        continue
                    
                    formatted_signal = {
                        'content': signal['content'],
                        'metadata': {
                            'user': signal['user'],
                            'channel': signal['channel'],
                            'dataset': dataset_name
                        }
                    }
                    formatted_signals.append(formatted_signal)

                return formatted_signals

        except Exception as e:
            print(f"Error loading dataset {dataset_name}: {str(e)}")
            return []

# Index Manager Class
class IndexManager:
    def __init__(self, config):
        self.config = config
        self.client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.current_collection = None
        self.current_dataset = None

    def get_embedding(self, text: str) -> List[float]:
        """Get embeddings from OpenAI"""
        response = self.openai_client.embeddings.create(
            input=text,
            model=self.config.EMBEDDING_MODEL
        )
        return response.data[0].embedding

    def create_collection(self, collection_name: str):
        """Create a new collection with schema"""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )

    def process_and_store_signals(self, signals: List[Dict], dataset_name: str) -> bool:
        """Process signals and store directly in Qdrant"""
        try:
            self.current_dataset = dataset_name
            self.current_collection = f"signals_collection_{dataset_name}"

            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(collection.name == self.current_collection for collection in collections)
            
            if not exists:
                print(f"Creating new Qdrant collection for dataset {dataset_name}...")
                self.create_collection(self.current_collection)

            # Process and store signals in batches
            batch_size = 100
            points = []
            
            for idx, signal in enumerate(signals):
                # Create embedding for the content
                content = signal['content']
                embedding = self.get_embedding(content)

                # Create point for Qdrant
                point = PointStruct(
                    id=idx,
                    vector=embedding,
                    payload={
                        "content": content,
                        "user": signal['metadata']['user'],
                        "channel": signal['metadata']['channel'],
                        "dataset": dataset_name
                    }
                )
                points.append(point)

                # Upload batch if size reached
                if len(points) >= batch_size:
                    self.client.upsert(
                        collection_name=self.current_collection,
                        points=points
                    )
                    points = []
                    print(f"Processed {idx + 1} signals...")

            # Upload remaining points
            if points:
                self.client.upsert(
                    collection_name=self.current_collection,
                    points=points
                )

            print(f"Successfully processed and stored {idx + 1} signals for dataset {dataset_name}")
            return True

        except Exception as e:
            print(f"Error processing signals for dataset {dataset_name}: {str(e)}")
            return False

    def search(self, query: str, limit: int = 3) -> List[dict]:
        """Search for similar documents in current collection"""
        if not self.current_collection:
            raise ValueError("No dataset selected")
            
        try:
            query_embedding = self.get_embedding(query)

            search_results = self.client.search(
                collection_name=self.current_collection,
                query_vector=query_embedding,
                limit=limit,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="dataset",
                            match=models.MatchValue(value=self.current_dataset)
                        )
                    ]
                )
            )
            
            results = []
            for result in search_results:
                formatted_text = (
                    f"Content: {result.payload['content']}\n"
                    f"User: {result.payload['user']}\n"
                    f"Channel: {result.payload['channel']}"
                )
                results.append({
                    "text": formatted_text,
                    "weight": float(result.score) * 100,
                    "metadata": {
                        "user": result.payload["user"],
                        "channel": result.payload["channel"],
                        "dataset": result.payload["dataset"]
                    }
                })
            return results
            
        except Exception as e:
            print(f"Error searching index: {str(e)}")
            return []

# Query Processor Class
class QueryProcessor:
    def __init__(self, index_manager, config):
        self.index_manager = index_manager
        self.config = config
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    @staticmethod
    def apply_confidence_decay(citations: List[Dict]) -> List[Dict]:
        """Apply confidence decay to citation weights"""
        total_score = 0
        decayed_citations = []

        for i, citation in enumerate(citations):
            decayed_score = citation['weight'] * (1 / (i + 1))
            boost_factor = 1.5 if "web" in citation['text'].lower() else 1.0
            adjusted_score = decayed_score * boost_factor
            total_score += adjusted_score

            decayed_citations.append({
                'text': citation['text'],
                'weight': adjusted_score
            })

        for citation in decayed_citations:
            citation['weight'] = round((citation['weight'] / total_score) * 100, 2)

        return decayed_citations

    def process_query(self, query: str) -> Tuple[str, List[Dict]]:
        """Process query and return response with citations"""
        citations = self.index_manager.search(query, limit=3)
        processed_citations = self.apply_confidence_decay(citations)
        context = "\n\n".join([f"Source {i+1}:\n{citation['text']}"
                              for i, citation in enumerate(processed_citations)])

        response = self.openai_client.chat.completions.create(
            model=self.config.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Use the provided sources to answer but do not reference or mention the sources in your response."},
                {"role": "user", "content": f"Based on these sources, answer this question without mentioning the sources: {query}\n\nSources:\n{context}"}
            ])

        return response.choices[0].message.content, processed_citations

# Visualizer Class
class Visualizer:
    @staticmethod
    def plot_contributions(citations: List[Dict[str, float]]) -> str:
        """Create a bar plot of contribution weights"""
        contributor_names = []
        for citation in citations:
            text = citation["text"]
            user_match = re.search(r"User: ([^\n]+)", text)
            channel_match = re.search(r"Channel: ([^\n]+)", text)

            user = user_match.group(1) if user_match else "Unknown"
            channel = channel_match.group(1) if channel_match else "Unknown"

            contributor_names.append(f"channel : {channel}\nUser : {user}")

        weights = [citation["weight"] for citation in citations]

        plt.figure(figsize=(8, 5))
        plt.bar(contributor_names, weights, color='Orange')
        plt.title("Top Contributors", fontsize=16, pad=15)
        plt.xlabel("Contributors", fontsize=12, labelpad=20)
        plt.ylabel("Weight (%)", fontsize=12)
        plt.ylim(0, 100)

        for i, weight in enumerate(weights):
            plt.text(i, weight + 1, f"{weight:.2f}%", ha='center', fontsize=10)

        plt.tight_layout(pad=1.5)
        plt.savefig("contributions_plot.png", bbox_inches='tight')
        plt.close()

        return "contributions_plot.png"

# Interface Class
class Interface:
    def __init__(self, query_processor: QueryProcessor, data_manager: DataManager):
        self.query_processor = query_processor
        self.data_manager = data_manager
        self.visualizer = Visualizer()
        self.current_dataset = None

    def handle_dataset_selection(self, dataset_name: str) -> str:
        """Handle dataset selection and processing"""
        try:
            signals = self.data_manager.load_dataset_content(dataset_name)
            if not signals:
                return f"Failed to load dataset {dataset_name}"

            success = self.query_processor.index_manager.process_and_store_signals(signals, dataset_name)
            if success:
                self.current_dataset = dataset_name
                return f"Dataset {dataset_name} loaded successfully"
            return f"Failed to process dataset {dataset_name}"
            
        except Exception as e:
            return f"Error processing dataset {dataset_name}: {str(e)}"
        
    def handle_query(self, query: str) -> Tuple[str, str, str]:
        """Handle user query and return formatted results"""
        if not self.current_dataset:
            return "Please select a dataset first.", "", ""

        response, citations = self.query_processor.process_query(query)
        citation_texts = "\n\n".join(
            [f"Weight: {citation['weight']}%\nSource: {citation['text']}"
             for citation in citations]
        )
        plot_path = self.visualizer.plot_contributions(citations)

        return response, citation_texts, plot_path
            
    def display_dataset(self) -> str:
        if not self.current_dataset:
            return "Please select a dataset first."
        try:
            signals = self.data_manager.load_dataset_content(self.current_dataset)
            samples = signals[:5]
            formatted_samples = json.dumps(samples, indent=2)
            return formatted_samples
        except Exception as e:
            return f"Error loading dataset samples: {str(e)}"

    def create_interface(self) -> gr.Blocks:
        with gr.Blocks() as ui:
            with gr.Row():
                gr.Image("src/llamafactory/data2/Rag Attribution 1.png", 
                        elem_classes="centered-image", show_download_button=False, show_fullscreen_button=False, show_label=False, scale=0.5)

            with gr.Row():
                dataset_dropdown = gr.Dropdown(
                    choices=list(self.data_manager.datasets.keys()),label="Select Dataset",elem_classes="spaced-dropdown")

            with gr.Row():
                input_box = gr.Textbox(
                    label="Enter your question",elem_classes="spaced-textbox",placeholder="E.g., Enter your Prompt")

            with gr.Row():
                response_box = gr.Textbox(
                    label="Response",placeholder="Model's Response",interactive=False)

            with gr.Row():
                citation_box = gr.Textbox(
                    label="Top 3 Citations with Weights",interactive=False)

            with gr.Row():
                plot_box = gr.Image(
                    label="Contribution Bar Graph",show_download_button=False, show_fullscreen_button=False)

            dataset_dropdown.change(
                fn=self.handle_dataset_selection,
                inputs=[dataset_dropdown],
                outputs=[response_box]
            )

            with gr.Row():
                submit_btn = gr.Button("Submit", variant="primary")
                dataset_btn = gr.Button("Show Dataset", variant="secondary")
                
            submit_btn.click(
                fn=self.handle_query,
                inputs=[input_box],
                outputs=[response_box, citation_box, plot_box]
            )
            
            with gr.Row():
                dataset_display = gr.Textbox(label="Dataset", interactive=False, max_lines=20)
                dataset_btn.click(
                    self.display_dataset,
                    inputs=[],
                    outputs=[dataset_display]
                )

        return ui


def create_rag_attribution_tab():
    with gr.Column():
        config = Config()
        Config.setup()

        data_manager = DataManager(config.DATASETS_BASE_DIR)
        index_manager = IndexManager(config)
        query_processor = QueryProcessor(index_manager, config)
        
        interface = Interface(query_processor, data_manager)
        return interface.create_interface()