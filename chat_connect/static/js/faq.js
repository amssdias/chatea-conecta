const faqQuestionsEl = document.querySelectorAll(".faq__question");

faqQuestionsEl.forEach(faqQuestion => {
    faqQuestion.addEventListener("click", function(e) {

        // Ensure we're working with the main .faq__question div
        const parentDiv = e.currentTarget;

        // Toggle the visibility of the <p> tag
        const paragraph = parentDiv.querySelector(".paragraph");
        if (paragraph) {
            paragraph.classList.toggle("hide");
        }

        const svgIcons = parentDiv.querySelectorAll("svg");
        if (svgIcons.length === 2) {
            svgIcons[0].classList.toggle("hide");
            svgIcons[1].classList.toggle("hide");
        }
    })
});
