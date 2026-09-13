import ChatView from "./views/chatView.js";
import SideBarView from "./views/sideBarView.js";
import ChatSocket from "./chatSocket.js";

import {SOCKET_URL} from "./config.js";

const translations = {
    sendPrivateMsg,
    ...(typeof chatStrings === "undefined" ? {} : chatStrings),
};

const sideBarView = new SideBarView(isPro, translations);
const chatView = new ChatView(
    currentUser,
    userId,
    sideBarView,
    translations,
    isPro
);

// The free-plan ceiling is a bar inside the conversation, and only chatView
// knows which conversation is open - so the rail asks it to draw one.
sideBarView.onLimitReached = (usernameTarget, message) =>
    chatView.showLimitNotice(usernameTarget, message);

const chatSocketHandler = new ChatSocket(
    SOCKET_URL,
    chatView,
    sideBarView,
    userId,
);

// Closing a row is not just a DOM removal: the consumer counts open private
// chats to enforce the free-plan ceiling, so it has to be told as well.
sideBarView.onPrivateChatClosed = (userIdTarget, privateGroupId) => {
    chatView.removePrivateChat(userIdTarget, privateGroupId);
    chatSocketHandler.closePrivateChat(userIdTarget);
};

// There is no topbar on this page: the drawer is opened from the burger in
// each conversation header (chatView) and closed from the rail's own button,
// the scrim behind it, or Escape.
const sideMenuCloseBtn = document.getElementById("side-menu-close-btn");
const sideMenuScrim = document.getElementById("side-menu-scrim");

if (sideMenuCloseBtn) {
    sideMenuCloseBtn.addEventListener("click", () => sideBarView.closeSideBar());
}

if (sideMenuScrim) {
    sideMenuScrim.addEventListener("click", () => sideBarView.closeSideBar());
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") sideBarView.closeSideBar();
});

// Back on a wide screen the rail is a permanent column again, so a drawer
// left open would otherwise keep its scrim over the conversation.
window.addEventListener("resize", function () {
    if (this.innerWidth > 900) sideBarView.closeSideBar();
});


chatSocketHandler.onOpen(() => {
    chatSocketHandler.createMainChat("Chatea");
});
