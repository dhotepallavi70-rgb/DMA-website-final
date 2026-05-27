function toggleMenu() {
    document.getElementById("menu").classList.toggle("active");
}

function closePopup() {
    const popup = document.getElementById("popup");
    if (popup) {
        popup.style.display = "none";
    }
}

window.addEventListener("load", function () {
    const popup = document.getElementById("popup");
    if (popup) {
        popup.style.display = "flex";
    }
});
