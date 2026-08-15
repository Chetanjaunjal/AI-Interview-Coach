"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const currentYear = document.querySelector("#current-year");

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }

    // Resume Analysis
    const analyzeButton = document.querySelector("#analyze-button");
    if (analyzeButton) {
        analyzeButton.addEventListener("click", handleAnalyzeResume);
    }

    // Job Analysis Form
    const jobAnalysisForm = document.querySelector("#job-analysis-form");
    if (jobAnalysisForm) {
        jobAnalysisForm.addEventListener("submit", handleAnalyzeJob);
        
        // Character counter for job description
        const jobDescriptionField = document.querySelector("#job-description");
        const charCountSpan = document.querySelector("#char-count");
        if (jobDescriptionField && charCountSpan) {
            jobDescriptionField.addEventListener("input", () => {
                charCountSpan.textContent = jobDescriptionField.value.length;
            });
        }
    }

    // Match Resume Button
    const matchButton = document.querySelector("#match-button");
    if (matchButton) {
        matchButton.addEventListener("click", handleMatchResume);
    }
});

/**
 * Handle resume analysis button click.
 * 
 * This function:
 * 1. Extracts the resume text from the page
 * 2. Sends it to the /api/analyze-resume endpoint
 * 3. Shows a loading state while waiting for the API
 * 4. Displays the analysis results or an error message
 */
async function handleAnalyzeResume() {
    const analyzeButton = document.querySelector("#analyze-button");
    const analysisStatus = document.querySelector("#analysis-status");
    const analysisResults = document.querySelector("#analysis-results");
    const analysisContent = document.querySelector("#analysis-content");

    // Extract resume text from the <pre> element
    const extractedTextSection = document.querySelector(".extracted-text pre");
    if (!extractedTextSection) {
        analysisStatus.textContent = "Error: Could not find resume text.";
        analysisStatus.style.display = "block";
        analysisStatus.className = "analysis-status error";
        return;
    }

    const resumeText = extractedTextSection.textContent.trim();

    if (!resumeText) {
        analysisStatus.textContent = "Error: Resume text is empty.";
        analysisStatus.style.display = "block";
        analysisStatus.className = "analysis-status error";
        return;
    }

    // Show loading state
    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing your resume...";
    analysisStatus.textContent = "Analyzing your resume with AI...";
    analysisStatus.style.display = "block";
    analysisStatus.className = "analysis-status loading";
    analysisResults.style.display = "none";

    try {
        // Send to API
        const response = await fetch("/api/analyze-resume", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                resume_text: resumeText
            })
        });

        const data = await response.json();

        if (data.success && data.analysis) {
            // Display analysis results
            displayAnalysisResults(data.analysis);
            analysisStatus.textContent = "Resume analysis completed.";
            analysisStatus.className = "analysis-status success";
        } else {
            // Show error message from API
            analysisStatus.textContent = `Unable to analyze the resume: ${data.error || "Unknown error"}`;
            analysisStatus.className = "analysis-status error";
            analysisResults.style.display = "none";
        }
    } catch (error) {
        // Network or other errors
        analysisStatus.textContent = "Unable to analyze the resume. Please check your internet connection and try again.";
        analysisStatus.className = "analysis-status error";
        analysisResults.style.display = "none";
        console.error("Error analyzing resume:", error);
    } finally {
        // Restore button state
        analyzeButton.disabled = false;
        analyzeButton.textContent = "Analyze Resume with AI";
    }
}

/**
 * Display the analysis results on the page.
 * 
 * Args:
 *     analysis: The parsed analysis object from the API
 * 
 * This function takes the structured JSON response from the AI
 * and formats it nicely on the page using HTML.
 */
