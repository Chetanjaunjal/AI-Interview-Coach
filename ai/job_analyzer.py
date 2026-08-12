"""
Job Description Analyzer Module

This module analyzes job descriptions and extracts structured information.

Similar to resume_analyzer.py, this keeps AI communication separated from Flask.
"""

import json
import os
from typing import Optional, Dict, Any

from openai import OpenAI, APIError, APIConnectionError, RateLimitError


class JobAnalyzer:
    """
    Analyzes job descriptions using OpenAI's LLM API.
    
    Extracts structured information about:
    - Job title and company
    - Required and preferred skills
    - Technical requirements
    - Responsibilities and qualifications
    - Experience and education
    """

    def __init__(self):
        """
        Initialize the analyzer with API key from environment variables.
        
        Raises:
            ValueError: If OPENAI_API_KEY is not set
        """
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it before running the application."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
        
        # Maximum length for job description (prevents excessive token usage)
        # ~50KB of text = ~12,500 tokens (reasonable limit)
        self.max_description_length = 50000

    def analyze_job_description(
        self,
        job_title: str,
        job_description: str,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a job description and extract structured information.
        
        Args:
            job_title: The title of the job position
            job_description: The full job description text
            company: Company name (optional)
            
        Returns:
            Dictionary with extracted job information, or error details
            
        Raises:
            ValueError: If inputs are invalid
            APIError: If OpenAI API fails (handled gracefully)
        """
        # Validate inputs
        validation_error = self._validate_inputs(job_title, job_description)
        if validation_error:
            return {
                "success": False,
                "error": validation_error
            }

        # Estimate tokens to check if description is too large
        token_estimate = len(job_description) // 4
        if token_estimate > 10000:
            return {
                "success": False,
                "error": "Job description is too large. Please use a description under ~40KB of text."
            }

        # Construct the prompt
        prompt = self._construct_prompt(job_title, job_description, company)

        try:
            # Send request to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a job-description analyzer. "
                            "Your job is to extract key information from job postings accurately. "
                            "Distinguish between required and preferred skills. "
                            "Do not invent any information. "
                            "If information is not mentioned, return 'Not mentioned' or empty list. "
                            "Always return valid JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for factual extraction
                max_tokens=1500  # Limit response to reduce costs
            )

            if not response.choices or len(response.choices) == 0:
                return {
                    "success": False,
                    "error": "No response received from AI service"
                }

            content = response.choices[0].message.content
            
            # Parse the JSON response
            parsed_analysis = self._parse_response(content)
            
            if not parsed_analysis:
                return {
                    "success": False,
                    "error": "AI returned invalid data format"
                }

            # Validate the parsed response
            validated = self._validate_response(parsed_analysis)
            
            return {
                "success": True,
                "analysis": validated
            }

        except (APIError, APIConnectionError, RateLimitError) as e:
            return {
                "success": False,
                "error": f"AI service temporarily unavailable: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error during analysis: {str(e)}"
            }

    def _validate_inputs(self, job_title: str, job_description: str) -> Optional[str]:
        """
        Validate user inputs.
        
        Args:
            job_title: The job title
            job_description: The job description
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not job_title or not job_title.strip():
            return "Please enter a job title"
        
        if len(job_title.strip()) < 2:
            return "Job title is too short (minimum 2 characters)"
        
        if not job_description or not job_description.strip():
            return "Please enter a job description"
        
        if len(job_description.strip()) < 50:
            return "Job description is too short. Please provide at least 50 characters."
        
        if len(job_description) > self.max_description_length:
            return f"Job description is too long (maximum {self.max_description_length} characters)"
        
        return None

    def _construct_prompt(
        self,
        job_title: str,
        job_description: str,
        company: Optional[str] = None
    ) -> str:
        """
        Construct a well-engineered prompt for the LLM.
        
        Args:
            job_title: The job title
            job_description: The job description
            company: Company name (optional)
            
        Returns:
            The complete prompt string
        """
        company_info = f"Company: {company}" if company and company.strip() else ""
        
        return f"""Analyze the following job posting and extract structured information.

IMPORTANT INSTRUCTIONS:
1. Extract ONLY information explicitly mentioned in the job description
2. Distinguish between REQUIRED skills and PREFERRED skills
3. Do NOT invent or assume any skills
4. For missing information, use "Not mentioned" (for text fields) or [] (for arrays)
5. Always return valid JSON with the exact keys shown below
6. Preserve technical terminology (e.g., "Spring Boot", "REST API", "SQL")
7. For arrays, return only items mentioned in the description

Job Title: {job_title}
{company_info}

Job Description:
{job_description}

Please extract the following information and return ONLY valid JSON (no other text):

{{
    "job_title": "Extracted or provided title",
    "company": "Company name if mentioned, otherwise 'Not mentioned'",
    "required_skills": ["Skills explicitly marked as required/must-have/mandatory"],
    "preferred_skills": ["Skills marked as preferred/nice-to-have/desired"],
    "programming_languages": ["Programming languages mentioned"],
    "frameworks": ["Frameworks/libraries mentioned (e.g., Spring Boot, React, Django)"],
    "tools": ["Development tools mentioned (e.g., Git, Docker, Jenkins)"],
    "databases": ["Databases mentioned (e.g., MySQL, PostgreSQL, MongoDB)"],
    "education": "Education requirement if mentioned, otherwise 'Not mentioned'",
    "experience": "Experience requirement if mentioned, otherwise 'Not mentioned'",
    "responsibilities": ["Key responsibilities listed in the posting"],
    "qualifications": ["Qualifications/qualities that make someone good at this job"],
    "keywords": ["Important technical keywords that appear in the description"]
}}

Return only valid JSON, no other text."""

    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse the AI response as JSON.
        
        Args:
            content: Raw response from the AI
            
        Returns:
            Parsed dictionary, or None if parsing fails
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from response with extra text
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
            
            return None

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize the AI response.
        
        Ensures all required fields exist and have correct types.
        
        Args:
            response: The parsed response from the AI
            
        Returns:
            Validated response with all fields present
        """
        expected_fields = {
            "job_title": str,
            "company": str,
            "required_skills": list,
            "preferred_skills": list,
            "programming_languages": list,
            "frameworks": list,
            "tools": list,
            "databases": list,
            "education": str,
            "experience": str,
            "responsibilities": list,
            "qualifications": list,
            "keywords": list
        }

        validated = {}

        for field, field_type in expected_fields.items():
            value = response.get(field)

            if field_type == list:
                if isinstance(value, list):
                    # Filter out "Not mentioned" from lists
                    validated[field] = [
                        item for item in value 
                        if item and str(item).lower() != "not mentioned"
                    ]
                elif isinstance(value, str):
                    if value.lower() == "not mentioned":
                        validated[field] = []
                    else:
                        validated[field] = [value]
                else:
                    validated[field] = []
            else:
                # For string fields
                if isinstance(value, str):
                    validated[field] = value
                else:
                    validated[field] = "Not mentioned"

        return validated


def get_job_analyzer() -> Optional[JobAnalyzer]:
    """
    Factory function to create a JobAnalyzer instance.
    
    Returns None if API key is not configured, allowing graceful degradation.
    
    Returns:
        JobAnalyzer instance, or None if not configured
    """
    try:
        return JobAnalyzer()
    except ValueError:
        # API key not configured
        return None
