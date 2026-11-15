
// ============================================
// CARECONNECT - FRONTEND + FASTAPI INTEGRATION
// ============================================

const API_BASE_URL = "http://127.0.0.1:8000";

const pages = document.querySelectorAll(".page");
const logoutBtn = document.getElementById("logoutBtn");

let currentUser = null;
let documents = [];

// ---------- PAGE NAVIGATION ----------

function showPage(pageId) {
    pages.forEach(page => page.classList.remove("active"));

    const selectedPage = document.getElementById(pageId);

    if (selectedPage) {
        selectedPage.classList.add("active");
    }

    logoutBtn.hidden = !currentUser;
    window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-page]").forEach(button => {
    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });
});

// ---------- MESSAGE DISPLAY ----------

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = "message " + type;
}

async function getErrorMessage(response) {
    try {
        const data = await response.json();

        if (typeof data.detail === "string") {
            return data.detail;
        }

        return "Request failed. Please check your details.";
    } catch {
        return "Unable to communicate with the server.";
    }
}

// ---------- REGISTRATION: REAL API ----------

document.getElementById("registerForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const name = document.getElementById("fullName").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const phone = document.getElementById("registerPhone").value.trim();
    const role = document.getElementById("registerRole").value;
    const language = document.getElementById("registerLanguage").value;
    const password = document.getElementById("registerPassword").value;

    const message = document.getElementById("registerMessage");
    message.textContent = "Creating your account...";
    message.className = "message";

    try {
        // Send registration information to FastAPI
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                full_name: name,
                email: email,
                phone: phone,
                password: password,
                role: role,
                preferred_language: language
            })
        });

        if (!response.ok) {
            const errorMessage = await getErrorMessage(response);
            showMessage("registerMessage", errorMessage, "error");
            return;
        }

        // Account successfully saved in PostgreSQL
        showMessage(
            "registerMessage",
            "Account created successfully! Logging you in...",
            "success"
        );

        // Automatically log in after successful registration
        await loginWithCredentials(email, password, "registerMessage");

        document.getElementById("registerForm").reset();

    } catch (error) {
        showMessage(
            "registerMessage",
            "Cannot connect to the backend. Check whether FastAPI is running.",
            "error"
        );

        console.error("Registration error:", error);
    }
});

// ---------- LOGIN: REAL API ----------

document.getElementById("loginForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const role = document.getElementById("loginRole").value;

    await loginWithCredentials(email, password, "loginMessage", role);
});

async function loginWithCredentials(email, password, messageId, selectedRole = null) {

    showMessage(messageId, "Checking your login details...", "");

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        if (!response.ok) {
            const errorMessage = await getErrorMessage(response);
            showMessage(messageId, errorMessage, "error");
            return;
        }

        const data = await response.json();

        // Check the selected login role
        if (selectedRole && data.user.role !== selectedRole) {
            showMessage(
                messageId,
                "The selected account type does not match this account.",
                "error"
            );
            return;
        }

        // Save the access token in this browser
       localStorage.setItem("careconnect_token", data.access_token);



        // Load the user's profile from FastAPI
        await loadUserProfile();

        showPage("dashboardPage");

    } catch (error) {
        showMessage(
            messageId,
            "Cannot connect to the backend. Check whether FastAPI is running.",
            "error"
        );

        console.error("Login error:", error);
    }
}

// ---------- LOAD USER PROFILE ----------


