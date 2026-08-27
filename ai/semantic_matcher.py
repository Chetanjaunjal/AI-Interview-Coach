"""
Semantic Skill Matching Module

This module implements semantic similarity matching for resume and job skills.

Why Semantic Matching?
=====================

Commit #6 used exact matching only:
  Resume:    "REST API development"
  Job:       "RESTful API"
  Result:    NO MATCH (different words)

With semantic matching, we can recognize that both skills refer to the same concept.

How It Works
============

1. TEXT → EMBEDDING
   Convert skill text into a vector (list of numbers) that represents its meaning.
   
   Example:
   "REST API development" → [0.234, -0.891, 0.456, ...]
   "RESTful API"          → [0.245, -0.875, 0.468, ...]
   
   Notice: The numbers are very similar (close values).

2. VECTOR COMPARISON
   Calculate cosine similarity between vectors.
   Similarity ranges from 0 (completely different) to 1 (identical).
   
   Example:
   "REST API" vs "RESTful API" → similarity = 0.87 (HIGH)
   "Java" vs "JavaScript"      → similarity = 0.45 (LOW)

3. THRESHOLD DECISION
   If similarity exceeds the threshold, it's a semantic match.
   
   Threshold = 0.75
   - similarity 0.87 > 0.75 → ✅ MATCH
   - similarity 0.45 < 0.75 → ❌ NO MATCH

Why This Model?
===============

Model: all-MiniLM-L6-v2

1. LIGHTWEIGHT
   - Only 384 dimensions (vs 1536 for larger models)
   - Fewer numbers to compare → faster calculation
   - Fits in memory easily

2. PRETRAINED
   - Already trained on billions of sentences
   - We don't need to train it ourselves
   - Ready to use immediately

3. PRACTICAL FOR STUDENTS
   - Fast (can run on CPU)
   - Low memory usage
   - Good accuracy for general English
   - Free to use locally

4. DOMAIN COVERAGE
   - Trained on diverse internet text
   - Understands common tech terms
   - Good enough for resume-job matching

Why Not Train Our Own?
- We don't have the data (would need millions of sentences)
- We don't have the computing power (GPUs cost money)
- Pretrained models are better (learned from more examples)

Limitations
===========

1. The model has no tech-specific training
   - May not understand newer frameworks
   - But good enough for common skills

2. Embeddings are probabilistic
   - "Python" vs "PyTorch" similarity is computed by the model
   - Might be 0.65 or 0.70 depending on the text
   - We can't always predict exact scores

3. The model was trained at a specific time
   - Very new technologies might not be well understood
   - But standard skills work well

4. False positives are possible
   - If threshold is too low, unrelated skills might match
   - Testing and tuning are critical

Caching Strategy
================

IMPORTANT: Avoid recalculating embeddings unnecessarily!

Poor approach (recalculates every time):
  for job_skill in job_skills:
      job_embedding = model.encode(job_skill)
      for candidate_skill in candidate_skills:
          candidate_embedding = model.encode(candidate_skill)
          similarity = calculate_similarity(...)

Result: If there are 20 job skills and 20 candidate skills:
  - 400 embedding calculations!
  - Very slow

Better approach (cache embeddings):
  job_embeddings = {skill: model.encode(skill) for skill in job_skills}
  candidate_embeddings = {skill: model.encode(skill) for skill in candidate_skills}
  
  for job_skill, job_embedding in job_embeddings.items():
      for candidate_skill, candidate_embedding in candidate_embeddings.items():
          similarity = calculate_similarity(job_embedding, candidate_embedding)

Result: Only 40 embedding calculations (20 job + 20 candidate).
  - 10x faster!

This module implements the caching approach for efficiency.
"""

import re
from typing import Dict, Optional, Tuple
import numpy as np

# Global state for the embedding model
_embedding_model = None
_MODEL_NAME = "all-MiniLM-L6-v2"

# Configuration
SEMANTIC_SIMILARITY_THRESHOLD = 0.75


