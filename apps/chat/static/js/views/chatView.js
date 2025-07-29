import { convertLinksToAnchors } from "../utils/create_elements.js";
import { toLowerKebabCase } from "../utils/stringUtils.js";


class ChatView {

    _parentElement = document.querySelector(".chat-container");

    constructor(username, sideBarView) {
        this._privateChatsMapping = {}
        this._username = username;
        this._sideBarView = sideBarView;
    }

    get activeChat() {
        return this._parentElement.querySelector(".active");
    }

    displayNUsersOnline(users_online) {
        const chatHeader = this.activeChat.querySelector(".chat__header-title");
        
        // Remove any existing user count in parentheses
        chatHeader.innerHTML = chatHeader.innerHTML.replace(/\(\d+\)\s*/, "");

        chatHeader.innerHTML = `(${users_online}) ${chatHeader.innerHTML}`;
    }

    hideActiveChat() {
        const activeChat = this.activeChat;

        if (activeChat) {
            activeChat.classList.remove("active");
            activeChat.classList.add("hide");
        }

    }

    displayChat (chat) {
        this.hideActiveChat();
        chat.classList.remove("hide");
        chat.classList.add("active");
    }

    createChat(groupChatName, sendMessageHandler) {

        // Chat header
        const chatHeader = this.createChatHeader(groupChatName);

        // Chat messages box
        const chatBox = this.createChatBox();

        // Chat form
        const form = this.createChatForm(sendMessageHandler, groupChatName);

        // Create chat
        const chat = document.createElement("div");
        chat.classList.add("chat", "hide");
        chat.dataset.groupName = groupChatName;

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

        // Use it in the future
        const svgElChatClose = `
        <svg class="chat__header-close" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="#fef3c7">
            <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
            <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
            <g id="SVGRepo_iconCarrier">
                <g id="Edit / Close_Circle">
                    <path id="Vector" d="M9 9L11.9999 11.9999M11.9999 11.9999L14.9999 14.9999M11.9999 11.9999L9 14.9999M11.9999 11.9999L14.9999 9M12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21Z" stroke="#fef3c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
                </g>
            </g>
        </svg>
        `;

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

    displayOtherUserMessage(username, message, groupChatName, createPrivateChatGroup, sendMsgHandler) {

        let chat = this._parentElement.querySelector(`[data-group-name=${groupChatName}]`);
        
        if (!chat) {
            const usernameFormatted = toLowerKebabCase(username);
            chat = this.createChat(this._privateChatsMapping[usernameFormatted], sendMsgHandler)
            const addIncomingMsgNotification = true;
            this._sideBarView.addPrivateChat(
                username,
                this.displayChat.bind(this, chat),
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
                username
            );
            const userMenu = this.createUserMenu(createPrivateChatGroup);
            div.appendChild(userMenu);

            chatBox.appendChild(div);

        }

        if (shouldScroll) {
            chatBox.scrollTop = chatBox.scrollHeight;
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
                true,
            );
            chatBox.appendChild(div);

        }

        if (shouldScroll) {
            chatBox.scrollTop = chatBox.scrollHeight;
        }


    }

    createUserChatMessageElements(message, username, isCurrentUser = false) {
        const div = document.createElement("div");

        div.setAttribute("data-username", username);
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
            const username = this.closest('[data-username]')?.dataset.username;
            if (!username) return;

            createPrivateChatGroup(username);
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

    // displayGroupChat(groupChatName) {

    //     this.hideActiveChat();

    //     const groupChat = this._parentElement.querySelector(`[data-group-name=${groupChatName}]`)
    //     groupChat.classList.add("active");
    //     groupChat.classList.remove("hide");
    // }

    openPrivateChatModal(usernameTarget, sendMsgHandler) {

        this.hideActiveChat();
        
        const cleanUsernameTarget = toLowerKebabCase(usernameTarget);
        const cleanCurrentUser = toLowerKebabCase(this._username)

        // Check if already exists a unique name for this private chat
        if (cleanUsernameTarget in this._privateChatsMapping) {

            // Check if exists a modal, if not create it
            const privateChatId = this._privateChatsMapping[usernameTarget];
            const privateChat = this._parentElement.querySelector(`[data-group-name=${privateChatId}]`)
            if (privateChat) {

                privateChat.classList.add("active");
                privateChat.classList.remove("hide");

            } else {
                // 1. Create and display chat
                const chat = this.createChat(privateChatId, sendMsgHandler);
                this.displayChat(chat);

                // 2. Add user private chat to side bar view
                this._sideBarView.addPrivateChat(
                    usernameTarget,
                    this.displayChat.bind(this, chat),
                );
                
            }
            
        } else {
            const privateChatId = `private-${cleanCurrentUser}-${cleanUsernameTarget}`;
            
            // 1. Create and display chat
            const chat = this.createChat(privateChatId, sendMsgHandler);
            this.displayChat(chat);
            
            // 2. Add user private chat to side bar view
            this._sideBarView.addPrivateChat(
                cleanUsernameTarget,
                this.displayChat.bind(this, chat),
            );

            // 3. Add to object of private chats
            this._privateChatsMapping[cleanUsernameTarget] = privateChatId;
        }

    }

    addPrivateChatUser(data) {
        const fromUsername = toLowerKebabCase(data.from_user);
        const privateGroup = data.private_group;
        this._privateChatsMapping[fromUsername] = privateGroup;
    }

}

export default ChatView;
