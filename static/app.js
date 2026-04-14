var pc = null;
var audioEl = null;
var isConnecting = false;
var gameState = { score: 0, correct_count: 0, incorrect_count: 0, total_words: 0 };

function showScreen(id) {
    document.querySelectorAll(".screen").forEach(function (s) {
        s.classList.remove("active");
        s.classList.add("hidden");
    });
    var el = document.getElementById(id);
    el.classList.remove("hidden");
    el.classList.add("active");
}

function showError(msg) {
    var el = document.getElementById("start-error");
    el.textContent = msg;
    el.classList.remove("hidden");
}

function hideError() {
    document.getElementById("start-error").classList.add("hidden");
}

function setBotStatus(status, text) {
    document.getElementById("bot-status").className = "bot-status " + status;
    document.getElementById("bot-status-text").textContent = text;
}

function updateUI() {
    document.getElementById("score").textContent = gameState.score;
    document.getElementById("correct-count").textContent = gameState.correct_count;
    document.getElementById("incorrect-count").textContent = gameState.incorrect_count;
    document.getElementById("total-words").textContent = gameState.total_words;
}

function handleDataMessage(raw) {
    console.log("Data channel message:", raw);
    try {
        var data = JSON.parse(raw);
        if (data.game_over) {
            gameState.score = data.score || 0;
            gameState.correct_count = data.correct_count || 0;
            gameState.incorrect_count = data.incorrect_count || 0;
            gameState.total_words = data.total_words || 0;
            updateUI();
            leaveGame();
            return;
        }
        if (data.score !== undefined) {
            gameState.score = data.score || 0;
            gameState.correct_count = data.correct_count || 0;
            gameState.incorrect_count = data.incorrect_count || 0;
            gameState.total_words = data.total_words || 0;
            updateUI();
        }
    } catch (e) {}
}

async function startGame() {
    if (isConnecting) return;
    hideError();

    var nameInput = document.getElementById("player-name");
    var name = nameInput.value.trim();
    if (!name) {
        showError("Please enter your name to start the game.");
        nameInput.focus();
        return;
    }

    isConnecting = true;
    var btn = document.getElementById("start-btn");
    btn.disabled = true;
    btn.textContent = "Connecting...";

    try {
        pc = new RTCPeerConnection();

        // Get user mic
        var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(function (track) {
            pc.addTrack(track, stream);
        });

        // Receive bot audio
        pc.addTransceiver("audio", { direction: "recvonly" });

        pc.ontrack = function (event) {
            if (event.streams && event.streams[0]) {
                audioEl = new Audio();
                audioEl.srcObject = event.streams[0];
                audioEl.autoplay = true;
            }
        };

        // Create data channel — Pipecat server receives this and sends game state back on it
        var dc = pc.createDataChannel("chat");
        dc.onopen = function () {
            console.log("Data channel open");
        };
        dc.onmessage = function (msg) {
            handleDataMessage(msg.data);
        };

        // Also listen for server-created channels
        pc.ondatachannel = function (event) {
            var channel = event.channel;
            channel.onmessage = function (msg) {
                handleDataMessage(msg.data);
            };
        };

        pc.oniceconnectionstatechange = function () {
            if (pc.iceConnectionState === "connected") {
                setBotStatus("active", "Bot is speaking...");
            } else if (pc.iceConnectionState === "disconnected" || pc.iceConnectionState === "failed") {
                handleGameEnd();
            }
        };

        var offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // Wait for ICE candidates
        await new Promise(function (resolve) {
            if (pc.iceGatheringState === "complete") {
                resolve();
            } else {
                pc.onicegatheringstatechange = function () {
                    if (pc.iceGatheringState === "complete") resolve();
                };
            }
        });

        var resp = await fetch("/api/offer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sdp: pc.localDescription.sdp,
                type: pc.localDescription.type,
                request_data: { name: name },
            }),
        });

        if (!resp.ok) throw new Error("Failed to connect to bot");

        var answer = await resp.json();
        await pc.setRemoteDescription(new RTCSessionDescription(answer));

        showScreen("game-screen");
        setBotStatus("connecting", "Connecting...");
    } catch (e) {
        showScreen("start-screen");
        showError(e.message || "Failed to connect");
        if (pc) { pc.close(); pc = null; }
    } finally {
        isConnecting = false;
        btn.disabled = false;
        btn.textContent = "Start Game";
    }
}

function leaveGame() {
    if (audioEl) {
        audioEl.pause();
        audioEl.srcObject = null;
        audioEl = null;
    }
    if (pc) {
        pc.close();
        pc = null;
    }
    handleGameEnd();
}

function handleGameEnd() {
    setBotStatus("ended", "Game ended");
    document.getElementById("final-score").textContent = gameState.score;
    document.getElementById("final-correct").textContent = gameState.correct_count;
    document.getElementById("final-total").textContent = gameState.total_words;
    showScreen("end-screen");
}

function resetGame() {
    gameState = { score: 0, correct_count: 0, incorrect_count: 0, total_words: 0 };
    updateUI();
    document.getElementById("player-name").value = "";
    showScreen("start-screen");
}

document.getElementById("player-name").addEventListener("keydown", function (e) {
    if (e.key === "Enter") startGame();
});
