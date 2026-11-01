const el = id => document.getElementById(id);
const password = el("password");
const fill = el("fill");
const track = document.querySelector(".track");
const verdict = el("verdict");
const verdictSub = el("verdict-sub");
const entropyOut = el("entropy");
const crackOut = el("crack");
const lenCount = el("len-count");
const tips = el("tips");
const issuesRow = el("issues-row");
const breachRow = el("breach-row");
const breachOut = el("breach");
const capsWarning = el("capslock-warning");
const toast = el("toast");

const reqs = {
    length: el("r-length"),
    lower: el("r-lower"),
    upper: el("r-upper"),
    number: el("r-number"),
    special: el("r-special"),
    nopattern: el("r-nopattern"),
};

const scale = [
    { max: 28,  label: "Very Weak",   color: "var(--red)",    w: "18%",  pct: 18,  sub: "Cracked almost instantly" },
    { max: 40,  label: "Weak",        color: "var(--orange)", w: "38%",  pct: 38,  sub: "Vulnerable to fast attacks" },
    { max: 60,  label: "Fair",        color: "var(--yellow)", w: "58%",  pct: 58,  sub: "Okay, but improvable" },
    { max: 80,  label: "Strong",      color: "var(--lime)",   w: "80%",  pct: 80,  sub: "Solid protection" },
    { max: 1e9, label: "Very Strong", color: "var(--green)",  w: "100%", pct: 100, sub: "Excellent — attacker's nightmare" },
];

const commonPasswords = new Set([
    "password","123456","12345678","123456789","qwerty","abc123","111111",
    "123123","admin","letmein","welcome","monkey","dragon","iloveyou",
    "password1","qwerty123","1q2w3e4r","sunshine","princess","football",
    "000000","1234567","12345","qazwsx","trustno1",
    "master","passw0rd","login","starwars","superman","batman"
]);
const sequences = ["abcdefghijklmnopqrstuvwxyz", "01234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"];

function charPool(v) {
    let pool = 0;
    if (/[a-z]/.test(v)) pool += 26;
    if (/[A-Z]/.test(v)) pool += 26;
    if (/[0-9]/.test(v)) pool += 10;
    if (/[^a-zA-Z0-9]/.test(v)) pool += 33;
    return pool;
}

function detectPatterns(v) {
    const issues = [];
    const critical = [];
    const lower = v.toLowerCase();
    if (v.length > 0) {
        if (commonPasswords.has(lower)) {
            issues.push("common password");
            critical.push("common password");
        } else {
            for (const cp of commonPasswords) {
                if (cp.length >= 5 && lower.includes(cp)) {
                    issues.push("contains a common password");
                    critical.push("contains a common password");
                    break;
                }
            }
        }
    }
    if (/(.)\1{2,}/.test(v)) issues.push("repeated characters");
    for (const seq of sequences) {
        for (let i = 0; i < seq.length - 2; i++) {
            const chunk = seq.substring(i, i + 3);
            if (lower.includes(chunk) || lower.includes([...chunk].reverse().join(""))) {
                issues.push("keyboard/alphabet sequence");
                break;
            }
        }
        if (issues.includes("keyboard/alphabet sequence")) break;
    }
    if (/^\d+$/.test(v) && v.length > 0) issues.push("digits only");
    if (/^[a-zA-Z]+$/.test(v) && v.length > 0) issues.push("letters only");
    if (/(19|20)\d{2}/.test(v)) issues.push("looks like a year");
    return { issues: [...new Set(issues)], critical: critical.length > 0 };
}

function entropyBits(v) {
    if (!v) return 0;
    const pool = charPool(v);
    if (pool === 0) return 0;
    let bits = v.length * Math.log2(pool);
    const { issues, critical } = detectPatterns(v);
    bits = Math.max(0, bits - issues.length * 12);
    if (critical) bits = Math.min(bits, 24);
    return Math.round(bits);
}

function crackTime(bits) {
    const guessesPerSec = 1e11;
    const seconds = Math.pow(2, bits) / 2 / guessesPerSec;
    if (seconds < 0.001) return "Instantly";
    const units = [
        [1, "second"], [60, "minute"], [60, "hour"], [24, "day"],
        [30, "month"], [12, "year"], [100, "century"], [10, "millennium"]
    ];
    let t = seconds, i = 0, name = "second";
    for (; i < units.length; i++) {
        if (t < units[i][0]) break;
        t /= units[i][0];
        name = units[i][1];
    }
    if (name === "second" && t < 1) return "Instantly";
    const rounded = t >= 100 ? Math.round(t) : Math.round(t * 10) / 10;
    if (rounded > 1000 && name === "millennium") return "Effectively forever";
    return rounded.toLocaleString() + " " + name + (rounded !== 1 ? "s" : "");
}

