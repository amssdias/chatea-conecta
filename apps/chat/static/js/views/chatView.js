import {appendTextWithLinks} from "../utils/create_elements.js";


class ChatView {

    _parentElement = document.querySelector(".chat-container");

    constructor(username, userId, sideBarView, translations = {}, isPro = false) {
        this._privateChatsMapping = {};
        this._username = username;
        this._userId = userId;
        this._sideBarView = sideBarView;
        this._translations = translations;
        this._isPro = isPro;
        this._leavePrivateChatHandler = null;
    }

    // =========================
    // Public getters
    // =========================

    get activeChat() {
        return this._getActiveChatElement();
    }

    // =========================
    // Public chat visibility
    // =========================

    hideActiveChat() {
        const activeChat = this.activeChat;

        if (activeChat) {
            activeChat.classList.remove("active");
            activeChat.classList.add("hide");
        }

    }

    displayChat(chat) {
        if (!chat) {
            console.warn("No chat provided to display");
            return;
        }

        this.hideActiveChat();
        chat.classList.remove("hide");
        chat.classList.add("active");
    }

    deleteChat(chat) {
        if (chat && chat.parentNode) {
            chat.parentNode.removeChild(chat);
        }
    }

    // =========================
    // Public chat creation
    // =========================

    createChat(groupChatName, groupId, sendMessageHandler) {

        // Chat header
        const chatHeader = this._createChatHeader(groupChatName);

        // Chat messages box
        const chatBox = this._createChatBox();

        // Chat form
        const form = this._createChatForm(sendMessageHandler, groupId);

        // Create chat
        const chat = document.createElement("div");
        chat.classList.add("chat", "hide");
        chat.dataset.groupName = groupId;

        chat.appendChild(chatHeader);
        chat.appendChild(chatBox);
        chat.appendChild(form);
        

        this._parentElement.appendChild(chat);

        return chat;
    }

    // =========================
    // Public message rendering
    // =========================

    displayOtherUserMessage(
        username,
        userId,
        message,
        groupChatName,
        createPrivateChatGroup,
        sendMsgHandler
    ) {
        const isPrivateGroup = this._isPrivateGroup(groupChatName);

        let chat = this._getChatElement(groupChatName);

        if (!chat && isPrivateGroup) {
            chat = this._createMissingPrivateChat(
                userId,
                username,
                groupChatName,
                sendMsgHandler
            );
        }

        if (!chat) {
            console.warn(`Chat not found for group: ${groupChatName}`);
            return;
        }

        const chatBox = this._getChatMessagesElement(chat);

        if (!chatBox) {
            console.warn(`Chat messages element not found for group: ${groupChatName}`);
            return;
        }

        this._appendMessageToChatBox({
            chatBox,
            username,
            userId,
            message,
            createPrivateChatGroup,
            // Only in the main room: inside a private chat you are already
            // talking to that person.
            canOpenPrivateChat: !isPrivateGroup,
        });

        const notificationGroupName = isPrivateGroup
            ? this._privateChatsMapping[userId]
            : groupChatName;

        this._addIncomingNotificationIfNeeded(chat, notificationGroupName);
    }

    displayCurrentUserMessage(message) {
        const activeChat = this.activeChat;

        if (!activeChat) {
            console.warn("No active chat found");
            return;
        }

        const chatBox = this._getChatMessagesElement(activeChat);

        if (!chatBox) {
            console.warn("Chat messages element not found");
            return;
        }

        this._appendMessageToChatBox({
            chatBox,
            username: this._username,
            userId: this._userId,
            message,
            isCurrentUser: true,
        });
    }

    updateCurrentUserBackgroundMessage(userMessage) {
        // Get all messages from a current user, get the last that matches the same message

        const activeChat = this.activeChat;

        if (!activeChat) {
            console.warn("No active chat found");
            return;
        }

        const chatMessagesEl = this._getChatMessagesElement(activeChat);

        if (!chatMessagesEl) {
            console.warn("Chat messages element not found");
            return;
        }

        const currentUserMessages = Array
            .from(chatMessagesEl.querySelectorAll(".chat__message--current-user"))
            .reverse();

        currentUserMessages.forEach(userChatMessage => {
            const userMessages = userChatMessage.querySelectorAll(".chat__message-text");

            userMessages.forEach(message => {
                if (message.textContent === userMessage) {
                    message.classList.remove("background-color-text-sending");
                }
            });
        });

    }

