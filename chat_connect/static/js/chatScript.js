const chatView = new ChatView();

document.querySelector(".chat-app__groups").addEventListener("click", function (e) {
    e.preventDefault();

    const targetEl = e.target;
    if (!targetEl) return;

    const groupChatLink = targetEl.closest(".chat-app__group-link") ? targetEl : targetEl.children[0];
    const groupChatName = groupChatLink.innerHTML;

    // Open web sockets connection
    // const chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${groupChatName}/`);
    // chatSocket.onmessage = function (e) {
    //     const data = JSON.parse(e.data);
    //     document.querySelector('#chat-log').value += (data.message + '\n');
    // };

    // chatSocket.onclose = function (e) {
    //     console.error('Chat socket closed unexpectedly');
    // };

    // Display chat
    chatView.createChat(groupChatName, sendMessage);

})



function sendMessage(e) {
    e.preventDefault();

    // Get the text to be sent
    const chatFormInput = this.querySelector(".chat-form-input");
    const message = chatFormInput.value.trim();
    if (!message) return;

    // Check who sent the last text
    const chatBox = document.getElementById("chat-messages");
    const lastMessage = chatBox.lastElementChild;

    // If last sent was by current user append to the div
    if (lastMessage && lastMessage.classList.contains("chat__message--current-user")) {

        const paragraph = document.createElement("p");
        paragraph.classList.add("chat__message-text");
        paragraph.innerHTML = message;

        lastMessage.appendChild(paragraph);

    } else {
        // If last sent was by the other user, create new div
        const div = chatView.createUserChatMessageElements(message);
        chatBox.appendChild(div);

    }
    chatFormInput.value = "";

};