function displayAnalysisResults(analysis) {
    const analysisContent = document.querySelector("#analysis-content");
    const analysisResults = document.querySelector("#analysis-results");

    // Start building the HTML
    let html = '<div class="analysis-grid">';

    // Helper function to display a field
    const displayField = (label, value, isList = false) => {
        let formattedValue;

        if (isList && Array.isArray(value) && value.length > 0) {
            formattedValue = value
                .map(item => `<li>${escapeHtml(item)}</li>`)
                .join("");
            return `
                <div class="analysis-field">
                    <h4>${label}</h4>
                    <ul>${formattedValue}</ul>
                </div>
            `;
        } else if (!isList && value && value !== "Not mentioned") {
            return `
                <div class="analysis-field">
                    <h4>${label}</h4>
                    <p>${escapeHtml(value)}</p>
                </div>
            `;
        } else if (isList && Array.isArray(value) && value.length === 0) {
            return `
                <div class="analysis-field">
                    <h4>${label}</h4>
                    <p class="not-mentioned">Not mentioned</p>
                </div>
            `;
        } else {
            return `
                <div class="analysis-field">
                    <h4>${label}</h4>
                    <p class="not-mentioned">${escapeHtml(value || "Not mentioned")}</p>
                </div>
            `;
        }
    };

    // Display each field
    html += displayField("Name", analysis.name);
    html += displayField("Email", analysis.email);
    html += displayField("Phone", analysis.phone);
    html += displayField("Education", analysis.education, true);
    html += displayField("Skills", analysis.skills, true);
    html += displayField("Experience", analysis.experience, true);
    html += displayField("Projects", analysis.projects, true);
    html += displayField("Certifications", analysis.certifications, true);
    html += displayField("Achievements", analysis.achievements, true);

    html += "</div>";

    analysisContent.innerHTML = html;
    analysisResults.style.display = "block";

    // Check if both analyses are complete and show match button
    updateMatchButtonVisibility();
}

/**
 * Escape HTML special characters to prevent XSS attacks.
 * 
 * Args:
 *     text: The text to escape
 * 
 * Returns:
 *     The escaped text safe to insert into HTML
 * 
 * This is important for security: the AI might return text that contains
 * HTML characters like <, >, &, etc. We need to escape them so they
 * display as text, not as HTML code.
 */
function escapeHtml(text) {
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Handle job description analysis form submission.
 * 
 * This function:
 * 1. Gets form data (job title, company, description)
 * 2. Sends it to the /api/analyze-job endpoint
 * 3. Shows loading state while waiting for the API
 * 4. Displays results or error message
 */
async function handleAnalyzeJob(event) {
    event.preventDefault();

    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const analysisStatus = document.querySelector("#job-analysis-status");
    const analysisResults = document.querySelector("#job-analysis-results");
    const analysisContent = document.querySelector("#job-analysis-content");

    const jobTitle = document.querySelector("#job-title").value.trim();
    const company = document.querySelector("#company").value.trim();
    const jobDescription = document.querySelector("#job-description").value.trim();

    // Validate on client-side for better UX
    if (!jobTitle) {
        analysisStatus.textContent = "Error: Please enter a job title.";
        analysisStatus.style.display = "block";
        analysisStatus.className = "analysis-status error";
        return;
    }

    if (!jobDescription) {
        analysisStatus.textContent = "Error: Please enter a job description.";
        analysisStatus.style.display = "block";
        analysisStatus.className = "analysis-status error";
        return;
    }

    if (jobDescription.length < 50) {
        analysisStatus.textContent = "Error: Job description is too short (minimum 50 characters).";
        analysisStatus.style.display = "block";
        analysisStatus.className = "analysis-status error";
        return;
    }

    // Show loading state
    submitButton.disabled = true;
    submitButton.textContent = "Analyzing job description...";
    analysisStatus.textContent = "Analyzing job description with AI...";
    analysisStatus.style.display = "block";
    analysisStatus.className = "analysis-status loading";
    analysisResults.style.display = "none";

    try {
        // Send to API
        const response = await fetch("/api/analyze-job", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                job_title: jobTitle,
                company: company || null,
                job_description: jobDescription
            })
        });

        const data = await response.json();

        if (data.success && data.analysis) {
            // Display job analysis results
            displayJobAnalysisResults(data.analysis);
            analysisStatus.textContent = "Job description analyzed successfully.";
            analysisStatus.className = "analysis-status success";
        } else {
            // Show error message from API
            analysisStatus.textContent = `Unable to analyze job description: ${data.error || "Unknown error"}`;
            analysisStatus.className = "analysis-status error";
            analysisResults.style.display = "none";
        }
    } catch (error) {
        // Network or other errors
        analysisStatus.textContent = "Unable to analyze job description. Please check your internet connection and try again.";
        analysisStatus.className = "analysis-status error";
        analysisResults.style.display = "none";
        console.error("Error analyzing job:", error);
    } finally {
        // Restore button state
        submitButton.disabled = false;
        submitButton.textContent = "Analyze Job Description";
    }
}