function analyze() {
    const v = password.value;
    lenCount.textContent = v.length + " char" + (v.length !== 1 ? "s" : "");

    const results = {
        length: v.length >= 12,
        lower: /[a-z]/.test(v),
        upper: /[A-Z]/.test(v),
        number: /[0-9]/.test(v),
        special: /[^a-zA-Z0-9]/.test(v),
        nopattern: v.length > 0 && detectPatterns(v).issues.length === 0,
    };
    for (const k in reqs) {
        const met = results[k];
        reqs[k].classList.toggle("met", met);
        reqs[k].querySelector(".mark").textContent = met ? "✓" : "—";
    }

    const bits = entropyBits(v);
    entropyOut.textContent = bits;

    if (!v) {
        fill.style.width = "2%";
        fill.style.background = "var(--red)";
        verdict.firstChild.textContent = "—";
        verdict.style.color = "var(--ink)";
        verdictSub.textContent = "Awaiting input";
        crackOut.textContent = "—";
        issuesRow.style.display = "none";
        breachRow.style.display = "none";
        track.setAttribute("aria-valuenow", "0");
        return;
    }

    const tier = scale.find(s => bits < s.max);
    fill.style.width = tier.w;
    fill.style.background = tier.color;
    verdict.firstChild.textContent = tier.label;
    verdict.style.color = tier.color;
    verdictSub.textContent = tier.sub;
    crackOut.textContent = crackTime(bits);
    track.setAttribute("aria-valuenow", String(tier.pct));

    const { issues } = detectPatterns(v);
    if (issues.length) {
        issuesRow.style.display = "flex";
        tips.innerHTML = issues.map(i => '<span class="tip">' + i + '</span>').join("");
    } else {
        issuesRow.style.display = "none";
    }
}

password.addEventListener("input", analyze);
password.closest("form").addEventListener("submit", e => e.preventDefault());

// Show / hide password
el("toggle").addEventListener("click", () => {
    const hidden = password.type === "password";
    password.type = hidden ? "text" : "password";
    el("toggle").setAttribute("aria-label", hidden ? "Hide password" : "Show password");
});

// Caps Lock warning
function updateCapsWarning(e) {
    const on = typeof e.getModifierState === "function" && e.getModifierState("CapsLock");
    capsWarning.hidden = !on;
}
password.addEventListener("keydown", updateCapsWarning);
password.addEventListener("keyup", updateCapsWarning);
password.addEventListener("blur", () => { capsWarning.hidden = true; });

// Cryptographically secure random helpers
function randomInt(maxExclusive) {
    const range = 256 - (256 % maxExclusive);
    const buf = new Uint8Array(1);
    let x;
    do { crypto.getRandomValues(buf); x = buf[0]; } while (x >= range);
    return x % maxExclusive;
}
function randomItem(arr) { return arr[randomInt(arr.length)]; }

let toastTimer;
function showToast(msg) {
    clearTimeout(toastTimer);
    toast.textContent = msg;
    toast.hidden = false;
    requestAnimationFrame(() => toast.classList.add("show"));
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => { toast.hidden = true; }, 300);
    }, 2200);
}

// Generate a strong, memorable passphrase and copy it to the clipboard
el("generate").addEventListener("click", async () => {
    const words = ["river","copper","lunar","ember","cactus","violet","harbor","quartz","meadow","cipher","falcon","onyx","cobalt","zephyr","willow","garnet"];
    const cap = w => w[0].toUpperCase() + w.slice(1);
    const symbol = randomItem([..."!@#$%^&*?"]);
    const num = randomInt(90) + 10;
    const pw = cap(randomItem(words)) + "-" + randomItem(words) + "-" + symbol + num + cap(randomItem(words));
    password.type = "text";
    el("toggle").setAttribute("aria-label", "Hide password");
    password.value = pw;
    analyze();
    checkBreach();
    try {
        await navigator.clipboard.writeText(pw);
        showToast("Generated and copied to clipboard");
    } catch (e) {
        showToast("Generated (copy failed — select and copy manually)");
    }
});

// Breach check via HaveIBeenPwned range API (k-anonymity), debounced
let breachTimer;
let breachController;
async function sha1(str) {
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(str));
    return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("").toUpperCase();
}
async function checkBreach() {
    const v = password.value;
    if (breachController) breachController.abort();
    breachController = new AbortController();
    if (v.length < 4) { breachRow.style.display = "none"; return; }
    const { signal } = breachController;

    breachRow.style.display = "flex";
    breachOut.innerHTML = '<span class="spinner"></span><span class="muted-note">Checking known breaches…</span>';

    if (!navigator.onLine) {
        breachOut.innerHTML = '<span class="muted-note">Breach check unavailable offline.</span>';
        return;
    }
    try {
        const hash = await sha1(v);
        const prefix = hash.slice(0, 5), suffix = hash.slice(5);
        const res = await fetch("https://api.pwnedpasswords.com/range/" + prefix, { signal });
        if (!res.ok) throw new Error("bad response");
        const text = await res.text();
        const match = text.split("\n").find(line => line.split(":")[0].trim() === suffix);
        if (match) {
            const count = parseInt(match.split(":")[1].trim(), 10).toLocaleString();
            breachOut.innerHTML = '<span style="color:var(--red)">⚠ Found in ' + count + ' breaches — do not use this.</span>';
        } else {
            breachOut.innerHTML = '<span style="color:var(--accent)">✓ Not found in known breaches</span>';
        }
    } catch (e) {
        if (e.name === "AbortError") return;
        breachOut.innerHTML = '<span class="muted-note">Breach check unavailable right now.</span>';
    }
}
password.addEventListener("input", () => {
    clearTimeout(breachTimer);
    breachTimer = setTimeout(checkBreach, 700);
});

// Initial render
analyze();