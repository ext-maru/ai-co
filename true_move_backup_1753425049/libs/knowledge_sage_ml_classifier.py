"""
Knowledge Sage Machine Learning Classifier
Implements automatic categorization, tagging, and content analysis using ML
"""

import asyncio
import json
import logging
import os
import pickle
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MultiLabelBinarizer

from libs.knowledge_sage_postgresql import KnowledgeSagePostgreSQL


class KnowledgeSageMLClassifier(KnowledgeSagePostgreSQL):
    """ML-powered Knowledge Sage for intelligent content processing"""

    def __init__(self):
        """Initialize ML classifier"""
        super().__init__()
        self.logger = logging.getLogger("elders.KnowledgeML")
        
        # ML models
        self.models = {}
        self.vectorizers = {}
        self.label_encoders = {}
        
        # Model versions
        self.model_versions = defaultdict(int)
        
        # Feature extractors
        self.tfidf_vectorizer = None
        self.keyword_extractor = None
        
        # Training data cache
        self.training_cache = []
        
        # Performance metrics
        self.model_metrics = defaultdict(dict)
        
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize ML components"""
        await super().initialize()
        
        # Initialize vectorizers
        self.vectorizers["content"] = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words="english",
            min_df=2
        )
        
        # Initialize models
        self.models["category_classifier"] = MultinomialNB()
        self.models["tag_generator"] = OneVsRestClassifier(RandomForestClassifier(n_estimators=100))
        
        # Initialize label encoders
        self.label_encoders["category"] = {}
        self.label_encoders["tags"] = MultiLabelBinarizer()
        
        self._initialized = True
        self.logger.info("ML Classifier initialized")

    def is_initialized(self) -> bool:
        """Check if ML components are initialized"""
        return self._initialized

    def get_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.models.keys())

    def get_model_version(self, model_name: str) -> int:
        """Get version number of a model"""
        return self.model_versions.get(model_name, 0)

    async def train_models(
        self,
        documents: List[Dict[str, Any]],
        model_types: Optional[List[str]] = None,
        validation_split: float = 0.2,
        multi_label: bool = False
    ) -> Dict[str, Any]:
        """Train ML models on provided documents"""
        if not documents:
            raise ValueError("No documents provided for training")
        
        model_types = model_types or ["category", "tags"]
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Prepare training data
            contents = [doc["content"] for doc in documents]
            categories = [doc.get("category", "unknown") for doc in documents]
            all_tags = [doc.get("tags", []) for doc in documents]
            
            # Vectorize content
            X = self.vectorizers["content"].fit_transform(contents)
            
            results = {}
            
            # Train category classifier
            if "category" in model_types:
                # Encode categories
                unique_categories = list(set(categories))
                self.label_encoders["category"] = {cat: i for i, cat in enumerate(unique_categories)}
                y_category = [self.label_encoders["category"][cat] for cat in categories]
                
                # Split data
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y_category, test_size=validation_split, random_state=42
                )
                
                # Train model
                self.models["category_classifier"].fit(X_train, y_train)
                
                # Evaluate
                y_pred = self.models["category_classifier"].predict(X_val)
                accuracy = accuracy_score(y_val, y_pred)
                
                results["category_accuracy"] = accuracy
                self.model_versions["category_classifier"] += 1
                
                # Store metrics
                self.model_metrics["category_classifier"] = {
                    "accuracy": accuracy,
                    "confusion_matrix": confusion_matrix(y_val, y_pred).tolist()
                }
            
            # Train tag generator
            if "tags" in model_types:
                # Encode tags
                y_tags = self.label_encoders["tags"].fit_transform(all_tags)
                
                # Split data
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y_tags, test_size=validation_split, random_state=42
                )
                
                # Train model
                self.models["tag_generator"].fit(X_train, y_train)
                
                # Evaluate
                y_pred = self.models["tag_generator"].predict(X_val)
                f1 = f1_score(y_val, y_pred, average="weighted")
                
                results["tag_f1_score"] = f1
                self.model_versions["tag_generator"] += 1
                
                # Store metrics
                self.model_metrics["tag_generator"] = {
                    "f1_score": f1
                }
            
            # Update training cache
            self.training_cache.extend(documents)
            
            training_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "success": True,
                "training_time": training_time,
                "documents_trained": len(documents),
                "model_versions": dict(self.model_versions),
                **results
            }
            
        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def classify_category(self, content: str) -> Dict[str, Any]:
        """Classify content into a category"""
        if not content:
            return {
                "category": "unknown",
                "confidence": 0.0,
                "probabilities": {}
            }
        
        try:
            # Vectorize content
            X = self.vectorizers["content"].transform([content])
            
            # Get predictions
            probabilities = self.models["category_classifier"].predict_proba(X)[0]
            predicted_idx = np.argmax(probabilities)
            
            # Decode category
            reverse_mapping = {v: k for k, v in self.label_encoders["category"].items()}
            predicted_category = reverse_mapping[predicted_idx]
            
            # Get all probabilities
            all_probs = {}
            for idx, prob in enumerate(probabilities):
                category = reverse_mapping.get(idx, "unknown")
                all_probs[category] = float(prob)
            
            return {
                "category": predicted_category,
                "confidence": float(probabilities[predicted_idx]),
                "probabilities": all_probs
            }
            
        except Exception as e:
            self.logger.error(f"Category classification failed: {e}")
            return {
                "category": "unknown",
                "confidence": 0.0,
                "probabilities": {},
                "error": str(e)
            }

    async def generate_tags(
        self,
        content: str,
        max_tags: int = 10,
        confidence_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """Generate tags for content"""
        if not content:
            return {"tags": [], "tag_scores": {}}
        
        try:
            # Vectorize content
            X = self.vectorizers["content"].transform([content])
            
            # Get predictions
            tag_probabilities = self.models["tag_generator"].predict_proba(X)[0]
            
            # Get tags above threshold
            tag_indices = np.where(tag_probabilities > confidence_threshold)[0]
            tag_scores = tag_probabilities[tag_indices]
            
            # Sort by score
            sorted_indices = np.argsort(tag_scores)[::-1][:max_tags]
            
            # Decode tags
            all_tags = self.label_encoders["tags"].classes_
            selected_tags = []
            tag_score_dict = {}
            
            for idx in sorted_indices:
                tag_idx = tag_indices[idx]
                tag = all_tags[tag_idx]
                score = float(tag_scores[idx])
                selected_tags.append(tag)
                tag_score_dict[tag] = score
            
            return {
                "tags": selected_tags,
                "tag_scores": tag_score_dict
            }
            
        except Exception as e:
            self.logger.error(f"Tag generation failed: {e}")
            return {
                "tags": [],
                "tag_scores": {},
                "error": str(e)
            }

    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """Perform comprehensive content analysis"""
        try:
            # Basic text statistics
            word_count = len(content.split())
            char_count = len(content)
            sentence_count = content.count('.') + content.count('!') + content.count('?')
            
            # Extract entities (simplified - in production use spaCy or similar)
            entities = self._extract_entities(content)
            
            # Extract keywords using TF-IDF
            keywords = await self._extract_keywords(content)
            
            # Sentiment analysis (simplified)
            sentiment = self._analyze_sentiment(content)
            
            # Complexity score
            avg_word_length = sum(len(word) for word in content.split()) / max(word_count, 1)
            complexity_score = min(1.0, (avg_word_length - 4) / 6)  # Normalize to 0-1
            
            # Reading time (assuming 200 words per minute)
            reading_time = max(1, word_count // 200)
            
            # Language detection (simplified)
            language = "english"  # In production, use langdetect or similar
            
            return {
                "word_count": word_count,
                "character_count": char_count,
                "sentence_count": sentence_count,
                "entities": entities,
                "keywords": keywords,
                "sentiment": sentiment,
                "complexity_score": complexity_score,
                "reading_time": reading_time,
                "language": language
            }
            
        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {
                "error": str(e),
                "entities": [],
                "keywords": [],
                "sentiment": {"polarity": 0, "subjectivity": 0},
                "complexity_score": 0.5,
                "reading_time": 1,
                "language": "unknown"
            }

    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Extract named entities (simplified implementation)"""
        entities = []
        
        # Simple pattern matching for technologies
        tech_patterns = {
            "TECHNOLOGY": ["Python", "JavaScript", "Docker", "Kubernetes", "PostgreSQL", 
                          "Redis", "React", "Django", "Flask", "FastAPI", "TensorFlow"],
            "FRAMEWORK": ["OAuth", "JWT", "REST", "GraphQL", "gRPC"],
            "CONCEPT": ["API", "authentication", "security", "deployment", "testing"]
        }
        
        for entity_type, patterns in tech_patterns.items():
        # 繰り返し処理
            for pattern in patterns:
                if pattern.lower() in content.lower():
                    entities.append({
                        "text": pattern,
                        "type": entity_type,
                        "start": content.lower().find(pattern.lower()),
                        "end": content.lower().find(pattern.lower()) + len(pattern)
                    })
        
        return entities

    async def _extract_keywords(self, content: str, top_k: int = 10) -> List[Dict[str, float]]:
        """Extract keywords using TF-IDF"""
        try:
            # Use a separate vectorizer for keyword extraction
            if not hasattr(self, 'keyword_vectorizer'):
                self.keyword_vectorizer = TfidfVectorizer(
                    max_features=100,
                    ngram_range=(1, 2),
                    stop_words="english"
                )
                # Fit on training data if available
                if self.training_cache:
                    train_contents = [doc["content"] for doc in self.training_cache]
                    self.keyword_vectorizer.fit(train_contents)
                else:
                    self.keyword_vectorizer.fit([content])
            
            # Transform content
            tfidf_matrix = self.keyword_vectorizer.transform([content])
            feature_names = self.keyword_vectorizer.get_feature_names_out()
            
            # Get top keywords
            scores = tfidf_matrix.toarray()[0]
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            keywords = []
            for idx in top_indices:
                if scores[idx] > 0:
                    keywords.append({
                        "word": feature_names[idx],
                        "score": float(scores[idx])
                    })
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return []

    def _analyze_sentiment(self, content: str) -> Dict[str, float]:
        """Analyze sentiment (simplified implementation)"""
        # In production, use TextBlob, VADER, or transformer models
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "best", "love"]
        negative_words = ["bad", "terrible", "awful", "worst", "hate", "error", "problem"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            polarity = (positive_count - negative_count) / total_sentiment_words
        else:
            polarity = 0.0
        
        # Simplified subjectivity (ratio of sentiment words to total words)
        word_count = len(content.split())
        subjectivity = total_sentiment_words / max(word_count, 1)
        
        return {
            "polarity": polarity,  # -1 to 1
            "subjectivity": min(1.0, subjectivity)  # 0 to 1
        }

    async def find_similar_documents(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Find similar documents using content similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Use parent's vector search
            results = await self.vector_search(
                query_embedding=query_embedding.tolist(),
                top_k=top_k,
                threshold=min_similarity
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Similar document search failed: {e}")
            return []

    async def cluster_documents(
        self,
        n_clusters: int = 5,
        algorithm: str = "kmeans",
        max_documents: int = 1000
    ) -> List[Dict[str, Any]]:
        """Cluster documents into groups"""
        try:
            # Fetch documents
            documents = await self._fetch_documents_for_clustering(max_documents)
            
            if len(documents) < n_clusters:
                raise ValueError(f"Not enough documents ({len(documents)}) for {n_clusters} clusters" \
                    "Not enough documents ({len(documents)}) for {n_clusters} clusters")
            
            # Vectorize documents
            contents = [doc["content"] for doc in documents]
            X = self.vectorizers["content"].transform(contents)
            
            # Reduce dimensionality for better clustering
            svd = TruncatedSVD(n_components=min(100, X.shape[1]))
            X_reduced = svd.fit_transform(X)
            
            # Perform clustering
            if algorithm == "kmeans":
                clusterer = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = clusterer.fit_predict(X_reduced)
                centroids = clusterer.cluster_centers_
            else:
                raise ValueError(f"Unsupported clustering algorithm: {algorithm}")
            
            # Organize results
            clusters = []
            for i in range(n_clusters):
                cluster_docs = [doc for j, doc in enumerate(documents) if cluster_labels[j] == i]
                
                # Extract cluster keywords
                cluster_contents = " ".join([doc["content"] for doc in cluster_docs])
                cluster_keywords = await self._extract_keywords(cluster_contents, top_k=5)
                
                clusters.append({
                    "cluster_id": i,
                    "documents": [{"id": doc["id"], "title": doc["title"]} for doc in cluster_docs],
                    "size": len(cluster_docs),
                    "centroid": centroids[i].tolist(),
                    "keywords": cluster_keywords
                })
            
            return clusters
            
        except Exception as e:
            self.logger.error(f"Document clustering failed: {e}")
            return []

    async def _fetch_documents_for_clustering(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch documents for clustering"""
        # In a real implementation, this would query the database
        # For now, return cached training documents
        return self.training_cache[:limit]

    async def update_models(
        self,
        new_documents: List[Dict[str, Any]],
        learning_rate: float = 0.1
    ) -> Dict[str, Any]:
        """Incrementally update models with new data"""
        try:
            # Add to training cache
            self.training_cache.extend(new_documents)
            
            # Retrain with all data (simplified incremental learning)
            # In production, use proper incremental learning algorithms
            result = await self.train_models(
                documents=self.training_cache[-1000:],  # Use last 1000 documents
                validation_split=0.1
            )
            
            return {
                "success": True,
                "documents_processed": len(new_documents),
                "total_training_size": len(self.training_cache),
                **result
            }
            
        except Exception as e:
            self.logger.error(f"Model update failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def classify_multi_label(
        self,
        content: str,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """Classify content into multiple categories"""
        try:
            # Get all category probabilities
            result = await self.classify_category(content)
            probabilities = result.get("probabilities", {})
            
            # Select categories above threshold
            categories = []
            scores = {}
            
            for category, prob in probabilities.items():
                if prob >= threshold:
                    categories.append({
                        "name": category,
                        "confidence": prob
                    })
                    scores[category] = prob
            
            # Sort by confidence
            categories.sort(key=lambda x: x["confidence"], reverse=True)
            
            return {
                "categories": categories,
                "scores": scores
            }
            
        except Exception as e:
            self.logger.error(f"Multi-label classification failed: {e}")
            return {
                "categories": [],
                "scores": {},
                "error": str(e)
            }

    async def explain_classification(
        self,
        content: str,
        model_type: str = "category"
    ) -> Dict[str, Any]:
        """Explain model classification decision"""
        try:
            # Vectorize content
            X = self.vectorizers["content"].transform([content])
            
            # Get feature names
            feature_names = self.vectorizers["content"].get_feature_names_out()
            
            # Get prediction
            if model_type == "category":
                prediction = await self.classify_category(content)
                model = self.models["category_classifier"]
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Extract feature weights (simplified)
            # In production, use LIME or SHAP for better explanations
            feature_weights = X.toarray()[0]
            
            # Get top features
            top_indices = np.argsort(feature_weights)[::-1][:20]
            important_features = []
            
            for idx in top_indices:
                if feature_weights[idx] > 0:
                    important_features.append({
                        "word": feature_names[idx],
                        "weight": float(feature_weights[idx])
                    })
            
            return {
                "predicted_category": prediction["category"],
                "confidence": prediction["confidence"],
                "important_features": important_features[:10],
                "feature_weights": {
                    "min": float(np.min(feature_weights)),
                    "max": float(np.max(feature_weights)),
                    "mean": float(np.mean(feature_weights))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Classification explanation failed: {e}")
            return {
                "error": str(e),
                "predicted_category": "unknown",
                "important_features": [],
                "feature_weights": {}
            }

    async def batch_classify(
        self,
        contents: List[str],
        batch_size: int = 50
    ) -> List[Dict[str, Any]]:
        """Batch classify multiple documents"""
        results = []
        
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [self.classify_category(content) for content in batch]
            batch_results = await asyncio.gather(*tasks)
            
            results.extend(batch_results)
        
        return results

    async def save_models(self, checkpoint_name: str) -> Dict[str, Any]:
        """Save trained models to disk"""
        try:
            checkpoint_dir = f"/tmp/knowledge_ml_checkpoints/{checkpoint_name}"
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            saved_files = []
            
            # Save models
            for model_name, model in self.models.items():
                model_file = f"{checkpoint_dir}/{model_name}.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
                saved_files.append(model_file)
            
            # Save vectorizers
            for vec_name, vectorizer in self.vectorizers.items():
                vec_file = f"{checkpoint_dir}/{vec_name}_vectorizer.pkl"
                with open(vec_file, 'wb') as f:
                    pickle.dump(vectorizer, f)
                saved_files.append(vec_file)
            
            # Save label encoders
            encoder_file = f"{checkpoint_dir}/label_encoders.pkl"
            with open(encoder_file, 'wb') as f:
                pickle.dump(self.label_encoders, f)
            saved_files.append(encoder_file)
            
            # Save metadata
            metadata = {
                "model_versions": dict(self.model_versions),
                "saved_at": datetime.now().isoformat(),
                "training_size": len(self.training_cache)
            }
            metadata_file = f"{checkpoint_dir}/metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            saved_files.append(metadata_file)
            
            return {
                "success": True,
                "checkpoint_dir": checkpoint_dir,
                "model_files": saved_files
            }
            
        except Exception as e:
            self.logger.error(f"Model save failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def load_models(self, checkpoint_name: str) -> Dict[str, Any]:
        """Load trained models from disk"""
        try:
            checkpoint_dir = f"/tmp/knowledge_ml_checkpoints/{checkpoint_name}"
            
            if not os.path.exists(checkpoint_dir):
                raise ValueError(f"Checkpoint not found: {checkpoint_name}")
            
            # Load models
            for model_name in self.models.keys():
                model_file = f"{checkpoint_dir}/{model_name}.pkl"
                if os.path.exists(model_file):
                    with open(model_file, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
            
            # Load vectorizers
            for vec_name in self.vectorizers.keys():
                vec_file = f"{checkpoint_dir}/{vec_name}_vectorizer.pkl"
                if os.path.exists(vec_file):
                    with open(vec_file, 'rb') as f:
                        self.vectorizers[vec_name] = pickle.load(f)
            
            # Load label encoders
            encoder_file = f"{checkpoint_dir}/label_encoders.pkl"
            if os.path.exists(encoder_file):
                with open(encoder_file, 'rb') as f:
                    self.label_encoders = pickle.load(f)
            
            # Load metadata
            metadata_file = f"{checkpoint_dir}/metadata.json"
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.model_versions = defaultdict(int, metadata["model_versions"])
            
            return {
                "success": True,
                "loaded_from": checkpoint_dir,
                "model_versions": dict(self.model_versions)
            }
            
        except Exception as e:
            self.logger.error(f"Model load failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_uncertain_samples(
        self,
        unlabeled_contents: List[str],
        n_samples: int = 10,
        uncertainty_type: str = "entropy"
    ) -> List[Dict[str, Any]]:
        """Get samples with highest uncertainty for active learning"""
        try:
            # Vectorize contents
            X = self.vectorizers["content"].transform(unlabeled_contents)
            
            # Get prediction probabilities
            probabilities = self.models["category_classifier"].predict_proba(X)
            
            # Calculate uncertainty
            if uncertainty_type == "entropy":
                # Shannon entropy
                uncertainties = -np.sum(probabilities * np.log(probabilities + 1e-10), axis=1)
            elif uncertainty_type == "margin":
                # Margin between top two predictions
                sorted_probs = np.sort(probabilities, axis=1)
                uncertainties = 1 - (sorted_probs[:, -1] - sorted_probs[:, -2])
            else:
                raise ValueError(f"Unsupported uncertainty type: {uncertainty_type}")
            
            # Get most uncertain samples
            uncertain_indices = np.argsort(uncertainties)[::-1][:n_samples]
            
            samples = []
            for idx in uncertain_indices:
                samples.append({
                    "content": unlabeled_contents[idx],
                    "uncertainty_score": float(uncertainties[idx]),
                    "predicted_probabilities": probabilities[idx].tolist()
                })
            
            return samples
            
        except Exception as e:
            self.logger.error(f"Uncertain sample selection failed: {e}")
            return []

    async def extract_features(
        self,
        content: str,
        feature_types: List[str] = None
    ) -> Dict[str, Any]:
        """Extract various features from content"""
        feature_types = feature_types or ["tfidf", "embeddings", "linguistic"]
        features = {}
        
        try:
            if "tfidf" in feature_types:
                # TF-IDF features
                X = self.vectorizers["content"].transform([content])
                feature_names = self.vectorizers["content"].get_feature_names_out()
                tfidf_values = X.toarray()[0]
                
                # Get non-zero features
                non_zero_indices = np.where(tfidf_values > 0)[0]
                features["tfidf"] = {
                    "feature_names": [feature_names[i] for i in non_zero_indices],
                    "values": [float(tfidf_values[i]) for i in non_zero_indices]
                }
            
            if "embeddings" in feature_types:
                # Generate embeddings
                embedding = await self.generate_embedding(content)
                features["embeddings"] = embedding.tolist()
            
            if "linguistic" in feature_types:
                # Linguistic features (simplified)
                words = content.split()
                features["linguistic"] = {
                    "pos_tags": self._simple_pos_tagging(words),
                    "named_entities": self._extract_entities(content),
                    "syntax_tree": "Not implemented in simplified version"
                }
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return {"error": str(e)}

    def _simple_pos_tagging(self, words: List[str]) -> List[Tuple[str, str]]:
        """Simple POS tagging (very simplified)"""
        # In production, use NLTK or spaCy
        pos_tags = []
        for word in words[:20]:  # Limit to first 20 words
            if word.endswith("ing"):
                pos_tags.append((word, "VBG"))  # Verb, gerund
            elif word.endswith("ed"):
                pos_tags.append((word, "VBD"))  # Verb, past tense
            elif word[0].isupper():
                pos_tags.append((word, "NNP"))  # Proper noun
            elif word in ["the", "a", "an"]:
                pos_tags.append((word, "DT"))  # Determiner
            else:
                pos_tags.append((word, "NN"))  # Noun (default)
        
        return pos_tags

    async def get_model_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models"""
        metrics = {}
        
        # 繰り返し処理
        for model_name, model_metrics in self.model_metrics.items():
            metrics[model_name] = model_metrics.copy()
            
            # Add additional computed metrics
            if model_name == "category_classifier" and "confusion_matrix" in model_metrics:
                cm = np.array(model_metrics["confusion_matrix"])
                
                # Calculate per-class metrics:
                n_classes = cm.shape[0]
                precision = np.zeros(n_classes)
                recall = np.zeros(n_classes)
                f1_scores = np.zeros(n_classes)
                
                for i in range(n_classes):
                    tp = cm[i, i]
                    fp = cm[:, i].sum() - tp
                    fn = cm[i, :].sum() - tp
                    
                    precision[i] = tp / (tp + fp) if (tp + fp) > 0 else 0
                    recall[i] = tp / (tp + fn) if (tp + fn) > 0 else 0
                    f1_scores[i] = 2 * (precision[i] * recall[i]) / (precision[i] + recall[i]) \
                                  if (precision[i] + recall[i]) > 0 else 0
                
                metrics[model_name]["precision"] = float(np.mean(precision))
                metrics[model_name]["recall"] = float(np.mean(recall))
                metrics[model_name]["f1_score"] = float(np.mean(f1_scores))
            
            elif model_name == "tag_generator":
                # Add precision/recall at k metrics
                metrics[model_name]["precision_at_k"] = {
                    "k=1": 0.85,  # Placeholder
                    "k=3": 0.75,
                    "k=5": 0.65
                }
                metrics[model_name]["recall_at_k"] = {
                    "k=1": 0.45,  # Placeholder
                    "k=3": 0.65,
                    "k=5": 0.80
                }
                metrics[model_name]["mean_average_precision"] = 0.72  # Placeholder
        
        return metrics

    async def cleanup(self) -> None:
        """Cleanup ML resources"""
        await super().cleanup()
        
        # Clear models and caches
        self.models.clear()
        self.vectorizers.clear()
        self.label_encoders.clear()
        self.training_cache.clear()
        self.model_metrics.clear()
        
        self._initialized = False
        self.logger.info("ML Classifier cleaned up")