/**
 * Display the job analysis results on the page.
 * 
 * Args:
 *     analysis: The parsed job analysis object from the API
 * 
 * This function takes the structured JSON response from the AI
 * and formats it nicely on the page using HTML.
 */
function displayJobAnalysisResults(analysis) {
    const analysisContent = document.querySelector("#job-analysis-content");
    const analysisResults = document.querySelector("#job-analysis-results");

    // Start building the HTML
    let html = '<div class="job-analysis-grid">';

    // Helper function to display a field
    const displayField = (label, value, isList = false) => {
        let formattedValue;

        if (isList && Array.isArray(value) && value.length > 0) {
            formattedValue = value
                .map(item => `<li>${escapeHtml(String(item))}</li>`)
                .join("");
            return `
                <div class="job-field">
                    <h4>${label}</h4>
                    <ul>${formattedValue}</ul>
                </div>
            `;
        } else if (!isList && value && value !== "Not mentioned") {
            return `
                <div class="job-field">
                    <h4>${label}</h4>
                    <p>${escapeHtml(String(value))}</p>
                </div>
            `;
        } else if (isList && Array.isArray(value) && value.length === 0) {
            return `
                <div class="job-field">
                    <h4>${label}</h4>
                    <p class="not-mentioned">Not mentioned</p>
                </div>
            `;
        } else {
            return `
                <div class="job-field">
                    <h4>${label}</h4>
                    <p class="not-mentioned">${escapeHtml(String(value || "Not mentioned"))}</p>
                </div>
            `;
        }
    };

    // Display each field
    html += displayField("Job Title", analysis.job_title);
    html += displayField("Company", analysis.company);
    html += displayField("Required Skills", analysis.required_skills, true);
    html += displayField("Preferred Skills", analysis.preferred_skills, true);
    html += displayField("Programming Languages", analysis.programming_languages, true);
    html += displayField("Frameworks", analysis.frameworks, true);
    html += displayField("Tools", analysis.tools, true);
    html += displayField("Databases", analysis.databases, true);
    html += displayField("Education", analysis.education);
    html += displayField("Experience", analysis.experience);
    html += displayField("Responsibilities", analysis.responsibilities, true);
    html += displayField("Qualifications", analysis.qualifications, true);
    html += displayField("Keywords", analysis.keywords, true);

    html += "</div>";

    analysisContent.innerHTML = html;
    analysisResults.style.display = "block";

    // Check if both analyses are complete and show match button
    updateMatchButtonVisibility();
}

/**
 * Check if both resume and job analyses are complete.
 * If so, show the match button. Otherwise, hide it.
 * 
 * This prevents users from trying to match if either analysis is missing.
 */
function updateMatchButtonVisibility() {
    const resumeAnalysisSection = document.querySelector("#analysis-results");
    const jobAnalysisSection = document.querySelector("#job-analysis-results");
    const matchButton = document.querySelector("#match-button");

    if (!matchButton) return;

    // Both analyses must be visible
    const resumeAnalyzed = resumeAnalysisSection && resumeAnalysisSection.style.display !== "none";
    const jobAnalyzed = jobAnalysisSection && jobAnalysisSection.style.display !== "none";

    if (resumeAnalyzed && jobAnalyzed) {
        matchButton.style.display = "block";
    } else {
        matchButton.style.display = "none";
    }
}

/**
 * Handle the match resume button click.
 * 
 * This function:
 * 1. Sends a request to /api/match-resume
 * 2. Shows loading state while waiting
 * 3. Displays matching results or error message
 * 4. Renders the match score and skill breakdowns
 */
