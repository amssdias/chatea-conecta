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

    // Create chat socket
    const groupSocket = createChatSocket(groupChatName);

    // Display chat with event
    chatView.createChat(groupChatName, sendMessage, groupSocket);

})


function createChatSocket(groupChatName) {

    const socketUrl = `ws://${window.location.host}/ws/chat/${groupChatName}/`;
    let chatSocket =  new ChatSocket(socketUrl, chatView);
    return chatSocket;

}


function sendMessage(chatSocket) {

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
