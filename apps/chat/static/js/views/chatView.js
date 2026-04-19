import { convertLinksToAnchors } from "../utils/create_elements.js";
import { toLowerKebabCase } from "../utils/stringUtils.js";


class ChatView {

    _parentElement = document.querySelector(".chat-container");

    constructor(username, userId, sideBarView) {
        this._privateChatsMapping = {}
        this._username = username;
        this._userId = userId;
        this._sideBarView = sideBarView;
    }

    get activeChat() {
        return this._parentElement.querySelector(".active");
    }

    hideActiveChat() {
        const activeChat = this.activeChat;

        if (activeChat) {
            activeChat.classList.remove("active");
            activeChat.classList.add("hide");
        }

    }

    getPrivateChatUsername(chatName) {
        const [, userId, userId2] = chatName.split("-");
        return this._userId !== userId ? userId : userId2;
    }

    getPrivateChatId(username1, username2) {
        return `private-${username1}-${username2}`;
    }

    getChatModal(chatId) {
        return this._parentElement.querySelector(`[data-group-name=${chatId}]`)
    }

    displayChat(chat) {
        this.hideActiveChat();
        chat.classList.remove("hide");
        chat.classList.add("active");
    }

    deleteChat(chat) {
        if (chat && chat.parentNode) {
            chat.parentNode.removeChild(chat);
        }
    }

