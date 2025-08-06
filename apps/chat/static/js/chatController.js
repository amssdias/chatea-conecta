import ChatView from "./views/chatView.js";
import SideBarView from "./views/sideBarView.js";
import ChatSocket from "./chatSocket.js";

import { SOCKET_URL } from "./config.js";

const chatGroups = document.getElementById("chat-groups");

const sideBarView = new SideBarView();
const chatView = new ChatView(
    currentUser, 
    sideBarView
);

const chatSocketHandler = new ChatSocket(
    SOCKET_URL,
    chatView,
    sideBarView,
);

const openedChats = new Set();


const sideMenuBtn = document.getElementById("side-menu-btn");
sideMenuBtn.addEventListener("click", function(e) {
    sideBarView.hideSideBar();
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


chatSocketHandler.addEventListener('open', () => {
    chatSocketHandler.createMainChat("Chatea");
});
