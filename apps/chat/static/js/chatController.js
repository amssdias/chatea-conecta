const chatGroups = document.querySelector(".chat-app__groups");

const chatView = new ChatView(username);

const openedChats = new Set();


// Event when user selects a group to chat
chatGroups.addEventListener("click", function (e) {
    e.preventDefault();

    const targetEl = e.target;
    if (!targetEl) return;

    const groupChatLink = targetEl.closest(".chat-app__group-link") ? targetEl : targetEl.children[0];
    const groupChatName = groupChatLink.dataset.groupName?.toLowerCase();

    // If the user already opened this chat
    if (openedChats.has(groupChatName)) {

        chatView.displayGroupChat(groupChatName);

    } else {
        // Create chat socket
        const groupSocket = createChatSocket(groupChatName);

        // Display chat with event
        chatView.createChat(groupChatName, sendMessage, groupSocket);

        // Add to list of opened chats
        openedChats.add(groupChatName);
    }



})


function createChatSocket(groupChatName) {

    const socketUrl = `${SOCKET_URL}${groupChatName}/`;
    let chatSocket = new ChatSocket(socketUrl, chatView);
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

// Save the messages on localstorage through a new file for chatModel.js
// Future make saying a small message saying (sendind and sent) on the chat



// Delete all localstorage if user leave the chatapp
window.addEventListener('beforeunload', function (event) {
    // You can optionally prompt the user with a confirmation dialog
    //    event.preventDefault(); // This line is required in some browsers
    //    event.returnValue = ''; // A string must be assigned to indicate a prompt should show
});