async function loadUserProfile() {

    const token = localStorage.getItem("careconnect_token");

    if (!token) {
        throw new Error("Login required.");
    }

    const response = await fetch(
        `${API_BASE_URL}/users/me`,
        {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        throw new Error("Unable to load the user profile.");
    }

    const user = await response.json();

    currentUser = {
        id: user.id,
        name: user.full_name,
        email: user.email,
        role: user.role,
        language: user.preferred_language
    };

    updateDashboard();
    await loadDocuments();
}


// ---------- UPDATE DASHBOARD ----------

function updateDashboard() {

    if (!currentUser) return;

    document.getElementById("dashboardWelcome").textContent =
        "Welcome, " + currentUser.name;

    document.getElementById("profileName").textContent =
        currentUser.name;

    document.getElementById("profileEmail").textContent =
        currentUser.email;

    document.getElementById("profileRole").textContent =
        currentUser.role;

    document.getElementById("profileLanguage").textContent =
        currentUser.language;

    document.getElementById("profileAvatar").textContent =
        currentUser.name.charAt(0).toUpperCase();

    updateDocumentCount();
}

// ---------- DOCUMENT DEMO (SERVER UPLOAD NEXT STEP) ----------


// ---------- SECURE DOCUMENT MANAGEMENT ----------

async function loadDocuments() {

    const token = localStorage.getItem("careconnect_token");

    if (!token) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/documents`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (response.status === 401) {
            localStorage.removeItem("careconnect_token");
            currentUser = null;
            showPage("loginPage");
            return;
        }

        if (!response.ok) {
            throw new Error("Unable to retrieve documents.");
        }

        const data = await response.json();

        documents = data.map(doc => ({
            id: doc.id,
            name: doc.document_name,
            category: doc.document_type,
            size: "Stored on server",
            date: new Date(doc.uploaded_at).toLocaleDateString()
        }));

        renderDocuments();
        updateDocumentCount();

    } catch (error) {
        console.error("Document loading error:", error);

        showMessage(
            "uploadMessage",
            "Unable to load your documents. Please try again.",
            "error"
        );
    }
}


// Upload a document to the backend
document.getElementById("uploadForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const category =
            document.getElementById("documentType").value;

        const fileInput =
            document.getElementById("documentFile");

        const file = fileInput.files[0];

        if (!category || !file) {
            showMessage(
                "uploadMessage",
                "Please select a document category and file.",
                "error"
            );
            return;
        }

        const allowedExtensions = /\.(pdf|png|jpg|jpeg)$/i;

        if (!allowedExtensions.test(file.name)) {
            showMessage(
                "uploadMessage",
                "Only PDF, JPG, JPEG and PNG files are allowed.",
                "error"
            );
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            showMessage(
                "uploadMessage",
                "File size must not exceed 5 MB.",
                "error"
            );
            return;
        }

        const token =
            localStorage.getItem("careconnect_token");

        if (!token) {
            showMessage(
                "uploadMessage",
                "Please log in before uploading a document.",
                "error"
            );
            return;
        }

        const formData = new FormData();

        formData.append("document_type", category);
        formData.append("file", file);

        showMessage(
            "uploadMessage",
            "Uploading your document...",
            ""
        );

        try {

            const response = await fetch(
                `${API_BASE_URL}/documents/upload`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`
                    },
                    body: formData
                }
            );

            if (!response.ok) {
                const errorMessage =
                    await getErrorMessage(response);

                showMessage(
                    "uploadMessage",
                    errorMessage,
                    "error"
                );

                return;
            }

            showMessage(
                "uploadMessage",
                "Document uploaded successfully!",
                "success"
            );

            this.reset();

            await loadDocuments();

        } catch (error) {

            console.error("Upload error:", error);

            showMessage(
                "uploadMessage",
                "Unable to connect to the server.",
                "error"
            );
        }
    }
);


// Display documents retrieved from PostgreSQL
function renderDocuments() {

    const list =
        document.getElementById("documentsList");

    if (documents.length === 0) {

        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">▤</div>
                <h3>No documents uploaded yet</h3>
                <p>Your uploaded documents will appear here.</p>
            </div>`;

        return;
    }

    list.innerHTML = "";

    documents.forEach(doc => {

        const item = document.createElement("div");
        item.className = "document-item";

        const details = document.createElement("div");

        const category = document.createElement("div");
        category.className = "document-category";
        category.textContent = doc.category;

        const name = document.createElement("p");
        name.textContent = doc.name;

        const meta = document.createElement("p");
        meta.textContent =
            `${doc.size} • Added ${doc.date}`;

        details.append(category, name, meta);

        const deleteButton =
            document.createElement("button");

        deleteButton.className = "delete-btn";
        deleteButton.textContent = "Remove";

        deleteButton.setAttribute(
            "aria-label",
            "Remove " + doc.name
        );

        deleteButton.addEventListener("click", async () => {

            await deleteDocument(doc.id);

        });

        item.append(details, deleteButton);
        list.appendChild(item);
    });
}


// Delete a document from the backend
async function deleteDocument(documentId) {

    const token =
        localStorage.getItem("careconnect_token");

    if (!token) {
        return;
    }

    try {

        const response = await fetch(
            `${API_BASE_URL}/documents/${documentId}`,
            {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            const errorMessage =
                await getErrorMessage(response);

            showMessage(
                "uploadMessage",
                errorMessage,
                "error"
            );

            return;
        }

        showMessage(
            "uploadMessage",
            "Document deleted successfully.",
            "success"
        );

        await loadDocuments();

    } catch (error) {

        console.error("Delete error:", error);

        showMessage(
            "uploadMessage",
            "Unable to delete the document.",
            "error"
        );
    }
}

function updateDocumentCount() {

    document.getElementById("documentCount").textContent =
        documents.length;

    document.getElementById("documentCountLabel").textContent =
        documents.length +
        (documents.length === 1 ? " file" : " files");

    document.getElementById("recentActivity").textContent =
        documents.length === 0
            ? "No documents uploaded yet."
            : documents.length +
              " document(s) added in this session.";
}

function formatFileSize(bytes) {

    if (bytes < 1024) return bytes + " B";

    if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(1) + " KB";
    }

    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// ---------- LOGOUT ----------

logoutBtn.addEventListener("click", () => {

    localStorage.removeItem("careconnect_token");
    localStorage.removeItem("careconnect_user_id");

    currentUser = null;
    documents = [];

    document.getElementById("loginForm").reset();

    updateDocumentCount();
    showPage("loginPage");
});

// ---------- LANGUAGE SELECTION ----------

const languageSelect = document.getElementById("languageSelect");

languageSelect.addEventListener("change", function() {

    const language = this.value;

    document.querySelectorAll("[data-en][data-te]").forEach(element => {
        element.textContent = element.dataset[language];
    });

    document.documentElement.lang =
        language === "te" ? "te" : "en";
});

// ---------- INITIAL PAGE ----------

updateDocumentCount();
showPage("loginPage");
