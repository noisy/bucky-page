// iOS beta sign-up form (src/pages/beta.html). Saves one document to
// Firestore, betaSignups/<sha256 of the email>, which the Firestore rules in
// noisy/Bucky allow to be created once and never read back. Firebase code is
// fetched from Google only when the form is sent, so just opening the page
// makes no third-party request.
//
// Testing against the Firestore emulator: on localhost, add
// ?emulator=127.0.0.1:8080 to the page URL.

const config = JSON.parse(document.getElementById("beta-config").textContent);
const form = document.querySelector("[data-beta-form]");
const SAVE_TIMEOUT_MS = 15000;
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

const pageLanguage = document.documentElement.lang;
const defaultLanguage = form.querySelector(`[data-default-for="${pageLanguage}"]`) || form.querySelector("[name=language]");
defaultLanguage.checked = true;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage(null);
  const signup = readForm();
  if (!EMAIL.test(signup.email) || signup.email.length > 254) return showMessage("invalid-email", form.email);
  if (!signup.consent) return showMessage("need-consent", form.consent);
  if (!config.firebase.projectId) return showMessage("closed");

  setBusy(true);
  try {
    const outcome = await withTimeout(save(signup), SAVE_TIMEOUT_MS);
    showDone(outcome);
  } catch (error) {
    console.warn("Beta sign-up not saved", error && error.code);
    showMessage("error");
  } finally {
    setBusy(false);
  }
});

function readForm() {
  const data = new FormData(form);
  const signup = {
    email: String(data.get("email") || "").trim().toLowerCase(),
    language: data.get("language") === "pl" ? "pl" : "en",
    consent: data.get("consent") === "on",
    consentVersion: config.consent_version,
  };
  const ages = data.getAll("kidsAges");
  if (ages.length) signup.kidsAges = ages;
  return signup;
}

// "saved" for a new sign-up, "duplicate" when the email is already on the
// list: the rules refuse the second write as an update of an existing
// document, and the form has already checked everything else they check.
async function save(signup) {
  const { firestore, db } = await connect();
  const id = await sha256Hex(signup.email);
  try {
    await firestore.setDoc(firestore.doc(db, "betaSignups", id), {
      ...signup,
      createdAt: firestore.serverTimestamp(),
    });
    return "saved";
  } catch (error) {
    if (error && error.code === "permission-denied") return "duplicate";
    throw error;
  }
}

// Loads Firebase once; a failed load is retried on the next submit.
let connection;
function connect() {
  connection = connection || openFirestore().catch((error) => {
    connection = null;
    throw error;
  });
  return connection;
}

async function openFirestore() {
  const sdk = config.sdk_url;
  const [{ initializeApp }, firestore] = await Promise.all([
    import(`${sdk}/firebase-app.js`),
    import(`${sdk}/firebase-firestore.js`),
  ]);
  const app = initializeApp(firebaseOptions(), "bucky-beta");
  if (config.app_check.enabled) await startAppCheck(app, sdk);
  const db = firestore.getFirestore(app);
  const emulator = new URLSearchParams(location.search).get("emulator");
  if (emulator && ["localhost", "127.0.0.1"].includes(location.hostname)) {
    const [host, port] = emulator.split(":");
    firestore.connectFirestoreEmulator(db, host, Number(port));
  }
  return { firestore, db };
}

function firebaseOptions() {
  // Only non-empty values: Firestore needs just the project id.
  return Object.fromEntries(Object.entries(config.firebase).filter(([, value]) => value));
}

async function startAppCheck(app, sdk) {
  const appCheck = await import(`${sdk}/firebase-app-check.js`);
  const Provider = config.app_check.provider === "recaptcha-v3"
    ? appCheck.ReCaptchaV3Provider
    : appCheck.ReCaptchaEnterpriseProvider;
  appCheck.initializeAppCheck(app, {
    provider: new Provider(config.app_check.site_key),
    isTokenAutoRefreshEnabled: false,
  });
}

async function sha256Hex(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function withTimeout(promise, ms) {
  let timer;
  const timeout = new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("timeout")), ms); });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function showMessage(name, focusField) {
  form.querySelectorAll("[data-message]").forEach((message) => { message.hidden = message.dataset.message !== name; });
  if (focusField) focusField.focus();
}

function setBusy(busy) {
  const button = form.querySelector("[data-submit]");
  button.disabled = busy;
  button.querySelector("[data-label-idle]").hidden = busy;
  button.querySelector("[data-label-busy]").hidden = !busy;
}

function showDone(outcome) {
  form.hidden = true;
  const done = document.querySelector(`[data-done="${outcome === "saved" ? "success" : "duplicate"}"]`);
  done.hidden = false;
  done.focus();
}
