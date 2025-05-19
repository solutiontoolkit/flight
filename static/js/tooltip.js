// static/js/tooltip.js

document.addEventListener("DOMContentLoaded", function () {
    const tooltips = {
        newBookingBtn: "Click to book a new flight.",
        logoutBtn: "Click here to safely log out of your account.",
    };

    Object.entries(tooltips).forEach(([id, message]) => {
        const el = document.getElementById(id);
        if (el) {
            const tooltip = document.createElement("div");
            tooltip.className = "custom-tooltip";
            tooltip.innerText = message;
            document.body.appendChild(tooltip);

            el.addEventListener("mouseover", () => {
                const rect = el.getBoundingClientRect();
                tooltip.style.top = `${rect.top - 35}px`;
                tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
                tooltip.style.opacity = 1;
            });

            el.addEventListener("mouseout", () => {
                tooltip.style.opacity = 0;
            });
        }
    });
});




