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

async function apiGet(url, token) {
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(url, {
    method: "GET",
    headers,
  });
  const body = await response.json().catch(() => ({}));
  return { response, body };
}

async function apiSession() {
  const token = getToken();
  const { response, body } = await apiGet("/api/auth/session", token);
  if (!response.ok) {
    return null;
  }
  const user = body.data && body.data.user ? body.data.user : null;
  return user;
}

async function apiDashboard() {
  const token = getToken();
  const { response, body } = await apiGet("/api/dashboard", token);
  if (!response.ok) {
    return null;
  }
  return body.data ? body.data : null;
}

function renderDashboard(user) {
  const mount = document.getElementById("dashboard-root");
  if (!mount) {
    return;
  }
  const institutionName = user && user.institution_name ? user.institution_name : "your institution";
  mount.innerHTML = `
    <section class="card">
      <h1 class="page-title">Dashboard</h1>
      <p class="page-subtitle">Welcome to the ${institutionName} workspace.</p>
      <p class="muted">Signed in as ${user ? user.email : ""} (${user ? user.role : ""}).</p>
    </section>
  `;
}

async function postJson(url, payload, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  return { response, body };
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

document.addEventListener("DOMContentLoaded", async () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", apiLogout);
  }

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      hideFormError();
      const payload = {
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
      };
      const { response, body } = await postJson("/api/auth/login", payload);
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

  const token = getToken();
  if (token) {
    const user = await apiSession();
    if (user) {
      const path = window.location.pathname;
      if (path === "/login" || path === "/register") {
        window.location.href = "/dashboard";
      } else if (path === "/dashboard") {
        await apiDashboard();
        renderDashboard(user);
      }
    } else {
      clearToken();
      window.location.href = "/login";
    }
  } else if (window.location.pathname === "/dashboard") {
    window.location.href = "/login";
  }
});