    // =========================
    // Public private-chat actions
    // =========================

    openPrivateChatModal(userIdTarget, usernameTarget, sendMsgHandler) {
        const existingPrivateChatId = this._privateChatsMapping[userIdTarget];
        const privateChatId = existingPrivateChatId || this._getPrivateChatGroupName(this._userId, userIdTarget);
        if (!this._sideBarView.canOpenPrivateChat(privateChatId)) {
            this._sideBarView.showPrivateChatLimitMessage();
            return false;
        }

        this.hideActiveChat();

        // Check if already exists a unique name for this private chat
        if (userIdTarget in this._privateChatsMapping) {

            // Check if exists a modal, if not create it
            const privateChat = this._getChatElement(privateChatId);
            if (privateChat) {

                privateChat.classList.add("active");
                privateChat.classList.remove("hide");

            } else {
                // 1. Create and display chat
                const chat = this.createChat(usernameTarget, privateChatId, sendMsgHandler);
                this.displayChat(chat);

                // 2. Add user private chat to side bar view
                this._sideBarView.addPrivateChat(
                    userIdTarget,
                    usernameTarget,
                    privateChatId,
                    this.displayChat.bind(this, chat),
                    this.deleteChat.bind(this, chat),
                    false
                );
                
            }
            
        } else {
            // 1. Create and display chat
            const chat = this.createChat(usernameTarget, privateChatId, sendMsgHandler);
            this.displayChat(chat);

            // 2. Add user private chat to side bar view
            this._sideBarView.addPrivateChat(
                userIdTarget,
                usernameTarget,
                privateChatId,
                this.displayChat.bind(this, chat),
                this.deleteChat.bind(this, chat),
                false
            );

            // 3. Add to object of private chats
            this._privateChatsMapping[userIdTarget] = privateChatId;
        }
        return true;

    }

    removePrivateChat(userIdTarget, privateGroupId) {
        delete this._privateChatsMapping[userIdTarget];
        this.deleteChat(this._getChatElement(privateGroupId));
        this._sideBarView.removePrivateChat(privateGroupId);
    }

    addPrivateChatUser(fromUserId, privateGroup) {
        this._privateChatsMapping[fromUserId] = privateGroup;
    }

    restorePrivateChatsState(privateChats) {
        this._privateChatsMapping = privateChats || {};
    }

    // =========================
    // Public private-chat status
    // =========================

    markPrivateChatAsOnline(privateGroupId) {
        this.markPrivateChatStatus(privateGroupId, "online");
    }

    markPrivateChatAsOffline(privateGroupId) {
        this.markPrivateChatStatus(privateGroupId, "offline");
    }

    markPrivateChatStatus(privateGroupId, status) {
        const chatModal = this._getChatElement(privateGroupId);

        if (!chatModal) {
            return;
        }

        const isOffline = status === "offline";

        this._updatePrivateChatHeaderStatus(chatModal, isOffline);
        this._updatePrivateChatInputStatus(chatModal, isOffline);
    }

    // =========================
    // Private DOM selectors
    // =========================

    _getActiveChatElement() {
        return this._parentElement.querySelector(".active");
    }

    _getChatElement(groupId) {
        return this._parentElement.querySelector(`[data-group-name="${groupId}"]`);
    }

    _getChatMessagesElement(chatElement) {
        return chatElement.querySelector(".chat__messages");
    }

    _getChatHeaderTitleElement(chatElement) {
        return chatElement.querySelector(".chat__header .chat__header-title");
    }

    _getChatFormInputElement(chatElement) {
        return chatElement.querySelector(".chat-form .chat-form-input");
    }

    _getChatFormInputFromForm(form) {
        return form.querySelector(".chat-form-input");
    }

    // =========================
    // Private chat element creation
    // =========================

    _createChatHeader(groupChatName) {
        const chatHeader = document.createElement("div");
        chatHeader.classList.add("chat__header");

        const h4El = document.createElement("h4");
        h4El.classList.add("chat__header-title");

        h4El.textContent = groupChatName;
        chatHeader.appendChild(h4El);

        return chatHeader;
    }

