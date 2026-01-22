"""Vector search engine for finding relevant skills."""

import logging
import threading
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from .skill_loader import Skill

logger = logging.getLogger(__name__)


class SkillSearchEngine:
    """Search engine for finding relevant skills using vector similarity.

    Attributes
    ----------
    model : SentenceTransformer | None
        Embedding model for generating vectors (lazy-loaded).
    model_name : str
        Name of the sentence-transformers model to use.
    skills : list[Skill]
        List of indexed skills.
    embeddings : np.ndarray | None
        Embeddings matrix for all skill descriptions.
    _lock : threading.Lock
        Lock for thread-safe access to skills and embeddings.
    """

    def __init__(self, model_name: str):
        """Initialize the search engine.

        Parameters
        ----------
        model_name : str
            Name of the sentence-transformers model to use.
        """
        logger.info(
            f"Search engine initialized (model: {model_name}, lazy-loading enabled)"
        )
        self.model: SentenceTransformer | None = None
        self.model_name = model_name
        self.skills: list[Skill] = []
        self.embeddings: np.ndarray | None = None
        self._lock = threading.Lock()

    def _ensure_model_loaded(self) -> SentenceTransformer:
        """Ensure the embedding model is loaded (lazy initialization).

        Returns
        -------
        SentenceTransformer
            The loaded embedding model.
        """
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded: {self.model_name}")
        return self.model

    def index_skills(self, skills: list[Skill]) -> None:
        """Index a list of skills by generating their embeddings.

        Parameters
        ----------
        skills : list[Skill]
            Skills to index.
        """
        with self._lock:
            if not skills:
                logger.warning("No skills to index")
                self.skills = []
                self.embeddings = None
                return

            logger.info(f"Indexing {len(skills)} skills...")
            self.skills = skills

            # Generate embeddings from skill descriptions
            descriptions = [skill.description for skill in skills]
            model = self._ensure_model_loaded()
            self.embeddings = model.encode(descriptions, convert_to_numpy=True)

            logger.info(f"Successfully indexed {len(skills)} skills")

    def add_skills(self, skills: list[Skill]) -> None:
        """Add skills incrementally and update embeddings.

        Parameters
        ----------
        skills : list[Skill]
            Skills to add to the index.
        """
        if not skills:
            return

        with self._lock:
            logger.info(f"Adding {len(skills)} skills to index...")

            # Generate embeddings for new skills
            descriptions = [skill.description for skill in skills]
            model = self._ensure_model_loaded()
            new_embeddings = model.encode(descriptions, convert_to_numpy=True)

            # Append to existing skills and embeddings
            self.skills.extend(skills)

            if self.embeddings is None:
                # First batch of skills
                self.embeddings = new_embeddings
            else:
                # Append to existing embeddings
                self.embeddings = np.vstack([self.embeddings, new_embeddings])

            logger.info(
                f"Successfully added {len(skills)} skills. Total: {len(self.skills)} skills"
            )

    def search(
        self,
        query: str,
        top_k: int = 3,
        tenant_id: str | None = None,
        allowed_skill_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for the most relevant skills based on a query.

        This method implements scope-based filtering:
        - Global skills (scope="global"): Always included in results
        - Tenant skills (scope="tenant"): Only included if ALL conditions are met:
            * skill.tenant_id == tenant_id (must match the provided tenant)
            * skill.name in allowed_skill_names (MUST be explicitly listed)
        
        Important: Tenant skills (uploaded skills) are NEVER accessible unless
        they are explicitly listed in allowed_skill_names. If allowed_skill_names
        is None or empty, NO tenant skills will be returned (only global skills).

        The skill engine does NOT perform authorization checks. It trusts
        the provided tenant_id and allowed_skill_names from the API server.

        Parameters
        ----------
        query : str
            The task description or query to search for.
        top_k : int, optional
            Number of top results to return, by default 3.
        tenant_id : str | None, optional
            Tenant ID for filtering tenant-scoped skills. Required for tenant skills.
        allowed_skill_names : list[str] | None, optional
            List of skill names the agent is allowed to access. If None or empty,
            NO tenant skills will be returned (only global skills). Tenant skills
            MUST be explicitly listed in this parameter to be accessible.

        Returns
        -------
        list[dict[str, Any]]
            List of skill dictionaries with relevance scores, sorted by relevance.
        """
        with self._lock:
            if not self.skills or self.embeddings is None:
                logger.warning("No skills indexed, returning empty results")
                return []

            # Normalize allowed_skill_names to a set for efficient lookup
            allowed_set = set(allowed_skill_names) if allowed_skill_names else set()
            
            # If allowed_skill_names is missing or empty, only global skills will be returned
            # Tenant skills require explicit permission via allowed_skill_names
            if not allowed_set:
                logger.debug(
                    f"allowed_skill_names is empty or None - only global skills will be returned "
                    f"(tenant_id={tenant_id})"
                )

            # Apply scope-based filtering to get candidate skills
            # This filtering happens BEFORE similarity search for efficiency
            candidate_indices = []
            for idx, skill in enumerate(self.skills):
                # Global skills (scope="global") are always included regardless of
                # tenant_id or allowed_skill_names
                if skill.scope == "global":
                    candidate_indices.append(idx)
                    continue
                
                # Tenant skills (scope="tenant") require matching tenant_id and explicit permission
                if skill.scope == "tenant":
                    # Must match tenant_id
                    if skill.tenant_id != tenant_id:
                        continue
                    
                    # Tenant skills MUST be explicitly listed in allowed_skill_names
                    # If allowed_set is empty (allowed_skill_names missing/empty),
                    # exclude ALL tenant skills - only global skills will be returned
                    if not allowed_set:
                        continue
                    
                    # Skill name must be explicitly in allowed_skill_names
                    if skill.name not in allowed_set:
                        continue
                    
                    # Both conditions met, include this tenant skill
                    candidate_indices.append(idx)
                    continue

            if not candidate_indices:
                logger.info(
                    f"No skills match filters (tenant_id={tenant_id}, "
                    f"allowed_skill_names={len(allowed_set) if allowed_set else 0} skills)"
                )
                return []

            # Ensure top_k doesn't exceed available candidate skills
            top_k = min(top_k, len(candidate_indices))

            logger.info(
                f"Searching for: '{query}' (top_k={top_k}, tenant_id={tenant_id}, "
                f"allowed_skills={len(allowed_set) if allowed_set else 0})"
            )

            # Generate embedding for the query
            model = self._ensure_model_loaded()
            query_embedding = model.encode([query], convert_to_numpy=True)[0]

            # Compute cosine similarity for all skills
            similarities = self._cosine_similarity(query_embedding, self.embeddings)

            # Get similarities for candidate skills only
            candidate_similarities = similarities[candidate_indices]

            # Get top-k indices from candidates
            top_candidate_indices = np.argsort(candidate_similarities)[::-1][:top_k]

            # Build results
            results = []
            for candidate_idx in top_candidate_indices:
                original_idx = candidate_indices[candidate_idx]
                skill = self.skills[original_idx]
                score = float(candidate_similarities[candidate_idx])

                result = skill.to_dict()
                result["relevance_score"] = score
                results.append(result)

                logger.debug(
                    f"Found skill: {skill.name} (scope={skill.scope}, score: {score:.4f})"
                )

            logger.info(f"Returning {len(results)} results")
            return results

    @staticmethod
    def _cosine_similarity(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between a vector and a matrix of vectors.

        Parameters
        ----------
        vec : np.ndarray
            Query vector.
        matrix : np.ndarray
            Matrix of vectors to compare against.

        Returns
        -------
        np.ndarray
            Similarity scores.
        """
        # Normalize vectors
        vec_norm = vec / np.linalg.norm(vec)
        matrix_norm = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

        # Compute dot product (cosine similarity for normalized vectors)
        similarities = np.dot(matrix_norm, vec_norm)

        return similarities

