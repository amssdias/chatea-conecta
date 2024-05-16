const chatGroups = document.querySelector(".chat-app__groups");

const chatView = new ChatView(username);
const chatGroupsView = new ChatGroupsView();

const chatSocketHandler = new ChatSocket(SOCKET_URL, chatView);

const openedChats = new Set();


// Event when user selects a group to chat
chatGroups.addEventListener("click", function (e) {
    e.preventDefault();

    const targetEl = e.target;
    if (!targetEl) return;

    const groupChatLink = targetEl.closest(".chat-app__group-link") ? targetEl : targetEl.querySelector(".chat-app__group-link");
    const groupChatName = groupChatLink.dataset.groupName?.toLowerCase();

    // If the user already opened this chat
    if (openedChats.has(groupChatName)) {

        chatView.displayGroupChat(groupChatName);

    } else {

        // Register user on a group
        chatSocketHandler.send(
            JSON.stringify({
                "registerGroup": groupChatName
            })
        );

        // Show group online icon
        chatGroupsView.activateGroup(groupChatName);

        // Make group chat as selected
        chatGroupsView.selectedGroupChat(groupChatName);

        // Display chat with event
        chatView.createChat(groupChatName, sendMessage);

        // Add to list of opened chats
        openedChats.add(groupChatName);
    };
});


function sendMessage(groupName) {

    // Get the text to be sent
    const chatFormInput = this.querySelector(".chat-form-input");
    const message = chatFormInput.value.trim();
    if (!message) return;

    // Display message on the chat
    chatView.displayCurrentUserMessage(message);

    // Clear input
    chatFormInput.value = "";

    // Send message through socket
    chatSocketHandler.send(
        JSON.stringify({
            "group": groupName,
            "message": message
        })
    );

};

// Open group chats
const groupsLinkImage = document.getElementById("groups-link");
groupsLinkImage.addEventListener("click", function (e) {

    const chatGroups = document.getElementById("chat-groups");

    // Hide or show group chats
    chatGroups.classList.toggle("hide");

    if (window.innerWidth <= 600) {
        if (chatGroups.classList.contains("hide")) {
            document.querySelector(".chat-container").classList.remove("hide");
        } else {
            document.querySelector(".chat-container").classList.add("hide");
        };

    };

});

// Make sure if window is resized the chat ocupies the whole space
window.addEventListener("resize", function (e) {

    if (this.innerWidth > 600) {
        document.querySelector(".chat-container").classList.remove("hide");
    }
})


// Save the messages on localstorage through a new file for chatModel.js
// Future make saying a small message saying (sendind and sent) on the chat



// Delete all localstorage if user leave the chatapp
window.addEventListener('beforeunload', function (event) {
    // You can optionally prompt the user with a confirmation dialog
    //    event.preventDefault(); // This line is required in some browsers
    //    event.returnValue = ''; // A string must be assigned to indicate a prompt should show
});
