document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registerForm");
  if (!form) return;

  const errorBox = document.getElementById("clientErrorBox");
  const btn = document.getElementById("registerBtn");

  const showError = (msg) => {
    errorBox.textContent = msg;
    errorBox.classList.remove("d-none");
  };

  const clearError = () => {
    errorBox.textContent = "";
    errorBox.classList.add("d-none");
  };

  form.addEventListener("submit", (e) => {
    clearError();

    // basic required check
    const requiredInputs = form.querySelectorAll("input[required]");
    for (const input of requiredInputs) {
      if (!input.value.trim()) {
        e.preventDefault();
        showError("Please fill in all required fields.");
        input.focus();
        return;
      }
    }

    // password match check if present
    const p1 = document.getElementById("id_password1");
    const p2 = document.getElementById("id_password2");
    if (p1 && p2 && p1.value !== p2.value) {
      e.preventDefault();
      showError("Passwords do not match.");
      p2.focus();
      return;
    }

    btn.disabled = true;
    btn.textContent = "Creating account...";
  });
});