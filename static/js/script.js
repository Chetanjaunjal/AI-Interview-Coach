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
