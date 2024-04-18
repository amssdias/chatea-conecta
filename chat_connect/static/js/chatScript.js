const chatForm = document.getElementById("chat-form");
const chatMessages = document.getElementById("chat-messages");
let user = "Dias";

chatForm.addEventListener("submit", function (e) {
    e.preventDefault();

    // Get the text to be sent
    const chatFormInput = chatForm.querySelector(".chat-form-input");
    const message = chatFormInput.value.trim();
    if (!message) return;

    // Check who sent the last text
    const lastMessage = chatMessages.lastElementChild;

    // If last sent was by current user append to the div
    if (lastMessage.classList.contains("chat__message--current-user")) {

        const paragraph = document.createElement("p");
        paragraph.classList.add("chat__message-text");
        paragraph.innerHTML = message;

        lastMessage.appendChild(paragraph);

    } else {
        // If last sent was by the other user, create new div
        const div = createUserChatMessageElements(message);
        chatMessages.appendChild(div);

    }
    chatFormInput.value = "";

})


function createUserChatMessageElements(message) {
    const div = document.createElement("div");
    div.classList.add("chat__message", "chat__message--current-user");

    const userHeader = document.createElement("h5");
    userHeader.classList.add("chat__message-user");
    userHeader.innerHTML = user;

    const paragraph = document.createElement("p");
    paragraph.classList.add("chat__message-text");
    paragraph.innerHTML = message;

    div.appendChild(userHeader);
    div.appendChild(paragraph);

    return div;
}