function checkEmail() {
    const subject = document.getElementById("emailSubject").value;
    const body = document.getElementById("emailText").value;
    const sender = document.getElementById("emailSender").value;

    fetch("/predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ subject, body, sender })
    })
    .then(response => response.json())
    .then(data => {
        let resultDiv = document.getElementById("result");

        const reasons = Array.isArray(data.reasons) ? data.reasons.join("<br>") : "";
        const probability = typeof data.probability === "number"
            ? ` (${(data.probability * 100).toFixed(2)}%)`
            : "";
        resultDiv.innerHTML = `<strong>${data.prediction}${probability}</strong><br>${reasons}`;
        resultDiv.style.color = data.prediction === "Phishing"
            ? "red"
            : data.prediction === "Suspicious" ? "orange" : "green";
    });
}