class ChatSocket extends WebSocket {

    constructor(url, chatView) {
        super(url);
        this.chatView = chatView;
        this.onmessage = (event) => this.handleMessage(event);
        this.onclose = (event) => this.handleClose(event);
    }

    handleMessage(event) {
        const data = JSON.parse(event.data);

        // Display how many users are online
        if (data.users_online) {
            this.chatView.displayNUsersOnline(data.users_online);
            console.log(`Users online: ${data.users_online}`);
            return;
        }

        // If message was from the same user who sent,
        // we change the background knowing the user that it was successfully sent
        if (data.username === username) {
            this.chatView.updateCurrentUserBackgroundMessage(data.message);

        } else {
            // Show message from other users
            this.chatView.displayOtherUserMessage(
                data.username,
                data.message,
                data.groupChatName
            );
        }

    };

    handleClose(e) {
        console.error("Chat socket closed unexpectedly");
        const chatClosedEl = document.getElementById("chat-closed");
        chatClosedEl.classList.remove("hide");
    };

}