const el = id => document.getElementById(id);

const tabLogin = el("tab-login");
const tabRegister = el("tab-register");
const loginForm = el("login-form");
const registerForm = el("register-form");
const loginError = el("login-error");
const registerError = el("register-error");
const strengthHint = el("strength-hint");

function showTab(which) {
    const isLogin = which === "login";
    loginForm.hidden = !isLogin;
    registerForm.hidden = isLogin;
    tabLogin.classList.toggle("active", isLogin);
    tabRegister.classList.toggle("active", !isLogin);
    tabLogin.setAttribute("aria-selected", String(isLogin));
    tabRegister.setAttribute("aria-selected", String(!isLogin));
    loginError.textContent = "";
    registerError.textContent = "";
}
tabLogin.addEventListener("click", () => showTab("login"));
tabRegister.addEventListener("click", () => showTab("register"));

// If already signed in, skip straight to the analyzer.
fetch("/api/me").then(res => {
    if (res.ok) window.location.href = "index.html";
});

loginForm.addEventListener("submit", async e => {
    e.preventDefault();
    loginError.textContent = "";
    const submitBtn = el("login-submit");
    submitBtn.disabled = true;
    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: el("login-username").value,
                password: el("login-password").value,
            }),
        });
        const data = await res.json();
        if (res.ok) {
            window.location.href = "index.html";
            return;
        }
        loginError.classList.remove("success");
        if (res.status === 429) {
            loginError.textContent = `${data.error} — try again in ${data.retry_after_seconds}s.`;
        } else {
            loginError.textContent = data.error || "Login failed.";
        }
    } catch (err) {
        loginError.textContent = "Could not reach the server.";
    } finally {
        submitBtn.disabled = false;
    }
});

registerForm.addEventListener("submit", async e => {
    e.preventDefault();
    registerError.textContent = "";
    const submitBtn = el("register-submit");
    submitBtn.disabled = true;
    const username = el("register-username").value;
    try {
        const res = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password: el("register-password").value }),
        });
        const data = await res.json();
        if (res.ok) {
            showTab("login");
            el("login-username").value = username;
            loginError.textContent = "Account created — log in below.";
            loginError.classList.add("success");
        } else {
            registerError.textContent = data.error || "Registration failed.";
        }
    } catch (err) {
        registerError.textContent = "Could not reach the server.";
    } finally {
        submitBtn.disabled = false;
    }
});

// Live strength hint while registering, via the same server-side scorer
// used to enforce the minimum at registration time.
let strengthTimer;
el("register-password").addEventListener("input", () => {
    clearTimeout(strengthTimer);
    const value = el("register-password").value;
    if (!value) { strengthHint.textContent = ""; return; }
    strengthTimer = setTimeout(async () => {
        try {
            const res = await fetch("/api/check-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password: value }),
            });
            const data = await res.json();
            // Drop the result if the user has typed again while it was in flight.
            if (value !== el("register-password").value) return;
            strengthHint.textContent = data.rating;
        } catch (err) {
            strengthHint.textContent = "";
        }
    }, 300);
});
