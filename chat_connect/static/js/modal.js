const modalTermsConditionsEl = document.getElementById("modal-terms-conditions");

document.getElementById("terms-and-conditions").addEventListener("click", function() {

    modalTermsConditionsEl.classList.remove("hide");

});

function closeModal() {
    modalTermsConditionsEl.classList.add("hide");
}

