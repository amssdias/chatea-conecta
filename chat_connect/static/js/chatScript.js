const chatView = new ChatView(username);

// Open web sockets connection
let chatSocket;

document.querySelector(".chat-app__groups").addEventListener("click", function (e) {
    e.preventDefault();

    const targetEl = e.target;
    if (!targetEl) return;

    const groupChatLink = targetEl.closest(".chat-app__group-link") ? targetEl : targetEl.children[0];
    const groupChatName = groupChatLink.innerHTML.toLowerCase();

    chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${groupChatName}/`);

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        // console.log(`RECEIVED MESSAGE FROM ${data.username} - MESSAGE SOCKET: ${data}`)

        // If message was from the same user who sent, we don't need to display on the user
        if (data.username === username) return;

        // Show message from other users
        chatView.displayOtherUserMessage(
            data.username,
            data.message
        );
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket closed unexpectedly');
    };

    // Display chat
    chatView.createChat(groupChatName, sendMessage);

})



function sendMessage(e) {
    e.preventDefault();

    // Get the text to be sent
    const chatFormInput = this.querySelector(".chat-form-input");
    const message = chatFormInput.value.trim();
    if (!message) return;

    // Display message on the chat
    chatView.displayCurrentUserMessage(message);

    // Clear input
    chatFormInput.value = "";

    console.log("SENDING MESSAGE ON SOCKET: ", message);
    chatSocket.send(
        JSON.stringify({
            'message': message
        })
    );

};
