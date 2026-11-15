
const pages = document.querySelectorAll(".page");
const logoutBtn = document.getElementById("logoutBtn");

let currentUser = null;
let documents = [];

function showPage(pageId) {
    pages.forEach(page => page.classList.remove("active"));

    const selectedPage = document.getElementById(pageId);
    if (selectedPage) {
        selectedPage.classList.add("active");
    }

    logoutBtn.hidden = !currentUser;
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// Navigation buttons
document.querySelectorAll("[data-page]").forEach(button => {
    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });
});

// Login demo
document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const role = document.getElementById("loginRole").value;

    if (!email || !password) {
        showMessage("loginMessage", "Please enter your email and password.", "error");
        return;
    }

    currentUser = {
        name: email.split("@")[0],
        email: email,
        role: role,
        language: document.getElementById("languageSelect").value === "te"
            ? "Telugu" : "English"
    };

    updateDashboard();
    showPage("dashboardPage");
});

// Registration demo
document.getElementById("registerForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const name = document.getElementById("fullName").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const phone = document.getElementById("registerPhone").value.trim();
    const password = document.getElementById("registerPassword").value;

    if (!name || !email || !phone || password.length < 6) {
        showMessage("registerMessage", "Please complete all fields correctly.", "error");
        return;
    }

    currentUser = {
        name: name,
        email: email,
        role: document.getElementById("registerRole").value,
        language: document.getElementById("registerLanguage").value
    };

    updateDashboard();
    showPage("dashboardPage");

    document.getElementById("registerForm").reset();
});

// Dashboard details
function updateDashboard() {
    if (!currentUser) return;

    document.getElementById("dashboardWelcome").textContent =
        "Welcome, " + currentUser.name;

    document.getElementById("profileName").textContent = currentUser.name;
    document.getElementById("profileEmail").textContent = currentUser.email;
    document.getElementById("profileRole").textContent = currentUser.role;
    document.getElementById("profileLanguage").textContent = currentUser.language;

    document.getElementById("profileAvatar").textContent =
        currentUser.name.charAt(0).toUpperCase();

    updateDocumentCount();
}

// Upload document demo
document.getElementById("uploadForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const category = document.getElementById("documentType").value;
    const fileInput = document.getElementById("documentFile");
    const file = fileInput.files[0];

    if (!category || !file) {
        showMessage("uploadMessage", "Please select a document category and file.", "error");
        return;
    }

    const allowedExtensions = /\.(pdf|png|jpg|jpeg|doc|docx)$/i;

    if (!allowedExtensions.test(file.name)) {
        showMessage("uploadMessage", "Please choose a supported document format.", "error");
        return;
    }

    documents.push({
        id: Date.now(),
        name: file.name,
        category: category,
        size: formatFileSize(file.size),
        date: new Date().toLocaleDateString()
    });

    renderDocuments();
    updateDocumentCount();

    showMessage("uploadMessage", "Document added to this demo session successfully!", "success");

    this.reset();
});

// Display uploaded document names
function renderDocuments() {
    const list = document.getElementById("documentsList");

    if (documents.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">▤</div>
                <h3>No documents added yet</h3>
                <p>Your uploaded document names will appear here.</p>
            </div>`;
        return;
    }

    list.innerHTML = "";

    documents.forEach(document => {
        const item = document.createElement("div");
        item.className = "document-item";

        const details = document.createElement("div");

        const category = document.createElement("div");
        category.className = "document-category";
        category.textContent = document.category;

        const name = document.createElement("p");
        name.textContent = document.name;

        const meta = document.createElement("p");
        meta.textContent = `${document.size} • Added ${document.date}`;

        details.append(category, name, meta);

        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-btn";
        deleteButton.textContent = "Remove";
        deleteButton.setAttribute("aria-label", "Remove " + document.name);

        deleteButton.addEventListener("click", () => {
            documents = documents.filter(doc => doc.id !== document.id);
            renderDocuments();
            updateDocumentCount();
        });

        item.append(details, deleteButton);
        list.appendChild(item);
    });
}

function updateDocumentCount() {
    document.getElementById("documentCount").textContent = documents.length;
    document.getElementById("documentCountLabel").textContent =
        documents.length + (documents.length === 1 ? " file" : " files");

    document.getElementById("recentActivity").textContent =
        documents.length === 0
            ? "No documents uploaded yet."
            : documents.length + " document(s) added in this session.";
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = "message " + type;
}

// Logout
logoutBtn.addEventListener("click", () => {
    currentUser = null;
    document.getElementById("loginForm").reset();
    showPage("loginPage");
});

// Language selection
const languageSelect = document.getElementById("languageSelect");

languageSelect.addEventListener("change", function() {
    const language = this.value;

    document.querySelectorAll("[data-en][data-te]").forEach(element => {
        element.textContent = element.dataset[language];
    });

    document.documentElement.lang = language === "te" ? "te" : "en";
});

// Initial state
updateDocumentCount();
showPage("loginPage");
