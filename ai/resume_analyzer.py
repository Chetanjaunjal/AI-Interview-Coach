"""
Resume Analyzer Module

This module handles communication with OpenAI's API to analyze resume text
and extract structured information.

Separation of concerns:
- app.py handles HTTP requests and Flask routing
- resume_analyzer.py handles AI API communication
- This keeps code modular and testable
"""

import json
import os
from typing import Optional, Dict, Any

import requests
from openai import OpenAI, APIError, APIConnectionError, RateLimitError


class ResumeAnalyzer:
    """
    Analyzes resume text using OpenAI's LLM API.
    
    This class encapsulates all AI API communication logic.
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
        self.model = "gpt-4o-mini"  # Using affordable model suitable for students

    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Analyze resume text and extract structured information.
        
        Args:
            resume_text: Raw text extracted from the PDF resume
            
        Returns:
            Dictionary with extracted resume information, or error details
            
        Raises:
            ValueError: If resume_text is empty or too large
            APIError: If OpenAI API fails (handled gracefully)
            APIConnectionError: If network connection fails (handled gracefully)
        """
        # Validate input
        if not resume_text or not resume_text.strip():
            return {
                "success": False,
                "error": "No resume text provided"
            }
        
        # Token warning: Large resumes cost more
        # This is a basic check - 1 token ≈ 4 characters
        token_estimate = len(resume_text) // 4
        if token_estimate > 8000:
            return {
                "success": False,
                "error": "Resume text is too large. Please use a resume under ~32KB of text."
            }

        # Construct the prompt
        # This prompt is carefully engineered to:
        # 1. Specify the exact format (JSON)
        # 2. Tell the AI not to invent information
        # 3. Provide default values for missing info
        prompt = self._construct_prompt(resume_text)

        try:
            # Send request to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional resume analyzer. "
                            "Your job is to extract information from resumes accurately. "
                            "Do not invent any information. "
                            "If a field is not mentioned in the resume, return 'Not mentioned'. "
                            "Always return valid JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature = more consistent, less creative (good for facts)
                max_tokens=1000  # Limit response length to reduce costs
            )

            # Extract the response content
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
            # API errors are expected sometimes (rate limits, service issues)
            return {
                "success": False,
                "error": f"AI service temporarily unavailable: {str(e)}"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "success": False,
                "error": f"Unexpected error during analysis: {str(e)}"
            }

    def _construct_prompt(self, resume_text: str) -> str:
        """
        Construct a well-engineered prompt for the LLM.
        
        Prompt engineering principles used:
        - Clear task definition
        - Specific output format (JSON)
        - Explicit instructions not to invent data
        - Default values for missing information
        
        Args:
            resume_text: The resume text to analyze
            
        Returns:
            The complete prompt string
        """
        return f"""Analyze the following resume text and extract the requested information.

IMPORTANT INSTRUCTIONS:
1. Extract ONLY information explicitly mentioned in the resume
2. Do NOT invent or assume any information
3. If a field is not mentioned, return: "Not mentioned"
4. Always return valid JSON with the exact keys shown below
5. For arrays (education, skills, etc.), return as a list

Please extract the following information and return ONLY valid JSON (no other text):

{{
    "name": "Full name if mentioned, otherwise 'Not mentioned'",
    "email": "Email address if mentioned, otherwise 'Not mentioned'",
    "phone": "Phone number if mentioned, otherwise 'Not mentioned'",
    "education": ["List of degrees/schools if mentioned, otherwise []"],
    "skills": ["List of technical/professional skills if mentioned, otherwise []"],
    "projects": ["List of projects if mentioned, otherwise []"],
    "certifications": ["List of certifications if mentioned, otherwise []"],
    "experience": ["List of job titles/companies if mentioned, otherwise []"],
    "achievements": ["List of achievements/accomplishments if mentioned, otherwise []"]
}}

RESUME TEXT TO ANALYZE:
{resume_text}

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
            # Try to parse the content as JSON
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError:
            # If the AI included extra text, try to extract JSON
            try:
                # Look for JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    parsed = json.loads(json_str)
                    return parsed
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
        # Define expected structure
        expected_fields = {
            "name": str,
            "email": str,
            "phone": str,
            "education": list,
            "skills": list,
            "projects": list,
            "certifications": list,
            "experience": list,
            "achievements": list
        }

        validated = {}

        for field, field_type in expected_fields.items():
            value = response.get(field)

            # Convert lists with single items to proper format
            if field_type == list:
                if isinstance(value, list):
                    validated[field] = value
                elif isinstance(value, str):
                    # If it's a string, convert to list (unless it's "Not mentioned")
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


def get_analyzer() -> Optional[ResumeAnalyzer]:
    """
    Factory function to create a ResumeAnalyzer instance.
    
    Returns None if API key is not configured, allowing the app to run
    in a graceful degraded state.
    
    Returns:
        ResumeAnalyzer instance, or None if not configured
    """
    try:
        return ResumeAnalyzer()
    except ValueError:
        # API key not configured
        return None
