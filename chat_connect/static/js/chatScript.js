const chatGroups = document.querySelector(".chat-app__groups");

const chatView = new ChatView(username);

// Open web sockets connection
let chatSocket;

// Event when user selects a group to chat
chatGroups.addEventListener("click", function (e) {
    e.preventDefault();

    const targetEl = e.target;
    if (!targetEl) return;

    const groupChatLink = targetEl.closest(".chat-app__group-link") ? targetEl : targetEl.children[0];
    const groupChatName = groupChatLink.dataset.groupName?.toLowerCase();

    createChatSocket(groupChatName);

    // Display chat with event
    chatView.createChat(groupChatName, sendMessage);

})


function createChatSocket(groupChatName) {
    chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${groupChatName}/`);

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        // If message was from the same user who sent, 
        // we change the background knowing the user that it was successfully sent
        if (data.username === username) {
            chatView.updateCurrentUserBackgroundMessage(data.message);

        } else {
            // Show message from other users
            chatView.displayOtherUserMessage(
                data.username,
                data.message
            );
        }

    };

    chatSocket.onclose = function (e) {
        console.error("Chat socket closed unexpectedly");
    };
}


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

    // Send message through socket
    chatSocket.send(
        JSON.stringify({
            "message": message
        })
    );

};