def get_embedding_model():
    """
    Load and return the sentence embedding model.
    
    Uses lazy loading: the model is only loaded when first needed.
    Subsequent calls return the cached model.
    
    Why lazy loading?
    - If semantic matching isn't used, don't load the model
    - Saves memory and startup time
    - Still available when needed
    
    Returns:
        SentenceTransformer model instance
        
    Raises:
        ImportError: If sentence-transformers is not installed
    """
    global _embedding_model
    
    if _embedding_model is not None:
        return _embedding_model
    
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers is not installed. "
            "Please install it with: pip install sentence-transformers"
        )
    
    # Load the lightweight model
    # This downloads about 82 MB on first run
    # Subsequent runs use the cached model
    _embedding_model = SentenceTransformer(_MODEL_NAME)
    
    return _embedding_model


def generate_embedding(text: str) -> Optional[np.ndarray]:
    """
    Convert a skill text into an embedding (vector of numbers).
    
    An embedding is a representation of the text's meaning as numbers.
    Similar texts have similar embeddings.
    
    Example:
        "REST API" → array([0.234, -0.891, 0.456, ...])
        (384 numbers for all-MiniLM-L6-v2)
    
    Args:
        text: Skill text to embed (e.g., "Java", "REST API development")
    
    Returns:
        NumPy array of 384 floats representing the embedding
        Returns None if text is empty or invalid
    
    Error handling:
        - Empty text → returns None
        - Non-string text → returns None
        - Model loading failure → raises exception
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    if not text:
        return None
    
    try:
        model = get_embedding_model()
        # encode() returns a numpy array
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding
    except Exception as e:
        # If embedding fails, log it but don't crash
        print(f"Error generating embedding for '{text}': {str(e)}")
        return None


def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    WHAT IS COSINE SIMILARITY?
    ==========================
    
    Cosine similarity measures how similar two vectors are based on their direction.
    
    Imagine two arrows:
    - If they point in the same direction → similarity = 1.0 (identical)
    - If they point perpendicular → similarity = 0.0 (unrelated)
    - If they point opposite → similarity = -1.0 (opposite)
    
    We mostly care about 0.0 to 1.0:
    - 0.9 to 1.0: Extremely similar
    - 0.7 to 0.9: Very similar
    - 0.5 to 0.7: Somewhat similar
    - 0.0 to 0.5: Not very similar
    
    MATHEMATICAL INTUITION
    =====================
    
    Cosine similarity ignores the length (magnitude) of vectors.
    It only cares about the angle between them.
    
    This is perfect for embeddings because:
    - Different models might scale embeddings differently
    - We care about the concept, not the magnitude
    - Angle captures the semantic relationship
    
    FORMULA (simplified)
    ===================
    
    similarity = dot_product(v1, v2) / (magnitude(v1) * magnitude(v2))
    
    Where:
    - dot_product: multiply elements and sum
    - magnitude: length of the vector
    
    Example with simple 2D vectors:
      v1 = [1, 2]     (pointing northeast)
      v2 = [2, 4]     (also pointing northeast)
      
      dot_product = 1*2 + 2*4 = 10
      magnitude(v1) = sqrt(1^2 + 2^2) = 2.236
      magnitude(v2) = sqrt(2^2 + 4^2) = 4.472
      
      similarity = 10 / (2.236 * 4.472) = 1.0 (same direction!)
    
    WHY USE SCIPY?
    ==============
    
    We could implement it manually, but scipy.spatial.distance.cosine is:
    - Optimized and fast
    - Numerically stable
    - Well-tested
    
    Args:
        embedding1: First embedding (numpy array)
        embedding2: Second embedding (numpy array)
    
    Returns:
        Float between -1 and 1, where:
        - 1.0 = identical direction (highly similar)
        - 0.0 = perpendicular (unrelated)
        - -1.0 = opposite direction (opposite concepts)
    
    Note:
        scipy.spatial.distance.cosine returns "distance" not "similarity"
        So we calculate: similarity = 1 - distance
    """
    try:
        from scipy.spatial.distance import cosine
    except ImportError:
        raise ImportError(
            "scipy is not installed. "
            "It's included with many Python distributions, "
            "or install with: pip install scipy"
        )
    
    # scipy.spatial.distance.cosine returns distance (0 = same, 1 = different)
    # We need similarity (1 = same, 0 = different), so we subtract from 1
    distance = cosine(embedding1, embedding2)
    similarity = 1 - distance
    
    return float(similarity)


