function validateForm(event) {
  event.preventDefault();
  const name = document.querySelector('input[name="name"]');
  const email = document.querySelector('input[name="email"]');
  const phone = document.querySelector('input[name="phone"]');
  const year = document.querySelector('input[name="year"]');
  const branch = document.querySelector('input[name="branch"]');


  if (!name || !email || !phone || !year || !branch) {
    console.error("One or more form fields not found:", {
      name,
      email,
      phone,
      year,
      branch,
    });
    alert("An error occurred. Please try again or contact support.");
    return false;
  }

  if (
    !name.value ||
    !email.value ||
    !phone.value ||
    !year.value ||
    !branch.value
  ) {
    alert("All fields except 'After registration' are required!");
    return false;
  }
  if (!email.value.includes("@")) {
    alert("Invalid email format!");
    return false;
  }
  if (!/^\d{10,}$/.test(phone.value)) {
    alert("Phone must be a valid 10+ digit number!");
    return false;
  }
  event.target.submit();
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(
    'form[onsubmit="return validateForm(event)"]'
  );
  if (form) {
    form.addEventListener("submit", validateForm);
  } else {
    console.log("No registration form found on this page.");
  }
});