    createChat(groupChatName, groupId, sendMessageHandler) {

        // Chat header
        const chatHeader = this.createChatHeader(groupChatName);

        // Chat messages box
        const chatBox = this.createChatBox();

        // Chat form
        const form = this.createChatForm(sendMessageHandler, groupId);

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

    createChatHeader(groupChatName) {
        const chatHeader = document.createElement("div");
        chatHeader.classList.add("chat__header");

        const h4El = document.createElement("h4");
        h4El.classList.add("chat__header-title");

        // const username = groupChatName.includes("private") ? this.getPrivateChatUsername(groupChatName) : groupChatName;

        h4El.innerHTML = groupChatName;
        chatHeader.appendChild(h4El);

        return chatHeader;
    }

    createChatBox() {
        const chatBox = document.createElement("div");
        chatBox.classList.add("chat__messages", "margin-top-xsmall");
        chatBox.id = "chat-messages";
        return chatBox;
    }

    createChatForm(sendMsgHandler, groupChatName) {

        const form = document.createElement("form");
        form.classList.add("chat-form", "margin-top-xsmall");
        form.id = "chat-form";

        const inputEl = document.createElement("input");
        inputEl.type = "text";
        inputEl.classList.add("chat-form-input");

        const btn = document.createElement("button");
        btn.type = "submit";
        btn.innerHTML = "Submit";
        btn.classList.add("chat-form-btn");

        form.appendChild(inputEl);
        form.appendChild(btn);
        form.addEventListener("submit", (e) => {
            e.preventDefault();

            // Get the text to be sent
            const chatFormInput = form.querySelector(".chat-form-input");
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

    displayOtherUserMessage(
        username, 
        userId, 
        message, 
        groupChatName, 
        createPrivateChatGroup, 
        sendMsgHandler
    ) {

        let chat = this.getChatModal(groupChatName);
        
        if (!chat) {
            const privateChatMapping = this._privateChatsMapping[userId]
            chat = this.createChat(username, privateChatMapping, sendMsgHandler);
            const addIncomingMsgNotification = true;
            this._sideBarView.addPrivateChat(
                userId,
                username,
                privateChatMapping,
                this.displayChat.bind(this, chat),
                this.deleteChat.bind(this, chat),
                addIncomingMsgNotification
            );
        };
        
        // Check who sent the last text
        const chatBox = chat.querySelector(".chat__messages");
        const lastMessage = chatBox.lastElementChild;
        const msg = convertLinksToAnchors(message);

        // If the user is not at the bottom of the chat, don't scrool, if yes, scroll
        const shouldScroll = chatBox.scrollHeight - chatBox.clientHeight - chatBox.scrollTop <= 5;

        // If last sent was by same user, then only add a paragraph to it
        if (lastMessage && lastMessage.dataset.username === username) {

            const paragraph = document.createElement("p");
            paragraph.classList.add("chat__message-text");
            paragraph.innerHTML = msg;

            lastMessage.appendChild(paragraph);


        } else {
            // If last sent was by some other user, create new div
            const div = this.createUserChatMessageElements(
                msg,
                username,
                userId
            );
            const userMenu = this.createUserMenu(createPrivateChatGroup);
            div.appendChild(userMenu);

            chatBox.appendChild(div);

        }

        if (shouldScroll) {
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        // Add notification chat on side menu if not opened
        if (!chat.classList.contains("active")) {
            const isPrivateGroup = groupChatName.includes("private") ? true : false;
            const groupName = isPrivateGroup ? this._privateChatsMapping[userId] : groupChatName ;
            this._sideBarView.addIncomingMsgNotification(groupName)
        }

    }

    displayCurrentUserMessage(message) {

        // Check who sent the last text
        const chatBox = this.activeChat.querySelector(".chat__messages");
        const lastMessage = chatBox.lastElementChild;
        const msg = convertLinksToAnchors(message);

        const shouldScroll = chatBox.scrollHeight - chatBox.clientHeight - chatBox.scrollTop <= 5;

        // If last sent was by current user append to the div
        if (lastMessage && lastMessage.dataset.username === this._username) {

            const paragraph = document.createElement("p");
            paragraph.classList.add("chat__message-text", "background-color-text-sending");
            paragraph.innerHTML = msg;

            lastMessage.appendChild(paragraph);

        } else {
            // If last sent was by the other user, create new div
            const div = this.createUserChatMessageElements(
                msg,
                this._username,
                this._userId, 
                true,
            );
            chatBox.appendChild(div);

        }

        if (shouldScroll) {
            chatBox.scrollTop = chatBox.scrollHeight;
        }


    }

    createUserChatMessageElements(message, username, userId, isCurrentUser = false) {
        const div = document.createElement("div");

        div.setAttribute("data-username", username);
        div.setAttribute("data-user-id", userId);
        div.classList.add("chat__message");

        const userHeader = document.createElement("h5");
        userHeader.classList.add("chat__message-user", "chat__message-user-link");
        userHeader.innerHTML = username;

        const paragraph = document.createElement("p");
        paragraph.classList.add("chat__message-text");
        paragraph.innerHTML = message;

        if (isCurrentUser) {
            div.classList.add("chat__message--current-user");
            paragraph.classList.add("background-color-text-sending");
        }

        div.appendChild(userHeader);
        div.appendChild(paragraph);

        return div;
    }

    createUserMenu(createPrivateChatGroup) {
        const menuOption = document.createElement("button");
        menuOption.classList.add("chat__message-menu-btn");
        menuOption.innerHTML = sendPrivateMsg;

        menuOption.addEventListener("click", function() {
            const userId = this.closest('[data-user-id]')?.dataset.userId;
            if (!userId) return;

            const username = this.closest('[data-username]')?.dataset.username;
            if (!username) return;


            createPrivateChatGroup(userId, username);
        })

        let userMenu = document.createElement("div");
        userMenu.classList.add("chat__message-menu");
        userMenu.appendChild(menuOption);
        return userMenu;
    }

    updateCurrentUserBackgroundMessage(userMessage) {

        // Get all messages from a current user, get the last that matches the same message
        const chatMessagesEl = this.activeChat.querySelector(".chat__messages");
        const currentUserMessages = Array.from(chatMessagesEl.querySelectorAll(".chat__message--current-user")).reverse()
        const userMsg = convertLinksToAnchors(userMessage);
        currentUserMessages.forEach(userChatMessage => {
            const userMessages = userChatMessage.querySelectorAll(".chat__message-text");
            
            userMessages.forEach(message => {
                if (message.innerHTML === userMsg) {
                    message.classList.remove("background-color-text-sending");
                }
            })

        })
    }

    openPrivateChatModal(userIdTarget, usernameTarget, sendMsgHandler) {

        this.hideActiveChat();

        // Check if already exists a unique name for this private chat
        if (userIdTarget in this._privateChatsMapping) {

            // Check if exists a modal, if not create it
            const privateChatId = this._privateChatsMapping[userIdTarget];
            const privateChat = this.getChatModal(privateChatId);
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
            const privateChatId = this._getPrivateChatGroupName(this._userId, userIdTarget)

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

    }

    addPrivateChatUser(data) {
        const fromUserId = data.fromUserId;
        const privateGroup = data.privateGroup;
        this._privateChatsMapping[fromUserId] = privateGroup;
    }

    markPrivateChatAsOffline(userId) {
        let chatId = this._getPrivateChatGroupName(this._userId, userId);
        let chatModal = this.getChatModal(chatId);
        if (!chatModal) {
            chatId = this.getPrivateChatId(userId, this._username);
            chatModal = this.getChatModal(chatId);
            if (!chatModal) return;
        }

        const nameEl = chatModal.querySelector(".chat__header .chat__header-title");
        const privateChatName = nameEl.textContent;

        nameEl.textContent = `${privateChatName} (Offline)`

        const formInputEl = chatModal.querySelector(".chat-form .chat-form-input");
        formInputEl.setAttribute("placeholder", "User is offline");
        formInputEl.disabled = true;

    }

    _getPrivateChatGroupName(userId, userIdTarget) {
        userId = userId.replace(" ", "-");
        userIdTarget = userIdTarget.replace(" ", "-");
        return `private-${userId}-${userIdTarget}`.toLowerCase();
    }

}

export default ChatView;
