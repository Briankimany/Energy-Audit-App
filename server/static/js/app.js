const TOKEN_KEY = "energy_audit_token";
const THEME_KEY = "energy_audit_theme";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function storeToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function getTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored) {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.textContent = theme === "light" ? "🌙" : "☀️";
  }
}

function toggleTheme() {
  applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
}

async function apiGet(url, token) {
  const headers = {};
  if (token) {
    headers.Authorization = "Bearer " + token;
  }
  const response = await fetch(url, { method: "GET", headers });
  const body = await response.json().catch(() => ({}));
  return { response, body };
}

async function apiSession() {
  const token = getToken();
  const { response, body } = await apiGet("/api/auth/session", token);
  if (!response.ok) {
    return null;
  }
  return body.data && body.data.user ? body.data.user : null;
}

async function apiLogout() {
  const token = getToken();
  if (token) {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token,
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

async function postJson(url, payload, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = "Bearer " + token;
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
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    applyTheme(getTheme());
    themeToggle.addEventListener("click", toggleTheme);
  }

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
        const data = await apiDashboard();
        if (data) {
          const instRes = await apiGet("/api/institution", token);
          const currency = instRes.data && instRes.data.currency ? instRes.data.currency : "";
          renderDashboardData(data, user, currency);
        }
      }
    } else {
      clearToken();
      window.location.href = "/login";
    }
  } else if (window.location.pathname === "/dashboard") {
    window.location.href = "/login";
  }
});

async function apiDashboard() {
  const token = getToken();
  const { response, body } = await apiGet("/api/dashboard", token);
  if (!response.ok) {
    return null;
  }
  return body.data ? body.data : null;
}

function formatCurrency(value, currency) {
  if (value == null) {
    return "—";
  }
  const sym = currency === "KES" ? "KES " : currency === "USD" ? "$" : currency + " ";
  return sym + Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderDashboardData(data, user, currency) {
  document.getElementById("updated-at").textContent = new Date().toLocaleDateString();

  const kwhEl = document.getElementById("stat-kwh");
  const costEl = document.getElementById("stat-cost");
  if (kwhEl) {
    kwhEl.textContent = ((data.total_kwh || 0) / 1).toLocaleString(undefined, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + " kWh";
  }
  if (costEl) {
    costEl.textContent = formatCurrency(data.total_cost || 0, currency);
  }

  const anomalies = data.anomalies || [];
  const anomalyList = document.getElementById("anomaly-list");
  if (anomalyList) {
    if (anomalies.length === 0) {
      anomalyList.innerHTML = "<p class=\"muted\">No anomalies detected.</p>";
    } else {
      anomalyList.innerHTML = anomalies
        .map(
          (a) =>
            "<div class=\"anomaly-row\"><span class=\"anomaly-month\">" +
            (a.month || "") +
            "</span><span class=\"anomaly-value\">+" +
            (a.percent_above || 0).toFixed(0) +
            "%</span></div>"
        )
        .join("");
    }
  }

  const series = data.monthly_series || [];
  const ctx = document.getElementById("consumptionChart");
  if (ctx && series.length) {
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: series.map((s) => s.month.slice(0, 7)),
        datasets: [
          {
            label: "kWh",
            data: series.map((s) => s.kwh),
            backgroundColor: "#168C83",
            borderWidth: 0,
            barPercentage: 0.6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: "#e3e8ef" }, ticks: { color: "#6b7a8d" } },
          x: { grid: { display: false }, ticks: { color: "#6b7a8d" } },
        },
      },
    });
  }
}
