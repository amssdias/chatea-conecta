import {appendTextWithLinks} from "../utils/create_elements.js";
import {avatarInitial, avatarVariant} from "../utils/avatar.js";

// The textarea grows with the message and then scrolls, rather than growing
// until it has eaten the conversation.
const COMPOSER_MAX_HEIGHT = 132;

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

        this._bindLimitNotice();
    }

    // =========================
    // Public getters
    // =========================

    get activeChat() {
        return this._getActiveChatElement();
    }

    // The translated strings the views write into the DOM, from chat.html.
    get strings() {
        return this._translations;
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
        this.hideLimitNotice();
        chat.classList.remove("hide");
        chat.classList.add("active");

        this._sideBarView.setActiveChat(chat.dataset.groupName);
    }

    deleteChat(chat) {
        if (chat && chat.parentNode) {
            chat.parentNode.removeChild(chat);
        }
    }

    // =========================
    // Public chat creation
    // =========================

    createChat(groupChatName, groupId, sendMessageHandler, options = {}) {
        const isRoom = Boolean(options.isRoom);

        // Chat header
        const chatHeader = this._createChatHeader(groupChatName, isRoom);

        // Chat messages box
        const chatBox = this._createChatBox();

        // Someone stepping out mid-conversation, said above the composer
        // rather than bolted onto the header title.
        const offlineBar = document.createElement("p");
        offlineBar.className = "chat__offline-bar hide";

        // Chat form
        const form = this._createChatForm(sendMessageHandler, groupId, groupChatName, isRoom);

        // Create chat
        const chat = document.createElement("div");
        chat.classList.add("chat", "hide");
        chat.dataset.groupName = groupId;
        chat.dataset.displayName = groupChatName;
        if (isRoom) chat.dataset.room = "true";

        chat.appendChild(chatHeader);
        chat.appendChild(chatBox);
        chat.appendChild(offlineBar);
        chat.appendChild(form);


        this._parentElement.appendChild(chat);

        // A private chat opens on a line saying what it is, which is also what
        // keeps the empty conversation from looking broken.
        if (!isRoom && this._translations.privateChatOpened) {
            this._appendSystemMessage(chatBox, this._translations.privateChatOpened);
        }

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
            this._sideBarView.showPrivateChatLimitMessage(usernameTarget);
            return false;
        }

        this.hideActiveChat();

        // Check if already exists a unique name for this private chat
        if (userIdTarget in this._privateChatsMapping) {

            // Check if exists a modal, if not create it
            const privateChat = this._getChatElement(privateChatId);
            if (privateChat) {

                this.displayChat(privateChat);

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
    // Public free-plan ceiling
    // =========================

    // The design puts this where the decision is made - a bar under the header
    // of the conversation you are in, with the way out next to it - instead of
    // a browser alert you can only acknowledge.
    showLimitNotice(usernameTarget = "", message = "") {
        const notice = document.getElementById("chat-limit-notice");

        if (!notice) {
            window.alert(message || privateChatLimitMessage);
            return;
        }

        this._setLimitNoticeDetail(notice, usernameTarget, message);

        const activeChat = this.activeChat;
        const header = activeChat && activeChat.querySelector(".chat__header");

        if (header) {
            header.insertAdjacentElement("afterend", notice);
        }

        notice.classList.remove("hide");
    }

    hideLimitNotice() {
        const notice = document.getElementById("chat-limit-notice");
        if (notice) notice.classList.add("hide");
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

    _createChatHeader(groupChatName, isRoom) {
        const chatHeader = document.createElement("div");
        chatHeader.classList.add("chat__header");

        // One burger per conversation header. Only one header is ever on
        // screen, and it is the only navigation this page has on a phone.
        chatHeader.appendChild(this._createRailToggle());

        if (!isRoom) {
            chatHeader.appendChild(this._createHeaderAvatar(groupChatName));
        }

        const text = document.createElement("span");
        text.classList.add("chat__header-text");

        const h4El = document.createElement("h4");
        h4El.classList.add("chat__header-title");
        h4El.textContent = groupChatName;

        const sub = document.createElement("span");
        sub.classList.add("chat__header-sub");
        sub.textContent = isRoom
            ? (this._translations.roomHeaderSubtitle || "")
            : (this._translations.onlineNow || "");

        text.append(h4El, sub);
        chatHeader.appendChild(text);

        chatHeader.appendChild(this._createHeaderActions(isRoom));

        return chatHeader;
    }

    _createRailToggle() {
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "chat__header-burger";
        toggle.setAttribute("aria-label", this._translations.openChatList || "Open chat list");
        toggle.appendChild(document.createElement("span"));

        toggle.addEventListener("click", () => this._sideBarView.openSideBar());

        return toggle;
    }

    _createHeaderAvatar(username) {
        const avatar = document.createElement("span");
        avatar.className = `chat__header-avatar chat__message-avatar--${avatarVariant(username)}`;
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = avatarInitial(username);
        return avatar;
    }

    _createHeaderActions(isRoom) {
        const actions = document.createElement("span");
        actions.className = "chat__header-actions";

        if (isRoom) {
            const presence = document.createElement("span");
            presence.className = "chat__header-presence";

            const dot = document.createElement("span");
            dot.className = "side-menu__dot online";

            const count = document.createElement("span");
            count.className = "js-online-count";
            count.textContent = "–";

            // One flex item, not two: otherwise the pill's 7px gap lands
            // between the number and the word it belongs to.
            const label = document.createElement("span");
            label.append(
                count,
                document.createTextNode(` ${this._translations.online || "online"}`)
            );

            presence.append(dot, label);
            actions.appendChild(presence);
        }

        // Every page of the site promises a report button in the chat. It
        // reaches the same inbox as /contact/, with the reason preselected.
        if (this._translations.reportUrl) {
            const report = document.createElement("a");
            report.className = "chat__header-report";
            report.href = this._translations.reportUrl;
            report.target = "_blank";
            report.rel = "noopener noreferrer";
            report.textContent = this._translations.report || "Report";
            actions.appendChild(report);
        }

        return actions;
    }

    _createChatBox() {
        const chatBox = document.createElement("div");
        chatBox.classList.add("chat__messages");
        return chatBox;
    }

    _createChatForm(sendMsgHandler, groupChatName, displayName, isRoom) {

        const form = document.createElement("form");
        form.classList.add("chat-form");

        const row = document.createElement("div");
        row.classList.add("chat-form__row");

        // A textarea, not an input: a long message wraps instead of scrolling
        // sideways through a one-line slot, which is what the canvas shows.
        const inputEl = document.createElement("textarea");
        inputEl.rows = 1;
        inputEl.classList.add("chat-form-input");
        inputEl.placeholder = this._composerPlaceholder(displayName, isRoom);
        inputEl.dataset.placeholder = inputEl.placeholder;
        inputEl.setAttribute("aria-label", inputEl.placeholder);

        const btn = document.createElement("button");
        btn.type = "submit";
        btn.textContent = this._translations.send || "Send";
        btn.classList.add("chat-form-btn");

        row.appendChild(inputEl);
        row.appendChild(btn);

        const hint = document.createElement("p");
        hint.classList.add("chat-form__hint");
        hint.textContent = isRoom
            ? (this._translations.roomHint || "")
            : (this._translations.privateHint || "");

        form.appendChild(row);
        form.appendChild(hint);

        inputEl.addEventListener("input", () => this._autoGrowComposer(inputEl));

        // Enter sends, Shift+Enter starts a new line.
        inputEl.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" || event.shiftKey) return;

            event.preventDefault();
            if (typeof form.requestSubmit === "function") {
                form.requestSubmit();
            } else {
                form.dispatchEvent(new Event("submit", {cancelable: true}));
            }
        });

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
            this._autoGrowComposer(chatFormInput);

            sendMsgHandler(groupChatName, message);
        });

        return form;
    }

    _composerPlaceholder(displayName, isRoom) {
        if (isRoom) return this._translations.roomPlaceholder || "";

        return (this._translations.privatePlaceholder || "%(name)s")
            .replace("%(name)s", displayName);
    }

    _autoGrowComposer(inputEl) {
        inputEl.style.height = "auto";
        inputEl.style.height = `${Math.min(inputEl.scrollHeight, COMPOSER_MAX_HEIGHT)}px`;
    }

    // =========================
    // Private message element creation
    // =========================

    _createAvatar(username) {
        const avatar = document.createElement("span");
        avatar.classList.add(
            "chat__message-avatar",
            `chat__message-avatar--${avatarVariant(username)}`
        );
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = avatarInitial(username);
        return avatar;
    }

    // Not a message from anybody: a hairline with a few words on it, marking
    // what just happened to the conversation.
    _appendSystemMessage(chatBox, text) {
        const line = document.createElement("p");
        line.className = "chat__message chat__message--system";

        const label = document.createElement("span");
        label.textContent = text;

        line.appendChild(label);
        chatBox.appendChild(line);
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
    // Private free-plan ceiling helpers
    // =========================

    _bindLimitNotice() {
        const dismiss = document.getElementById("chat-limit-dismiss");
        if (dismiss) dismiss.addEventListener("click", () => this.hideLimitNotice());
    }

    _setLimitNoticeDetail(notice, usernameTarget, message) {
        const detail = notice.querySelector("#chat-limit-notice-detail");
        if (!detail) return;

        // The generic sentence is the one Django rendered. Keep a copy the
        // first time round so naming a person is reversible.
        if (!detail.dataset.defaultText) {
            detail.dataset.defaultText = detail.textContent.trim();
        }

        if (message) {
            detail.textContent = message;
            return;
        }

        const template = this._translations.limitWithName;

        if (!usernameTarget || !template || !template.includes("%(name)s")) {
            detail.textContent = detail.dataset.defaultText;
            return;
        }

        const [before, after] = template.split("%(name)s");
        const name = document.createElement("strong");
        name.className = "chat__notice-name";
        name.textContent = usernameTarget;

        detail.replaceChildren(document.createTextNode(before), name, document.createTextNode(after));
    }

    // =========================
    // Private private-chat status helpers
    // =========================

    _updatePrivateChatHeaderStatus(chatElement, isOffline) {
        const sub = chatElement.querySelector(".chat__header-sub");

        if (sub) {
            sub.textContent = isOffline
                ? (this._translations.offline || "")
                : (this._translations.onlineNow || "");
            sub.classList.toggle("chat__header-sub--offline", isOffline);
        }

        const bar = chatElement.querySelector(".chat__offline-bar");

        if (bar) {
            const name = chatElement.dataset.displayName || "";
            bar.textContent = (this._translations.peerWentOffline || "")
                .replace("%(name)s", name);
            bar.classList.toggle("hide", !isOffline);
        }
    }

    _updatePrivateChatInputStatus(chatElement, isOffline) {
        const formInputEl = this._getChatFormInputElement(chatElement);

        if (!formInputEl) {
            return;
        }

        formInputEl.placeholder = isOffline
            ? (this._translations.offlinePlaceholder || "")
            : (formInputEl.dataset.placeholder || "");
        formInputEl.disabled = isOffline;

        const sendBtn = chatElement.querySelector(".chat-form-btn");
        if (sendBtn) sendBtn.disabled = isOffline;
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

        this._updateRailPreview(chatBox, message, isCurrentUser);

        if (shouldScroll) {
            this._scrollToBottom(chatBox);
        }
    }

    // The rail row shows the last thing said, so a stack of private chats
    // reads as conversations rather than a list of nicknames.
    _updateRailPreview(chatBox, message, isCurrentUser) {
        const chat = chatBox.closest(".chat");
        if (!chat || chat.dataset.room === "true") return;

        this._sideBarView.setPrivateChatPreview(
            chat.dataset.groupName,
            message,
            isCurrentUser
        );
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
