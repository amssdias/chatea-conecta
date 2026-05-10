const faqQuestionsEl = document.querySelectorAll(".faq__question");

faqQuestionsEl.forEach(faqQuestion => {
    faqQuestion.addEventListener("click", function(e) {

        // Ensure we're working with the main .faq__question div
        const parentDiv = e.currentTarget;
        const trigger = parentDiv.querySelector(".faq__question__header");

        // Toggle the visibility of the <p> tag
        const paragraph = parentDiv.querySelector(".paragraph");
        if (paragraph) {
            paragraph.classList.toggle("hide");
            paragraph.hidden = paragraph.classList.contains("hide");
            if (trigger) {
                trigger.setAttribute("aria-expanded", String(!paragraph.hidden));
            }
        }

        const svgIcons = parentDiv.querySelectorAll("svg");
        if (svgIcons.length === 2) {
            svgIcons[0].classList.toggle("hide");
            svgIcons[1].classList.toggle("hide");
        }
    })
});
