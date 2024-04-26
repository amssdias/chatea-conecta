class ChatView {

    _parentElement = document.querySelector(".chat");

    constructor(username) {
        this._username = username;
    }

    clearChat() {
        this._parentElement.innerHTML = "";
    }

    createChat(groupChatName, send_message_handler) {

        // Clear chat
        this.clearChat();

        // Create chat header
        const chatHeader = this.createChatHeader(groupChatName);

        // Chat box
        const chatBox = this.createChatBox();

        // Chat form
        const form = this.createChatForm(send_message_handler);

        this._parentElement.appendChild(chatHeader);
        this._parentElement.appendChild(chatBox);
        this._parentElement.appendChild(form);
    }

    createChatHeader(groupChatName) {
        const chatHeader = document.createElement("div");
        chatHeader.classList.add("chat__header");
        chatHeader.innerHTML = groupChatName;
        return chatHeader;
    }

    createChatBox() {
        const chatBox = document.createElement("div");
        chatBox.classList.add("chat__messages", "margin-top-xsmall");
        chatBox.id = "chat-messages";
        return chatBox;
    }

    createChatForm(handler) {
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
        form.addEventListener("submit", handler);
        return form;
    }

    displayOtherUserMessage(username, message) {

        // Check who sent the last text
        const chatBox = document.getElementById("chat-messages");
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
        const chatBox = document.getElementById("chat-messages");
        const lastMessage = chatBox.lastElementChild;

        // If last sent was by current user append to the div
        if (lastMessage && lastMessage.dataset.username === this._username) {

            const paragraph = document.createElement("p");
            paragraph.classList.add("chat__message-text");
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
        if (isCurrentUser) {
            div.classList.add("chat__message--current-user")
        }

        div.setAttribute("data-username", username);
        div.classList.add("chat__message");

        const userHeader = document.createElement("h5");
        userHeader.classList.add("chat__message-user");
        userHeader.innerHTML = username;

        const paragraph = document.createElement("p");
        paragraph.classList.add("chat__message-text");
        paragraph.innerHTML = message;

        div.appendChild(userHeader);
        div.appendChild(paragraph);

        return div;
    }
}

