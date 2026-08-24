"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const answer = document.querySelector("#answer");
    const record = document.querySelector("#record-answer");
    const stop = document.querySelector("#stop-recording");
    const speak = document.querySelector("#speak-question");
    const status = document.querySelector("#voice-status");
    const timer = document.querySelector("#voice-timer");
    const durationField = document.querySelector("#voice-duration");
    const wordField = document.querySelector("#voice-word-count");
    const fillerField = document.querySelector("#voice-filler-count");
    const question = document.querySelector(".active-question h2").textContent;
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    let finalTranscript = "";
    let startedAt = 0;
    let timerId;
    let state = "IDLE";

    function setState(nextState, message) {
        state = nextState;
        status.textContent = message;
        status.className = nextState === "ERROR" ? "analysis-status error" : "analysis-status";
    }

    function speakQuestion() {
        if (!window.speechSynthesis) {
            setState("ERROR", "Text-to-speech is not supported in this browser.");
            return;
        }
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(question);
        utterance.onerror = () => setState("ERROR", "The question could not be read aloud.");
        window.speechSynthesis.speak(utterance);
    }

    function countMetrics() {
        const text = answer.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        const fillers = (text.match(/\b(um|uh|like|actually)\b/gi) || []).length + (text.match(/\byou know\b/gi) || []).length;
        wordField.value = words;
        fillerField.value = fillers;
    }

    speak.addEventListener("click", speakQuestion);
    answer.addEventListener("input", countMetrics);

    if (!Recognition) {
        setState("ERROR", "Voice input is not supported in this browser. You can type your answer instead.");
        record.disabled = true;
        return;
    }

    recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onstart = () => setState("LISTENING", "Listening... speak your answer.");
    recognition.onresult = event => {
        let interimTranscript = "";
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
            if (event.results[index].isFinal) finalTranscript += event.results[index][0].transcript + " ";
            else interimTranscript += event.results[index][0].transcript;
        }
        const transcript = `${finalTranscript}${interimTranscript}`;
        if (transcript.length > 5000) {
            recognition.stop();
            setState("ERROR", "Your transcript is over the 5,000 character limit. Please edit it before submitting.");
            return;
        }
        answer.value = transcript.trim();
        countMetrics();
    };
    recognition.onerror = event => {
        const message = event.error === "not-allowed" ? "Microphone permission is required for voice interview mode." : event.error === "no-speech" ? "No answer was detected. Please try again." : "Voice input stopped unexpectedly. You can type your answer instead.";
        setState("ERROR", message);
        record.disabled = false;
        stop.disabled = true;
    };
    recognition.onend = () => {
        if (state === "LISTENING") setState("TRANSCRIBED", answer.value.trim() ? "Transcript ready. Review it before submitting." : "No answer was detected. Please try again.");
        record.disabled = false;
        stop.disabled = true;
        if (startedAt) {
            const seconds = Math.round((Date.now() - startedAt) / 1000);
            durationField.value = seconds;
            clearInterval(timerId);
        }
    };
    record.addEventListener("click", () => {
        try {
            state = "REQUESTING_PERMISSION";
            recognition.start();
            startedAt = Date.now();
            record.disabled = true;
            stop.disabled = false;
            timerId = setInterval(() => { timer.textContent = `Recording: ${String(Math.floor((Date.now() - startedAt) / 1000)).padStart(2, "0")} sec`; }, 1000);
        } catch (error) {
            setState("ERROR", "Microphone is unavailable. You can type your answer instead.");
        }
    });
    stop.addEventListener("click", () => recognition.stop());
});
