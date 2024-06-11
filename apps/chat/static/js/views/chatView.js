class ChatView {

    _parentElement = document.querySelector(".chat-container");

    constructor(username) {
        this._username = username;
    }

    get activeChat() {
        return this._parentElement.querySelector(".active");
    }

    displayNUsersOnline(users_online) {
        const chatHeader = this.activeChat.querySelector(".chat__header-title");
        chatHeader.innerHTML = `(${users_online}) ${chatHeader.innerHTML}`;
    }

    hideActiveChat() {
        const activeChat = this.activeChat;

        if (activeChat) {
            activeChat.classList.remove("active");
            activeChat.classList.add("hide");
        }

    }

    createChat(groupChatName, send_message_handler, chatSocket) {

        // Hide chat
        this.hideActiveChat();

        // Chat header
        const chatHeader = this.createChatHeader(groupChatName);

        // Chat messages box
        const chatBox = this.createChatBox();

        // Chat form
        const form = this.createChatForm(send_message_handler, groupChatName);

        // Create chat
        const chat = document.createElement("div");
        chat.classList.add("chat", "active");
        chat.dataset.groupName = groupChatName;

        chat.appendChild(chatHeader);
        chat.appendChild(chatBox);
        chat.appendChild(form);

        this._parentElement.appendChild(chat);
    }

    createChatHeader(groupChatName) {
        const chatHeader = document.createElement("div");
        chatHeader.classList.add("chat__header");
        
        const h4El = document.createElement("h4");
        h4El.classList.add("chat__header-title");
        // chatHeader.innerHTML = groupChatName;

        const svgEl = `
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

        h4El.innerHTML = groupChatName + svgEl;
        chatHeader.appendChild(h4El);

        return chatHeader;
    }

    createChatBox() {
        const chatBox = document.createElement("div");
        chatBox.classList.add("chat__messages", "margin-top-xsmall");
        chatBox.id = "chat-messages";
        return chatBox;
    }

    createChatForm(handler, groupChatName) {

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
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            handler.call(this, groupChatName);
        });

        return form;
    }

    displayOtherUserMessage(username, message, groupChatName) {

        // Check who sent the last text
        const chat = this._parentElement.querySelector(`[data-group-name=${groupChatName}]`);

        if (!chat) return;

        const chatBox = chat.querySelector(".chat__messages");
        const lastMessage = chatBox.lastElementChild;

        // If last sent was by same user, then only add a paragraph to it
        if (lastMessage && lastMessage.dataset.username === username) {

            const paragraph = document.createElement("p");
            paragraph.classList.add("chat__message-text");
            paragraph.innerHTML = message;

            lastMessage.appendChild(paragraph);


        } else {
            // If last sent was by some other user, create new div
            const div = this.createUserChatMessageElements(
                message,
                username
            );
            chatBox.appendChild(div);

        }

    }

    displayCurrentUserMessage(message) {

        // Check who sent the last text
        const chatBox = this.activeChat.querySelector(".chat__messages");
        const lastMessage = chatBox.lastElementChild;

        // If last sent was by current user append to the div
        if (lastMessage && lastMessage.dataset.username === this._username) {

            const paragraph = document.createElement("p");
            paragraph.classList.add("chat__message-text", "background-color-text-sending");
            paragraph.innerHTML = message;

            lastMessage.appendChild(paragraph);

        } else {
            // If last sent was by the other user, create new div
            const div = this.createUserChatMessageElements(
                message,
                this._username,
                true,
            );
            chatBox.appendChild(div);

        }

    }

    createUserChatMessageElements(message, username, isCurrentUser = false) {
        const div = document.createElement("div");

        div.setAttribute("data-username", username);
        div.classList.add("chat__message");

        const userHeader = document.createElement("h5");
        userHeader.classList.add("chat__message-user");
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

    updateCurrentUserBackgroundMessage(userMessage) {

        // Get all messages from a current user, get the last that matches the same message
        const chatMessagesEl = this.activeChat.querySelector(".chat__messages");
        const currentUserMessages = Array.from(chatMessagesEl.querySelectorAll(".chat__message--current-user")).reverse()

        currentUserMessages.forEach(userChatMessage => {
            const userMessages = userChatMessage.querySelectorAll(".chat__message-text");

            userMessages.forEach(message => {
                if (message.innerHTML === userMessage) {
                    message.classList.remove("background-color-text-sending");
                }
            })

        })
    }

    displayGroupChat(groupChatName) {

        this.hideActiveChat();

        const groupChat = this._parentElement.querySelector(`[data-group-name=${groupChatName}]`)
        groupChat.classList.add("active");
        groupChat.classList.remove("hide");
    }
}

