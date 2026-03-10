console.log("main.js loaded 🚀");
function initDeleteModal() {
  const modalEl = document.getElementById("deleteModal");
  const formEl = document.getElementById("deleteForm");
  if (!modalEl || !formEl) return;

  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

  function forceCleanupBackdrop() {

    document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());

    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("padding-right");
  }


  modalEl.addEventListener("hidden.bs.modal", forceCleanupBackdrop);


  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      formEl.action = btn.dataset.url;
      modal.show();
    });
  });


  modalEl.querySelectorAll('[data-bs-dismiss="modal"]').forEach((btn) => {
    btn.addEventListener("click", () => {

      setTimeout(forceCleanupBackdrop, 50);
    });
  });
}
function initLoadingButtons() {
    const forms = document.querySelectorAll("form");

    forms.forEach(form => {
        form.addEventListener("submit", function () {

            const submitBtn = form.querySelector("button[type='submit']");
            if (!submitBtn) return;

            // Prevent duplicate clicks
            submitBtn.disabled = true;

            const spinner = submitBtn.querySelector(".spinner-border");
            const btnText = submitBtn.querySelector(".btn-text");

            if (spinner) spinner.classList.remove("d-none");

            if (btnText && submitBtn.dataset.loadingText) {
                btnText.textContent = submitBtn.dataset.loadingText;
            }
        });
    });
}
function initCaloriePreview() {
    const foodSelect = document.getElementById("id_food");
    const quantityInput = document.getElementById("id_quantity");
    const calDisplay = document.getElementById("calValue");

    if (!foodSelect || !quantityInput || !calDisplay) return;

    function updateCalories() {
        const selectedOption = foodSelect.options[foodSelect.selectedIndex];
        const caloriesPer100g = parseFloat(selectedOption.dataset.calories || "0");
        const quantity = parseFloat(quantityInput.value || "0");

        if (!caloriesPer100g || !quantity) {
            calDisplay.textContent = "0";
            return;
        }

        const total = (caloriesPer100g / 100) * quantity;
        calDisplay.textContent = Math.round(total).toString();
    }

    foodSelect.addEventListener("change", updateCalories);
    quantityInput.addEventListener("input", updateCalories);

    updateCalories();
}

document.addEventListener("DOMContentLoaded", () => {
  initCaloriePreview();
  initDeleteModal(let lastFocusedElement = null;

modalEl.addEventListener("show.bs.modal", function (event) {
    lastFocusedElement = event.relatedTarget;
});

modalEl.addEventListener("shown.bs.modal", function () {
    const firstButton = modalEl.querySelector("button");
    if (firstButton) {
        firstButton.focus();
    }
});

modalEl.addEventListener("hidden.bs.modal", function () {
    if (lastFocusedElement) {
        lastFocusedElement.focus();
    }
});
document.addEventListener("DOMContentLoaded", function () {
    initDeleteModal();
    initLoadingButtons();
});
);
});