async function handleMatchResume() {
    const matchButton = document.querySelector("#match-button");
    const matchStatus = document.querySelector("#match-status");
    const matchingResults = document.querySelector("#matching-results");

    // Show loading state
    matchButton.disabled = true;
    matchButton.textContent = "Matching resume to job...";
    matchStatus.textContent = "Matching your resume to the job requirements...";
    matchStatus.style.display = "block";
    matchStatus.className = "analysis-status loading";
    matchingResults.style.display = "none";

    try {
        // Send to API
        const response = await fetch("/api/match-resume", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (data.success && data.result) {
            // Display matching results
            displayMatchingResults(data.result);
            matchStatus.textContent = "Matching complete!";
            matchStatus.className = "analysis-status success";
        } else {
            // Show error message from API
            matchStatus.textContent = `Unable to match resume: ${data.error || "Unknown error"}`;
            matchStatus.className = "analysis-status error";
            matchingResults.style.display = "none";
        }
    } catch (error) {
        // Network or other errors
        matchStatus.textContent = "Unable to match resume. Please check your internet connection and try again.";
        matchStatus.className = "analysis-status error";
        matchingResults.style.display = "none";
        console.error("Error matching resume:", error);
    } finally {
        // Restore button state
        matchButton.disabled = false;
        matchButton.textContent = "Match Resume to Job";
    }
}

/**
 * Display the matching results on the page.
 * 
 * Args:
 *     result: The matching result object from the API containing:
 *             - match_percentage: 0-100
 *             - matched_required_skills: []
 *             - missing_required_skills: []
 *             - matched_preferred_skills: []
 *             - missing_preferred_skills: []
 *             - additional_candidate_skills: []
 *             - recommendations: []
 */
function displayMatchingResults(result) {
    const matchPercentage = document.querySelector("#match-percentage");
    
    // Exact match sections
    const exactMatchedRequiredSection = document.querySelector("#exact-matched-required-section");
    const exactMatchedRequiredList = document.querySelector("#exact-matched-required-list");
    const exactMatchedPreferredSection = document.querySelector("#exact-matched-preferred-section");
    const exactMatchedPreferredList = document.querySelector("#exact-matched-preferred-list");
    
    // Semantic match sections
    const semanticMatchedRequiredSection = document.querySelector("#semantic-matched-required-section");
    const semanticMatchedRequiredList = document.querySelector("#semantic-matched-required-list");
    const semanticMatchedPreferredSection = document.querySelector("#semantic-matched-preferred-section");
    const semanticMatchedPreferredList = document.querySelector("#semantic-matched-preferred-list");
    
    // Legacy combined sections (for backward compatibility)
    const matchedRequiredSection = document.querySelector("#matched-required-section");
    const matchedRequiredList = document.querySelector("#matched-required-list");
    const matchedPreferredSection = document.querySelector("#matched-preferred-section");
    const matchedPreferredList = document.querySelector("#matched-preferred-list");
    
    // Missing and additional skills sections
    const missingRequiredSection = document.querySelector("#missing-required-section");
    const missingRequiredList = document.querySelector("#missing-required-list");
    const missingPreferredSection = document.querySelector("#missing-preferred-section");
    const missingPreferredList = document.querySelector("#missing-preferred-list");
    const additionalSkillsSection = document.querySelector("#additional-skills-section");
    const additionalSkillsList = document.querySelector("#additional-skills-list");
    const recommendationsSection = document.querySelector("#recommendations-section");
    const recommendationsList = document.querySelector("#recommendations-list");
    const matchingResults = document.querySelector("#matching-results");

    // Display match percentage
    const percentage = result.match_percentage || 0;
    if (matchPercentage) {
        matchPercentage.textContent = `${percentage}%`;
    }

    // Helper function to separate exact and semantic matches
    function separateMatches(matchedSkills) {
        const exact = [];
        const semantic = [];
        
        if (!Array.isArray(matchedSkills)) {
            return { exact, semantic };
        }
        
        for (const match of matchedSkills) {
            if (typeof match === 'string') {
                // Legacy format (just skill name)
                exact.push(match);
            } else if (typeof match === 'object' && match.match_type) {
                if (match.match_type === 'exact') {
                    exact.push(match.candidate_skill || match.job_skill);
                } else if (match.match_type === 'semantic') {
                    semantic.push(match);
                }
            }
        }
        
        return { exact, semantic };
    }

    // Process required skills
    const requiredMatches = separateMatches(result.matched_required_skills);
    
    // Display exact matched required skills
    if (requiredMatches.exact.length > 0) {
        exactMatchedRequiredList.innerHTML = requiredMatches.exact
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        exactMatchedRequiredSection.style.display = "block";
    } else {
        exactMatchedRequiredSection.style.display = "none";
    }

    // Display semantic matched required skills
    if (requiredMatches.semantic.length > 0) {
        semanticMatchedRequiredList.innerHTML = requiredMatches.semantic
            .map(match => {
                const similarity = Math.round(match.similarity * 100);
                const html = `
                    <li>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${escapeHtml(match.job_skill)}</strong>
                                <br/>
                                <small style="color: #666;">Your skill: ${escapeHtml(match.candidate_skill)}</small>
                            </div>
                            <div style="text-align: right; font-weight: bold; color: #27ae60;">
                                ${similarity}%
                            </div>
                        </div>
                    </li>
                `;
                return html;
            })
            .join("");
        semanticMatchedRequiredSection.style.display = "block";
    } else {
        semanticMatchedRequiredSection.style.display = "none";
    }

    // Hide legacy combined section if using new format
    if (result.matched_required_skills && Array.isArray(result.matched_required_skills) && result.matched_required_skills.length > 0 && typeof result.matched_required_skills[0] === 'object') {
        matchedRequiredSection.style.display = "none";
    } else if (result.matched_required_skills && result.matched_required_skills.length > 0) {
        // Legacy format
        matchedRequiredList.innerHTML = result.matched_required_skills
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        matchedRequiredSection.style.display = "block";
    } else {
        matchedRequiredSection.style.display = "none";
    }

    // Display missing required skills
    if (result.missing_required_skills && result.missing_required_skills.length > 0) {
        missingRequiredList.innerHTML = result.missing_required_skills
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        missingRequiredSection.style.display = "block";
    } else {
        missingRequiredSection.style.display = "none";
    }

    // Process preferred skills
    const preferredMatches = separateMatches(result.matched_preferred_skills);

    // Display exact matched preferred skills
    if (preferredMatches.exact.length > 0) {
        exactMatchedPreferredList.innerHTML = preferredMatches.exact
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        exactMatchedPreferredSection.style.display = "block";
    } else {
        exactMatchedPreferredSection.style.display = "none";
    }

    // Display semantic matched preferred skills
    if (preferredMatches.semantic.length > 0) {
        semanticMatchedPreferredList.innerHTML = preferredMatches.semantic
            .map(match => {
                const similarity = Math.round(match.similarity * 100);
                const html = `
                    <li>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${escapeHtml(match.job_skill)}</strong>
                                <br/>
                                <small style="color: #666;">Your skill: ${escapeHtml(match.candidate_skill)}</small>
                            </div>
                            <div style="text-align: right; font-weight: bold; color: #27ae60;">
                                ${similarity}%
                            </div>
                        </div>
                    </li>
                `;
                return html;
            })
            .join("");
        semanticMatchedPreferredSection.style.display = "block";
    } else {
        semanticMatchedPreferredSection.style.display = "none";
    }

    // Hide legacy combined section if using new format
    if (result.matched_preferred_skills && Array.isArray(result.matched_preferred_skills) && result.matched_preferred_skills.length > 0 && typeof result.matched_preferred_skills[0] === 'object') {
        matchedPreferredSection.style.display = "none";
    } else if (result.matched_preferred_skills && result.matched_preferred_skills.length > 0) {
        // Legacy format
        matchedPreferredList.innerHTML = result.matched_preferred_skills
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        matchedPreferredSection.style.display = "block";
    } else {
        matchedPreferredSection.style.display = "none";
    }

    // Display missing preferred skills
    if (result.missing_preferred_skills && result.missing_preferred_skills.length > 0) {
        missingPreferredList.innerHTML = result.missing_preferred_skills
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        missingPreferredSection.style.display = "block";
    } else {
        missingPreferredSection.style.display = "none";
    }

    // Display additional candidate skills
    if (result.additional_candidate_skills && result.additional_candidate_skills.length > 0) {
        additionalSkillsList.innerHTML = result.additional_candidate_skills
            .map(skill => `<li>${escapeHtml(skill)}</li>`)
            .join("");
        additionalSkillsSection.style.display = "block";
    } else {
        additionalSkillsSection.style.display = "none";
    }

    // Display recommendations
    if (result.recommendations && result.recommendations.length > 0) {
        recommendationsList.innerHTML = result.recommendations
            .map(rec => `<li>${escapeHtml(rec)}</li>`)
            .join("");
        recommendationsSection.style.display = "block";
    } else {
        recommendationsSection.style.display = "none";
    }

    // Show the entire results section
    matchingResults.style.display = "block";
}
