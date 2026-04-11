const themeToggle = document.getElementById("themeToggle");
const body = document.body;

if (localStorage.getItem("theme") === "dark") {
  body.classList.add("dark-mode");
  themeToggle.innerHTML = `<i class="fa-solid fa-sun"></i>`;
}

themeToggle.addEventListener("click", () => {
  body.classList.toggle("dark-mode");

  if (body.classList.contains("dark-mode")) {
    themeToggle.innerHTML = `<i class="fa-solid fa-sun"></i>`;
    localStorage.setItem("theme", "dark");
  } else {
    themeToggle.innerHTML = `<i class="fa-solid fa-moon"></i>`;
    localStorage.setItem("theme", "light");
  }
});
const menuToggle = document.getElementById("menuToggle");

if (localStorage.getItem("sidebar") === "hidden") {
  document.body.classList.add("sidebar-hidden");
}

if (menuToggle) {
  menuToggle.addEventListener("click", () => {
    document.body.classList.toggle("sidebar-hidden");

    if (document.body.classList.contains("sidebar-hidden")) {
      localStorage.setItem("sidebar", "hidden");
    } else {
      localStorage.setItem("sidebar", "shown");
    }
  });
}