    _createChatBox() {
        const chatBox = document.createElement("div");
        chatBox.classList.add("chat__messages", "margin-top-xsmall");
        return chatBox;
    }

    _createChatForm(sendMsgHandler, groupChatName) {

        const form = document.createElement("form");
        form.classList.add("chat-form", "margin-top-xsmall");

        const inputEl = document.createElement("input");
        inputEl.type = "text";
        inputEl.classList.add("chat-form-input");

        const btn = document.createElement("button");
        btn.type = "submit";
        btn.textContent = "Submit";
        btn.classList.add("chat-form-btn");

        form.appendChild(inputEl);
        form.appendChild(btn);
        form.addEventListener("submit", (e) => {
            e.preventDefault();

            // Get the text to be sent
            const chatFormInput = this._getChatFormInputFromForm(form);
            const message = chatFormInput.value.trim();
            if (!message) return;

            // Display message on the chat
            this.displayCurrentUserMessage(message);

            // Clear input
            chatFormInput.value = "";

            sendMsgHandler(groupChatName, message);
        });

        return form;
    }

    // =========================
    // Private message element creation
    // =========================

    // Six avatar colours, picked from the username so the same person keeps
    // the same colour for everyone in the room without the server sending one.
    _avatarVariant(username) {
        let hash = 0;
        for (let i = 0; i < username.length; i++) {
            hash = (hash * 31 + username.charCodeAt(i)) >>> 0;
        }
        return (hash % 6) + 1;
    }

    _createAvatar(username) {
        const avatar = document.createElement("span");
        avatar.classList.add(
            "chat__message-avatar",
            `chat__message-avatar--${this._avatarVariant(username)}`
        );
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = username.charAt(0).toUpperCase();
        return avatar;
    }

