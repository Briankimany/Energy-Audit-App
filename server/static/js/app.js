const TOKEN_KEY = "energy_audit_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function storeToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiLogout() {
  const token = getToken();
  if (token) {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: "{}",
      });
    } catch (err) {
      // ignore network failures during logout
    }
  }
  clearToken();
  window.location.href = "/login";
}

function showFormError(message) {
  const errorEl = document.getElementById("form-error");
  if (!errorEl) {
    return;
  }
  errorEl.textContent = message || "Something went wrong.";
  errorEl.classList.remove("hidden");
}

function hideFormError() {
  const errorEl = document.getElementById("form-error");
  if (!errorEl) {
    return;
  }
  errorEl.textContent = "";
  errorEl.classList.add("hidden");
}

async function postJson(url, payload, authToken) {
  const headers = { "Content-Type": "application/json" };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  return { response, body };
}

document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", apiLogout);
  }

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      hideFormError();
      const token = getToken();
      const payload = {
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
      };
      const { response, body } = await postJson("/api/auth/login", payload, token);
      if (!response.ok) {
        showFormError(body.message || "Login failed");
        return;
      }
      storeToken(body.data.access_token);
      window.location.href = "/dashboard";
    });
  }

  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      hideFormError();
      const payload = {
        institution_name: document.getElementById("institution_name").value.trim(),
        admin_name: document.getElementById("admin_name").value.trim(),
        admin_email: document.getElementById("admin_email").value.trim(),
        password: document.getElementById("password").value,
      };
      const { response, body } = await postJson("/api/auth/register-institution", payload);
      if (!response.ok) {
        showFormError(body.message || "Registration failed");
        return;
      }
      storeToken(body.data.access_token);
      window.location.href = "/dashboard";
    });
  }
});
