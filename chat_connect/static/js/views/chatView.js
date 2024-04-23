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

    createUserChatMessageElements(message) {
        const div = document.createElement("div");
        div.classList.add("chat__message", "chat__message--current-user");

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

