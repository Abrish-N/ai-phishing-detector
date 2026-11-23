const PANEL_ID = "gmail-phishing-bar";
const API_URL = "http://127.0.0.1:5000/predict";
const EMAIL_BODY_SELECTORS = [
    "div.a3s",
    "div[aria-label='Message Body']",
    "div[role='textbox']"
];
const SENDER_SELECTORS = [
    "span.gD",
    "span[email]",
    "span.hb",
    "span.go"
];
let analyzeTimeout = null;
let lastEmailText = "";

function findEmailSubject() {
    const subjectElement = document.querySelector("h2.hP, h2[role='heading']");
    return subjectElement ? subjectElement.innerText.trim() : "";
}

function findEmailBodyElement() {
    for (const selector of EMAIL_BODY_SELECTORS) {
        const element = document.querySelector(selector);
        if (element && element.innerText.trim()) {
            return element;
        }
    }
    return null;
}

function findEmailViewRoot() {
    const bodyElement = findEmailBodyElement();
    if (!bodyElement) {
        return null;
    }

    return bodyElement.closest("div.adn") ||
           bodyElement.closest("div.if") ||
           bodyElement.closest("div[role='article']") ||
           bodyElement.closest("div[role='main']") ||
           bodyElement.parentElement;
}

function findSenderEmail() {
    for (const selector of SENDER_SELECTORS) {
        const element = document.querySelector(selector);
        if (!element) continue;
        const email = element.getAttribute("email") || element.textContent;
        if (email && email.trim()) {
            return email.trim();
        }
    }
    return null;
}

function findInsertionRoot() {
    const root = findEmailViewRoot();
    if (!root) {
        return null;
    }

    const headerRoot = root.querySelector(
        "div.ajR, div.ha, div.hX, div.gE, div.gD, div.hP, div.h7, div[aria-label='Message details']"
    );

    return headerRoot || root;
}

function removeToolbar() {
    const bar = document.getElementById(PANEL_ID);
    if (bar) {
        bar.remove();
    }
}

function createToolbar() {
    const root = findInsertionRoot();
    if (!root) {
        return null;
    }

    let bar = document.getElementById(PANEL_ID);
    if (!bar) {
        bar = document.createElement("div");
        bar.id = PANEL_ID;
        bar.className = "gmail-phishing-bar";
        bar.innerHTML = `
            <div class="gmail-phishing-message risk-low">
                <div class="bar-header">
                    <span class="bar-title">Phishing Email</span>
                    <span class="bar-risk">Risk: 0%</span>
                </div>
                <div class="bar-meter">
                    <div class="bar-meter-fill" style="width:0%"></div>
                </div>
                <div class="bar-reasons-block">
                    <strong>Reasons:</strong>
                    <ul class="bar-reason-list">
                        <li>Checking email content...</li>
                    </ul>
                </div>
            </div>
        `;

        if (root.parentElement && root.parentElement.contains(root)) {
            root.parentElement.insertBefore(bar, root);
        } else {
            root.prepend(bar);
        }
    }
    return bar;
}

function updateToolbar(risk, verdict, reasons) {
    const bar = createToolbar();
    if (!bar) return;

    const colorClass = risk > 70 ? "risk-high" : risk > 40 ? "risk-med" : "risk-low";
    const safeReasons = Array.isArray(reasons) ? reasons : [];
    const reasonItems = safeReasons.length
        ? safeReasons.map(reason => `<li>${reason}</li>`).join("")
        : `<li>No immediate threats detected.</li>`;
    const clampedRisk = Math.max(0, Math.min(100, risk));

    bar.innerHTML = `
        <div class="gmail-phishing-message ${colorClass}">
            <div class="bar-header">
                <span class="bar-title">Phishing Email</span>
                <span class="bar-risk">Risk: ${clampedRisk}%</span>
            </div>
            <div class="bar-meter">
                <div class="bar-meter-fill" style="width:${clampedRisk}%"></div>
            </div>
            <div class="bar-reasons-block">
                <strong>Reasons:</strong>
                <ul class="bar-reason-list">
                    ${reasonItems}
                </ul>
            </div>
        </div>
    `;
}

function analyzeEmail(force = false) {
    const bodyElement = findEmailBodyElement();
    if (!bodyElement) {
        removeToolbar();
        return;
    }

    const subject = findEmailSubject();
    const body = bodyElement.innerText.trim();
    const text = `${subject} ${body}`.trim();
    if (!text) {
        removeToolbar();
        return;
    }

    if (!force && text === lastEmailText) {
        return;
    }

    lastEmailText = text;
    createToolbar();

    const sender = findSenderEmail();
    fetch(API_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ subject, body, sender })
    })
    .then(response => response.json())
    .then(data => {
        const risk = data.risk ?? 0;
        const verdict = data.prediction ?? "Unknown";
        updateToolbar(risk, verdict, data.reasons || []);
    })
    .catch(() => {
        updateToolbar(0, "Unable to analyze", ["Local API not available."]);
    });
}

function scheduleAnalyze(force = false) {
    if (analyzeTimeout) {
        clearTimeout(analyzeTimeout);
    }
    analyzeTimeout = setTimeout(() => {
        analyzeEmail(force);
        analyzeTimeout = null;
    }, 400);
}

function init() {
    scheduleAnalyze(true);
    const observer = new MutationObserver(() => {
        scheduleAnalyze();
    });
    observer.observe(document.body, { childList: true, subtree: true });
}

window.addEventListener("load", init);
setTimeout(init, 1000);