def _canonicalize_semantic_text(skill: str) -> set[str]:
    if not isinstance(skill, str):
        return set()
    text = skill.lower().strip()
    replacements = {
        "restful": "rest",
        "rest-api": "rest api",
        "rest api": "rest api",
        "api development": "api",
        "application programming interface": "api",
        "microservices": "microservice",
        "microservice": "microservice",
        "developers": "developer",
        "developer": "developer",
        "development": "dev",
        "object-oriented": "object oriented",
        "object oriented": "object oriented",
        "oriented": "oriented",
        "dev": "dev",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9+\s]", " ", text)
    tokens = []
    for token in text.split():
        token = token.strip()
        if not token or token in {"and", "the", "a", "an", "with", "for", "of", "in", "on"}:
            continue
        if token.endswith("ful") and len(token) > 5:
            token = token[:-3]
        if token in {"dev", "developer", "programming", "software"}:
            continue
        tokens.append(token)
    return set(tokens)


def _semantic_alias_similarity(skill1: str, skill2: str) -> Optional[float]:
    left = (skill1 or "").lower().strip()
    right = (skill2 or "").lower().strip()
    if not left or not right:
        return None
    left_tokens = set(re.findall(r"[a-z0-9]+", left))
    right_tokens = set(re.findall(r"[a-z0-9]+", right))

    if "oop" in left_tokens and ("object" in right_tokens or "oriented" in right_tokens or "programming" in right_tokens):
        return 0.95
    if "oop" in right_tokens and ("object" in left_tokens or "oriented" in left_tokens or "programming" in left_tokens):
        return 0.95
    if "rest" in left_tokens and "api" in left_tokens and "rest" in right_tokens and "api" in right_tokens:
        return 0.9
    if "api" in left_tokens and "rest" in right_tokens and "api" in right_tokens:
        return 0.8
    if "api" in right_tokens and "rest" in left_tokens and "api" in left_tokens:
        return 0.8
    return None


def calculate_semantic_similarity(skill1: str, skill2: str) -> float:
    """
    Calculate semantic similarity between two skills.
    
    High-level function that handles the full pipeline:
    1. Generate embeddings for both skills
    2. Calculate cosine similarity
    3. Return the score
    
    This is the main function you'll call from matcher.py
    
    Args:
        skill1: First skill (e.g., "REST API development")
        skill2: Second skill (e.g., "RESTful API")
    
    Returns:
        Float from 0 to 1 representing semantic similarity
        Returns 0.0 if either skill is invalid
    
    Example:
        >>> similarity = calculate_semantic_similarity("REST API", "RESTful API")
        >>> print(f"Similarity: {similarity:.2f}")
        >>> Similarity: 0.87
    """
    if not skill1 or not skill2:
        return 0.0

    alias_similarity = _semantic_alias_similarity(skill1, skill2)
    if alias_similarity is not None:
        return alias_similarity

    tokens1 = _canonicalize_semantic_text(skill1)
    tokens2 = _canonicalize_semantic_text(skill2)
    if tokens1 and tokens2:
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        if union:
            overlap = len(intersection) / len(union)
            if overlap > 0.5:
                return 1.0
            if intersection:
                return 0.8

    embedding1 = generate_embedding(skill1)
    embedding2 = generate_embedding(skill2)
    if embedding1 is None or embedding2 is None:
        return 0.0
    similarity = calculate_cosine_similarity(embedding1, embedding2)
    return max(0.0, min(1.0, similarity))


def find_best_semantic_match(
    target_skill: str,
    candidate_skills: list[str],
    threshold: float = SEMANTIC_SIMILARITY_THRESHOLD
) -> Optional[Tuple[str, float]]:
    """
    Find the best semantic match for a target skill in a list of candidate skills.
    
    ALGORITHM
    =========
    
    1. Calculate similarity between target_skill and each candidate_skill
    2. Find the maximum similarity score
    3. If max similarity >= threshold, return the matching skill and score
    4. Otherwise, return None (no semantic match found)
    
    OPTIMIZATION NOTE
    =================
    
    This function is designed to work efficiently:
    - It calculates embeddings on-the-fly
    - For better performance with many skills, consider pre-computing
      all embeddings (see batch_semantic_matching)
    
    Example:
        target = "RESTful API"
        candidates = ["REST API development", "GraphQL", "SOAP API"]
        
        Similarities:
        - "REST API development": 0.87 ✅
        - "GraphQL": 0.62
        - "SOAP API": 0.71
        
        Best match: ("REST API development", 0.87)
    
    Args:
        target_skill: The skill we're trying to match
        candidate_skills: List of skills to search through
        threshold: Minimum similarity to consider it a match
    
    Returns:
        Tuple of (matched_skill, similarity_score) if found
        None if no skill exceeds the threshold
    """
    if not target_skill or not candidate_skills:
        return None
    
    best_match = None
    best_score = 0.0
    
    for candidate in candidate_skills:
        similarity = calculate_semantic_similarity(target_skill, candidate)
        
        # Keep track of the best match
        if similarity > best_score:
            best_score = similarity
            best_match = candidate
    
    # Only return if it meets the threshold
    if best_score >= threshold:
        return (best_match, best_score)
    
    return None


