const statusText = document.getElementById("statusText");
const initBtn = document.getElementById("initBtn");
const sendBtn = document.getElementById("sendBtn");
const modelSelect = document.getElementById("model");
const skillsList = document.getElementById("skillsList");
const messages = document.getElementById("messages");
const input = document.getElementById("input");
const modelText = document.getElementById("modelText");
const loadedSkills = document.getElementById("loadedSkills");
const toolCalls = document.getElementById("toolCalls");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const uploadList = document.getElementById("uploadList");

const uploadedFiles = [];

function loadLocalConfig() {
    modelSelect.value = localStorage.getItem("ss2_openai_model") || "gpt-4o-mini";
}

function saveLocalConfig() {
    localStorage.setItem("ss2_openai_model", modelSelect.value);
}

function appendMessage(role, text) {
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

// 渲染上传文件列表，并支持点击插入路径
function renderUploadList() {
    if (!uploadedFiles.length) {
        uploadList.classList.add("empty");
        uploadList.textContent = "暂无上传文件";
        return;
    }

    uploadList.classList.remove("empty");
    uploadList.innerHTML = uploadedFiles.map(item => (
        `<span class="tag file-tag" data-path="${item.path}" title="点击插入路径">${item.name}</span>`
    )).join("");
}

// 将文件路径插入到输入框
function insertFilePath(path) {
    const text = input.value.trim();
    input.value = text ? `${text} ${path}` : path;
    input.focus();
}

// 上传文件到后端并更新列表
async function uploadFile() {
    const file = fileInput.files[0];
    if (!file) {
        uploadStatus.textContent = "请选择文件后再上传";
        return;
    }

    uploadStatus.textContent = "上传中...";
    uploadBtn.disabled = true;

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        const data = await res.json();
        uploadStatus.textContent = data.detail || "上传失败";
        uploadBtn.disabled = false;
        return;
    }

    const data = await res.json();
    if (data.file) {
        uploadedFiles.unshift(data.file);
        renderUploadList();
        uploadStatus.textContent = `已上传: ${data.file.name}`;
        appendMessage("system", `已上传文件: ${data.file.path}`);
        fileInput.value = "";
    } else {
        uploadStatus.textContent = "上传成功";
    }
    uploadBtn.disabled = false;
}

async function initAgent() {
    saveLocalConfig();
    statusText.textContent = "初始化中...";
    initBtn.disabled = true;

    const res = await fetch("/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            model: modelSelect.value
        })
    });

    if (!res.ok) {
        const data = await res.json();
        appendMessage("system", data.error || "初始化失败");
        statusText.textContent = "未初始化";
        initBtn.disabled = false;
        return;
    }

    const data = await res.json();
    statusText.textContent = "已就绪";
    sendBtn.disabled = false;
    modelText.textContent = data.model || "-";

    if (data.skills && data.skills.length > 0) {
        skillsList.innerHTML = data.skills.map(s => `<span class="tag">${s}</span>`).join("");
    } else {
        skillsList.textContent = "未发现技能";
    }
    appendMessage("system", `已加载 ${data.skills.length} 个技能。`);
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    appendMessage("user", text);
    input.value = "";
    sendBtn.disabled = true;

    const res = await fetch("/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });

    if (!res.ok) {
        const data = await res.json();
        appendMessage("system", data.error || "请求失败");
        sendBtn.disabled = false;
        return;
    }

    const data = await res.json();
    appendMessage("assistant", data.response || "(empty response)");
    loadedSkills.textContent = data.skills_loaded && data.skills_loaded.length
        ? data.skills_loaded.join(", ")
        : "-";
    toolCalls.textContent = data.tool_calls && data.tool_calls.length
        ? data.tool_calls.map(t => t.name).join(", ")
        : "-";
    sendBtn.disabled = false;
}

initBtn.addEventListener("click", initAgent);
sendBtn.addEventListener("click", sendMessage);
// 上传按钮与列表点击事件绑定
uploadBtn.addEventListener("click", uploadFile);
uploadList.addEventListener("click", (e) => {
    const target = e.target;
    if (target.classList.contains("file-tag")) {
        insertFilePath(target.dataset.path);
    }
});
input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

loadLocalConfig();
