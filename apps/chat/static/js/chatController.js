import ChatView from "./views/chatView.js";
import ChatGroupsView from "./views/chatGroupsView.js";
import ChatSocket from "./chatSocket.js";

import { SOCKET_URL } from "./config.js";

const chatGroups = document.getElementById("chat-groups");

const chatView = new ChatView(username);
const chatGroupsView = new ChatGroupsView();

const chatSocketHandler = new ChatSocket(SOCKET_URL, chatView);

const openedChats = new Set();


if (chatGroups) {

    // Event when user selects a group to chat
    chatGroups.addEventListener("click", function (e) {
        e.preventDefault();

        const targetEl = e.target;
        if (!targetEl) return;
        if (targetEl.closest("#group-search")) return;

        const groupChatLink = targetEl.closest(".chat-app__group-link") ? targetEl : targetEl.querySelector(".chat-app__group-link");
        if (!groupChatLink) return;
        const groupChatName = groupChatLink.dataset.groupName?.toLowerCase();

        // If the user already opened this chat
        if (openedChats.has(groupChatName)) {

            chatView.displayGroupChat(groupChatName);

        } else {

            // Register user on a group
            chatSocketHandler.send(
                JSON.stringify({
                    "registerGroup": true,
                    "group": groupChatName,
                    "username": username,
                })
            );

            // Show group online icon
            chatGroupsView.activateGroup(groupChatName);

            // Display chat with event
            chatView.createChat(groupChatName, sendMessage);

            // Add to list of opened chats
            openedChats.add(groupChatName);
        };

        // Make group chat as selected
        chatGroupsView.selectedGroupChat(groupChatName);

    });

    // Event to search groups
    document.getElementById("group-search").addEventListener("keyup", function (e) {

        const searchFilter = this.children[0].value.toLowerCase();

        const groups = document.getElementById("chat-app-groups");
        const allGroups = groups.querySelectorAll("li > a");

        for (const group of allGroups) {
            const groupName = group.dataset.groupName.split("_").join(" ");
            if (!groupName.includes(searchFilter)) {
                group.parentElement.style.display = "none";
            } else {
                group.parentElement.style.display = "flex";
            }
        }
    });

}


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
    chatGroupsView.openGroupChatsList();

});

// Open online groups chats
const groupsOnline = document.getElementById("groups-connected");
groupsOnline.addEventListener("click", function (e) {
    chatGroupsView.openOnlineGroupsList();
})

// Make sure if window is resized the chat ocupies the whole space
window.addEventListener("resize", function (e) {

    if (this.innerWidth > 600) {
        document.querySelector(".chat-container").classList.remove("hide");
    }
})


// Delete all localstorage if user leave the chatapp
window.addEventListener('beforeunload', function (event) {
    // You can optionally prompt the user with a confirmation dialog
    //    event.preventDefault(); // This line is required in some browsers
    //    event.returnValue = ''; // A string must be assigned to indicate a prompt should show
});

function createMainChat(groupChatName) {
    // Register user on a group
    chatSocketHandler.send(
        JSON.stringify({
            "registerGroup": true,
            "group": groupChatName,
            "username": username,
        })
    );

    // Display chat with event
    chatView.createChat(groupChatName, sendMessage);

    // Add to list of opened chats
    openedChats.add(groupChatName);
}

chatSocketHandler.addEventListener('open', () => {
    createMainChat("chatea");
});
