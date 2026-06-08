document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const registerForm = document.getElementById("register-form");
  const loginForm = document.getElementById("login-form");
  const messageDiv = document.getElementById("message");
  const currentUserPanel = document.getElementById("current-user");
  const currentUserEmail = document.getElementById("current-user-email");
  const currentUserRole = document.getElementById("current-user-role");
  const signupHint = document.getElementById("signup-hint");

  const state = {
    token: localStorage.getItem("authToken") || "",
    user: null,
  };

  function showMessage(text, type = "success") {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function apiRequest(url, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (state.token) {
      headers.Authorization = `Bearer ${state.token}`;
    }

    return fetch(url, {
      ...options,
      headers,
    });
  }

  function updateAuthUI() {
    if (state.user) {
      currentUserEmail.textContent = state.user.email;
      currentUserRole.textContent = state.user.role;
      currentUserPanel.classList.remove("hidden");
    } else {
      currentUserPanel.classList.add("hidden");
    }

    signupHint.textContent = state.user
      ? "Signed-in student accounts can sign up and unregister themselves."
      : "Log in as a student to sign up or unregister.";
  }

  async function restoreSession() {
    if (!state.token) {
      updateAuthUI();
      return;
    }

    try {
      const response = await apiRequest("/auth/me");
      if (!response.ok) {
        localStorage.removeItem("authToken");
        state.token = "";
        state.user = null;
      } else {
        state.user = await response.json();
      }
    } catch (error) {
      console.error("Failed to restore session:", error);
      state.user = null;
    }

    updateAuthUI();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map((email) => {
                    const canUnregister =
                      state.user &&
                      state.user.role === "student" &&
                      state.user.email === email;

                    const actionButton = canUnregister
                      ? `<button class="delete-btn" data-activity="${name}" title="Unregister yourself">❌</button>`
                      : "";

                    return `<li><span class="participant-email">${email}</span>${actionButton}</li>`;
                  })
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");

    try {
      const response = await apiRequest(
        `/activities/${encodeURIComponent(activity)}/unregister`,
        { method: "DELETE" }
      );
      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "An error occurred", "error");
        return;
      }

      showMessage(result.message, "success");
      fetchActivities();
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      email: document.getElementById("register-email").value,
      password: document.getElementById("register-password").value,
      role: document.getElementById("register-role").value,
    };

    try {
      const response = await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "Registration failed", "error");
        return;
      }

      registerForm.reset();
      showMessage("Registration successful. Please log in.", "success");
    } catch (error) {
      showMessage("Failed to register. Please try again.", "error");
      console.error("Error registering:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      email: document.getElementById("login-email").value,
      password: document.getElementById("login-password").value,
    };

    try {
      const response = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "Login failed", "error");
        return;
      }

      state.token = result.access_token;
      state.user = result.user;
      localStorage.setItem("authToken", state.token);
      loginForm.reset();
      updateAuthUI();
      fetchActivities();
      showMessage(result.message, "success");
    } catch (error) {
      showMessage("Failed to login. Please try again.", "error");
      console.error("Error logging in:", error);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = document.getElementById("activity").value;

    try {
      const response = await apiRequest(
        `/activities/${encodeURIComponent(activity)}/signup`,
        { method: "POST" }
      );
      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "An error occurred", "error");
        return;
      }

      signupForm.reset();
      showMessage(result.message, "success");
      fetchActivities();
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  restoreSession().then(fetchActivities);
});
