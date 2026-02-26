document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("diagnose-form");
  const resultEl = document.getElementById("result");

  if (!form || !resultEl) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    resultEl.textContent = "";

    const formData = new FormData();

    const imagesInput = document.getElementById("images");
    const pondSizeInput = document.getElementById("pond-size");
    const pondDepthInput = document.getElementById("pond-depth");

    if (imagesInput && imagesInput.files) {
      Array.from(imagesInput.files).forEach((file, index) => {
        formData.append(`images_${index}`, file);
      });
    }

    if (pondSizeInput) {
      formData.append("pond_size", pondSizeInput.value);
    }

    if (pondDepthInput) {
      formData.append("pond_depth", pondDepthInput.value);
    }

    try {
      const response = await fetch("/api/diagnose", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();
      resultEl.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      resultEl.textContent = "An error occurred. Please try again.";
      // eslint-disable-next-line no-console
      console.error(error);
    }
  });
});
