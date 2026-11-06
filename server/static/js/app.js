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
  return "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.textContent = theme === "light" ? "Dark mode" : "Light mode";
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

function applySessionUser(user) {
  const userWrap = document.getElementById("topbar-user");
  const institutionEl = document.getElementById("topbar-institution");
  const metaEl = document.getElementById("topbar-user-meta");
  const logoutBtn = document.getElementById("logout-btn");

  if (userWrap) {
    userWrap.style.display = "flex";
  }
  if (institutionEl) {
    institutionEl.textContent = user.institution_name || "";
  }
  if (metaEl) {
    metaEl.textContent = [user.email, user.role].filter(Boolean).join(" · ");
  }
  if (logoutBtn) {
    logoutBtn.style.display = "inline-flex";
  }

  document.querySelectorAll(".admin-only").forEach((el) => {
    el.style.display = user.role === "admin" ? "" : "none";
  });
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
  const path = window.location.pathname;

  if (!token) {
    if (path === "/dashboard") {
      window.location.href = "/login";
    }
    return;
  }

  const user = await apiSession();
  if (!user) {
    clearToken();
    window.location.href = "/login";
    return;
  }

  applySessionUser(user);

  if (path === "/login" || path === "/register") {
    window.location.href = "/dashboard";
    return;
  }

  if (path === "/dashboard") {
    const instRes = await apiGet("/api/institution", token);
    const currency = instRes.data && instRes.data.currency ? instRes.data.currency : "";
    const data = await apiDashboard();
    if (data) {
      renderDashboardData(data, user, currency);
    }
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

function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function formatNumber(value, digits) {
  if (value == null) {
    return "—";
  }
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits == null ? 0 : digits,
    maximumFractionDigits: digits == null ? 0 : digits,
  });
}

function formatCurrency(value, currency) {
  if (value == null) {
    return "—";
  }
  const sym = currency === "KES" ? "KSh " : currency === "USD" ? "$" : currency ? currency + " " : "";
  return sym + Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function chartColors() {
  const styles = getComputedStyle(document.documentElement);
  return {
    grid: styles.getPropertyValue("--color-border").trim() || "#e3e8ef",
    text: styles.getPropertyValue("--color-text-muted").trim() || "#6b7a8d",
  };
}

let dashboardChart = null;

function renderComparisonTable(container, comparisons, currency) {
  if (!container) {
    return;
  }
  if (!comparisons || comparisons.length === 0) {
    container.innerHTML = '<p class="muted">No building data yet.</p>';
    return;
  }
  const rows = comparisons
    .map((c) => {
      const eui = c.eui == null ? "—" : Number(c.eui).toFixed(2);
      const note = c.eui_note || "insufficient";
      return `
        <tr>
          <td>${escapeHtml(c.name)}</td>
          <td>${escapeHtml(c.type)}</td>
          <td>${formatNumber(c.total_kwh, 1)}</td>
          <td>${formatCurrency(c.total_cost, currency)}</td>
          <td>${eui}</td>
          <td><span class="badge badge-${escapeHtml(note)}">${escapeHtml(note)}</span></td>
        </tr>`;
    })
    .join("");
  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr><th>Building</th><th>Type</th><th>Total kWh</th><th>Total cost</th><th>EUI</th><th>Data</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderDashboardData(data, user, currency) {
  const updated = document.getElementById("updated-at");
  if (updated) {
    updated.textContent = new Date().toLocaleDateString();
  }

  const subtitle = document.getElementById("page-subtitle");
  if (subtitle && user.institution_name) {
    subtitle.textContent = user.institution_name + " · " + user.email;
  }

  const kwhEl = document.getElementById("stat-kwh");
  const costEl = document.getElementById("stat-cost");
  const buildingsEl = document.getElementById("stat-buildings");
  const anomaliesEl = document.getElementById("stat-anomalies");

  if (kwhEl) {
    kwhEl.textContent = formatNumber(data.total_kwh || 0, 1) + " kWh";
  }
  if (costEl) {
    costEl.textContent = formatCurrency(data.total_cost || 0, currency);
  }
  if (buildingsEl) {
    buildingsEl.textContent = String(data.building_count || 0);
  }

  const anomalies = data.anomalies || [];
  if (anomaliesEl) {
    anomaliesEl.textContent = String(anomalies.length);
  }

  const namesById = {};
  (data.comparisons || []).forEach((comparison) => {
    namesById[comparison.building_id] = comparison.name;
  });

  const anomalyList = document.getElementById("anomaly-list");
  if (anomalyList) {
    if (anomalies.length === 0) {
      anomalyList.innerHTML = '<p class="muted">No anomalies detected.</p>';
    } else {
      anomalyList.innerHTML = anomalies
        .map((anomaly) => {
          const label = [anomaly.month, namesById[anomaly.building_id]].filter(Boolean).join(" · ");
          return (
            '<div class="anomaly-row"><span class="anomaly-month">' +
            escapeHtml(label) +
            '</span><span class="anomaly-value">+' +
            Number(anomaly.percent_above || 0).toFixed(0) +
            "%</span></div>"
          );
        })
        .join("");
    }
  }

  renderComparisonTable(document.getElementById("dashboard-buildings"), data.comparisons || [], currency);

  const series = data.monthly_series || [];
  const ctx = document.getElementById("consumptionChart");
  const emptyEl = document.getElementById("chart-empty");
  if (emptyEl) {
    emptyEl.style.display = series.length ? "none" : "block";
  }

  if (dashboardChart) {
    dashboardChart.destroy();
    dashboardChart = null;
  }

  if (ctx && series.length) {
    const colors = chartColors();
    dashboardChart = new Chart(ctx, {
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
          y: { beginAtZero: true, grid: { color: colors.grid }, ticks: { color: colors.text } },
          x: { grid: { display: false }, ticks: { color: colors.text } },
        },
      },
    });
  }
}