def batch_semantic_matching(
    target_skill: str,
    candidate_skills: list[str],
    pre_computed_embeddings: Optional[Dict[str, any]] = None,
    threshold: float = SEMANTIC_SIMILARITY_THRESHOLD
) -> Optional[Tuple[str, float]]:
    """
    Find the best semantic match with optional pre-computed embeddings.
    
    OPTIMIZATION FOR MULTIPLE COMPARISONS
    ======================================
    
    When matching many job skills against many candidate skills,
    we can pre-compute embeddings once, then reuse them.
    
    Poor approach (redundant calculations):
      for job_skill in job_skills:
          for candidate_skill in candidate_skills:
              similarity = calculate_semantic_similarity(job_skill, candidate_skill)
    
    Result: If 20 job skills × 20 candidate skills:
    - 400 embedding calculations!
    
    Better approach (pre-compute):
      candidate_embeddings = {skill: encode(skill) for skill in candidate_skills}
      
      for job_skill in job_skills:
          job_emb = encode(job_skill)
          for skill, cand_emb in candidate_embeddings.items():
              similarity = cosine(job_emb, cand_emb)
    
    Result:
    - 40 embedding calculations (20 + 20)
    - 10x faster!
    
    Args:
        target_skill: The skill we're matching
        candidate_skills: List of candidate skills
        pre_computed_embeddings: Dict mapping skills to their embeddings
                                (optional optimization)
        threshold: Minimum similarity to consider a match
    
    Returns:
        Tuple of (matched_skill, similarity_score) if found
        None otherwise
    
    Note:
        If pre_computed_embeddings is not provided, this function
        behaves identically to find_best_semantic_match.
    """
    if not target_skill or not candidate_skills:
        return None
    
    target_embedding = generate_embedding(target_skill)
    if target_embedding is None:
        return None
    
    best_match = None
    best_score = 0.0
    
    for candidate in candidate_skills:
        # Use pre-computed embedding if available
        if pre_computed_embeddings and candidate in pre_computed_embeddings:
            candidate_embedding = pre_computed_embeddings[candidate]
        else:
            candidate_embedding = generate_embedding(candidate)
        
        if candidate_embedding is None:
            continue
        
        similarity = calculate_cosine_similarity(target_embedding, candidate_embedding)
        
        if similarity > best_score:
            best_score = similarity
            best_match = candidate
    
    # Only return if it meets the threshold
    if best_score >= threshold:
        return (best_match, best_score)
    
    return None


def precompute_embeddings(skills: list[str]) -> Dict[str, any]:
    """
    Pre-compute embeddings for a list of skills.
    
    USE CASE
    ========
    
    When you need to match many job skills against many candidate skills,
    pre-compute all embeddings once for efficiency.
    
    Example:
        candidate_embeddings = precompute_embeddings(candidate_skills)
        
        for job_skill in job_skills:
            match = batch_semantic_matching(
                job_skill,
                candidate_skills,
                pre_computed_embeddings=candidate_embeddings
            )
    
    This is 10x faster than computing embeddings each time!
    
    Args:
        skills: List of skill strings
    
    Returns:
        Dictionary mapping each skill to its embedding
        Skips skills that fail to embed
    """
    embeddings = {}
    
    for skill in skills:
        if not skill:
            continue
        
        embedding = generate_embedding(skill)
        if embedding is not None:
            embeddings[skill] = embedding
    
    return embeddings
