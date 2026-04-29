class ChatSocket {
    static ACTION_TYPES = {
        HEARTBEAT: "heartbeat",
        PRIVATE_INVITE: "private_invite",
        REGISTER_GROUP: "register_group",
        SEND_MESSAGE: "send_message",
    };

    constructor(url, chatView, sideBarView, currentUserId) {
        this.socket = new WebSocket(url);
        this.chatView = chatView;
        this.sideMenuView = sideBarView;
        this.currentUserId = currentUserId;
        this._heartbeatInterval = null;

        this.messageHandlers = this._getMessageHandlers();

        this._bindSocketEvents();
    }

    // Connection lifecycle

    handleOpen(event) {
        this.startHeartbeat();
    }

    handleClose(event) {
        this.stopHeartbeat();
        console.error("Chat socket closed unexpectedly");
        this._showChatClosedMessage();
    }

    handleError(event) {
        console.error("WebSocket error:", event);
    }

    startHeartbeat() {
        this.stopHeartbeat();

        this._heartbeatInterval = setInterval(() => {
            this._sendPayload({
                type: ChatSocket.ACTION_TYPES.HEARTBEAT,
            });
        }, 30000);
    }

    stopHeartbeat() {
        if (this._heartbeatInterval) {
            clearInterval(this._heartbeatInterval);
            this._heartbeatInterval = null;
        }
    }

    onOpen(callback) {
        this.socket.addEventListener("open", callback);
    }

    // Incoming messages

    handleMessage(event) {
        let data;

        try {
            data = JSON.parse(event.data);
        } catch (error) {
            console.warn("Invalid WebSocket message:", event.data);
            return;
        }

        const handler = this.messageHandlers[data.type];

        if (!handler) {
            console.warn("No handler for message type:", data.type);
            return;
        }

        handler(data);

    }

    handleNotifyUsersCount(data) {
        const onlineUsersCount = data.users_online;
        this.sideMenuView.updateUsersCountOnline(onlineUsersCount);
    }

    handleSendMessage(data) {
        if (String(data.userId) === String(this.currentUserId)) {
            this.chatView.updateCurrentUserBackgroundMessage(data.message);
            return;
        }

        this.chatView.displayOtherUserMessage(
            data.username,
            data.userId,
            data.message,
            data.groupChatName,
            this.createPrivateChatGroup.bind(this),
            this.sendMessage.bind(this),
        );
    }

    handleChatInvite(data) {
        this.chatView.addPrivateChatUser(data.fromUserId, data.privateGroup);
    }

    handlePrivateChatOffline(data) {
        // Change color of side bar private chat
        this.sideMenuView.setPrivateChatOffline(data.privateGroupId);

        // On user chat, make a way to target him as offline
        this.chatView.markPrivateChatAsOffline(data.privateGroupId);
    }

    handleErrorSocketAction(data) {
        console.error("Socket error action received:", data);
        this._showChatClosedMessage();
    }

    handlePrivateChatsRestored(data) {
        this.chatView.restorePrivateChatsState(data.privateChats);
    }

    handlePrivateChatParticipantOnline(data) {
        this.sideMenuView.setPrivateChatOnline(data.privateGroupId);
        this.chatView.addPrivateChatUser(data.userId, data.privateGroupId);
        this.chatView.markPrivateChatAsOnline(data.privateGroupId);
    }

    // Outgoing actions

    registerGroupUser(groupChatName) {
        this._sendPayload({
            "type": ChatSocket.ACTION_TYPES.REGISTER_GROUP,
            "group": groupChatName,
        });
    }

    createMainChat(groupChatName) {
        const formattedGroupChatName = groupChatName.toLowerCase();
        this.registerGroupUser(formattedGroupChatName);

        // Create and display chat with event
        const chat = this.chatView.createChat(
            formattedGroupChatName, 
            formattedGroupChatName,
            this.sendMessage.bind(this)
        );

        this.chatView.displayChat(chat);

        this.sideMenuView.addGroupChat(
            groupChatName,
            this.chatView.displayChat.bind(this.chatView, chat)
        );
    }

    sendMessage(groupName, message) {
        this._sendPayload({
            "type": ChatSocket.ACTION_TYPES.SEND_MESSAGE,
            "group": groupName,
            "message": message,
        });
    }

    createPrivateChatGroup(userIdTarget, usernameTarget) {
        this.chatView.openPrivateChatModal(
            userIdTarget,
            usernameTarget,
            this.sendMessage.bind(this),
        );

        this._sendPayload({
            "type": ChatSocket.ACTION_TYPES.PRIVATE_INVITE,
            "target_user_id": userIdTarget,
        });
    }

    // Private helpers

    _bindSocketEvents() {
        this.socket.addEventListener("message", this.handleMessage.bind(this));
        this.socket.addEventListener("open", this.handleOpen.bind(this));
        this.socket.addEventListener("close", this.handleClose.bind(this));
        this.socket.addEventListener("error", this.handleError.bind(this));
    }

    _getMessageHandlers() {
        return {
            notify_users_count: this.handleNotifyUsersCount.bind(this),
            send_message: this.handleSendMessage.bind(this),
            private_invite: this.handleChatInvite.bind(this),
            private_chat_participant_offline: this.handlePrivateChatOffline.bind(this),
            error_action: this.handleErrorSocketAction.bind(this),
            private_chats_restored: this.handlePrivateChatsRestored.bind(this),
            private_chat_participant_online: this.handlePrivateChatParticipantOnline.bind(this),
        };
    }

    _sendPayload(payload) {
        if (this.socket.readyState !== WebSocket.OPEN) {
            console.warn("Cannot send message. WebSocket is not open.");
            return;
        }

        this.socket.send(JSON.stringify(payload));
    }

    _showChatClosedMessage() {
        const chatClosedEl = document.getElementById("chat-closed");

        if (chatClosedEl) {
            chatClosedEl.classList.remove("hide");
        }
    }

}

export default ChatSocket;