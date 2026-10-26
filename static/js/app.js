document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.dataset.confirm || "Are you sure?")) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll(".flash").forEach(function (message) {
    window.setTimeout(function () {
      message.classList.add("flash-hidden");
    }, 4500);
  });
});