    // Messages are never stored, so everything rendered here arrived just now
    // and the client clock is the honest source for the timestamp.
    _createTimestamp() {
        const now = new Date();
        const time = document.createElement("time");
        time.classList.add("chat__message-time");
        time.dateTime = now.toISOString();
        time.textContent = now.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });
        return time;
    }

    // Makes a nickname (or its avatar) open a private chat when clicked.
    // Keyboard support too: these are not <button>s, so Enter and Space have
    // to be wired by hand for anyone not using a mouse.
    _makeOpenPrivateChat(el, onOpenPrivateChat) {
        el.classList.add("chat__message-user-link");
        el.setAttribute("role", "button");
        el.setAttribute("tabindex", "0");
        el.title = this._translations.sendPrivateMsg || "Send private message";

        const open = () => {
            // Read the identity back off the message block rather than closing
            // over the values. dataset always yields strings, and the socket
            // sends user_id as a number - _getPrivateChatGroupName calls
            // .replace() on it, so a raw number throws.
            const block = el.closest("[data-user-id][data-username]");
            if (!block) return;

            const { userId, username } = block.dataset;
            if (!userId || !username) return;

            onOpenPrivateChat(userId, username);
        };

        el.addEventListener("click", open);
        el.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                open();
            }
        });
    }

    _createUserChatMessageElements(
        message,
        username,
        userId,
        isCurrentUser = false,
        onOpenPrivateChat = null
    ) {
        const div = document.createElement("div");

        div.setAttribute("data-username", username);
        div.setAttribute("data-user-id", userId);
        div.classList.add("chat__message");

        const userHeader = document.createElement("h5");
        userHeader.classList.add("chat__message-user");
        userHeader.textContent = username;

        const avatar = this._createAvatar(username);
        const paragraph = this._createMessageParagraph(message, isCurrentUser);

        if (isCurrentUser) {
            div.classList.add("chat__message--current-user");
        }

        // Clicking the nickname or the avatar opens a private chat with that
        // person. Never on your own name, and never inside a private chat -
        // the caller decides by passing null.
        if (onOpenPrivateChat && !isCurrentUser) {
            this._makeOpenPrivateChat(userHeader, onOpenPrivateChat);
            this._makeOpenPrivateChat(avatar, onOpenPrivateChat);
            avatar.removeAttribute("aria-hidden");
            avatar.setAttribute("aria-label", username);
        }

        // Only the first message of a run gets these: consecutive messages from
        // the same person append a paragraph to this block instead of building
        // a new one, which is the grouping the design shows.
        div.appendChild(avatar);
        div.appendChild(userHeader);
        div.appendChild(this._createTimestamp());
        div.appendChild(paragraph);

        return div;
    }

    _createMessageParagraph(message, isCurrentUser = false) {
        const paragraph = document.createElement("p");
        paragraph.classList.add("chat__message-text");

        if (isCurrentUser) {
            paragraph.classList.add("background-color-text-sending");
        }

        appendTextWithLinks(paragraph, message);

        return paragraph;
    }

    // =========================
    // Private private-chat status helpers
    // =========================

    _updatePrivateChatHeaderStatus(chatElement, isOffline) {
        const nameEl = this._getChatHeaderTitleElement(chatElement);

        if (!nameEl) {
            return;
        }

        const cleanName = nameEl.textContent.replace(" (Offline)", "");

        nameEl.textContent = isOffline
            ? `${cleanName} (Offline)`
            : cleanName;
    }

    _updatePrivateChatInputStatus(chatElement, isOffline) {
        const formInputEl = this._getChatFormInputElement(chatElement);

        if (!formInputEl) {
            return;
        }

        formInputEl.placeholder = isOffline ? "User is offline" : "";
        formInputEl.disabled = isOffline;
    }

    // =========================
    // Private message rendering helpers
    // =========================

    _shouldScrollToBottom(chatBox) {
        return chatBox.scrollHeight - chatBox.clientHeight - chatBox.scrollTop <= 5;
    }

    _scrollToBottom(chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    _appendMessageToChatBox({
        chatBox,
        username,
        userId,
        message,
        isCurrentUser = false,
        createPrivateChatGroup = null,
        canOpenPrivateChat = false,
    }) {
        const lastMessage = chatBox.lastElementChild;
        const shouldScroll = this._shouldScrollToBottom(chatBox);

        if (lastMessage && lastMessage.dataset.username === username) {
            const paragraph = this._createMessageParagraph(message, isCurrentUser);
            lastMessage.appendChild(paragraph);
        } else {
            const messageElement = this._createUserChatMessageElements(
                message,
                username,
                userId,
                isCurrentUser,
                canOpenPrivateChat ? createPrivateChatGroup : null
            );

            chatBox.appendChild(messageElement);
        }

        if (shouldScroll) {
            this._scrollToBottom(chatBox);
        }
    }

    // =========================
    // Private private-chat helpers
    // =========================

    _getOrCreatePrivateChatMapping(userId, groupChatName) {
        if (!this._privateChatsMapping[userId]) {
            this._privateChatsMapping[userId] = groupChatName;
        }

        return this._privateChatsMapping[userId];
    }

    _createMissingPrivateChat(userId, username, groupChatName, sendMsgHandler) {
        const privateChatId = this._getOrCreatePrivateChatMapping(userId, groupChatName);

        const chat = this.createChat(username, privateChatId, sendMsgHandler);

        this._sideBarView.addPrivateChat(
            userId,
            username,
            privateChatId,
            this.displayChat.bind(this, chat),
            this.deleteChat.bind(this, chat),
            true
        );

        return chat;
    }

    _addIncomingNotificationIfNeeded(chat, groupName) {
        if (chat.classList.contains("active")) {
            return;
        }

        this._sideBarView.addIncomingMsgNotification(groupName);
    }

    _isPrivateGroup(groupChatName) {
        return groupChatName.startsWith("private-");
    }

    _getPrivateChatGroupName(userId, userIdTarget) {
        // Coerced because callers are not consistent: dataset gives strings but
        // the socket payload gives user_id as a number, and a number has no
        // .replace(). Must stay in step with USER_PRIVATE_GROUP in
        // apps/chat/constants/consumer.py.
        userId = String(userId).replace(" ", "-");
        userIdTarget = String(userIdTarget).replace(" ", "-");
        return `private-${userId}-${userIdTarget}`.toLowerCase();
    }

}

export default ChatView;
