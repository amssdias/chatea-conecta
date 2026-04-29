class ChatSocket extends WebSocket {
    static ACTION_TYPES = {
        HEARTBEAT: "heartbeat",
        PRIVATE_INVITE: "private_invite",
        REGISTER_GROUP: "register_group",
        SEND_MESSAGE: "send_message",
    };

    constructor(url, chatView, sideBarView) {
        super(url);
        this.chatView = chatView;
        this.sideMenuView = sideBarView;
        this._heartbeatInterval = null;
        this.onmessage = (event) => this.handleMessage(event);
        this.onopen = (event) => this.handleOpen(event);
        this.onclose = (event) => this.handleClose(event);

        this.messageHandlers = {
            notify_users_count: this.handleNotifyUsersCount.bind(this),
            send_message: this.handleSendMessage.bind(this),
            private_invite: this.handleChatInvite.bind(this),
            private_chat_participant_offline: this.handlePrivateChatOffline.bind(this),
            error_action: this.handle_error_socket_action.bind(this),
            private_chats_restored: this.handle_private_chats_restored.bind(this),
            private_chat_participant_online: this.handle_private_chat_participant_online.bind(this)
        };
    }

    handleOpen(event) {
        this.startHeartbeat();
    }

    startHeartbeat() {
        this.stopHeartbeat();

        this._heartbeatInterval = setInterval(() => {
            if (this.readyState === WebSocket.OPEN) {
                this.send(JSON.stringify({
                    type: ChatSocket.ACTION_TYPES.HEARTBEAT,
                }));
            }
        }, 30000);
    }

    stopHeartbeat() {
        if (this._heartbeatInterval) {
            clearInterval(this._heartbeatInterval);
            this._heartbeatInterval = null;
        }
    }

    handleMessage(event) {
        const data = JSON.parse(event.data);

        const handler = this.messageHandlers[data.type];

        if (handler) {
            handler(data);
        } else {
            console.warn("No handler for message type:", data.type);
        }

    };

    handleClose(e) {
        this.stopHeartbeat();

        console.error("Chat socket closed unexpectedly");
        const chatClosedEl = document.getElementById("chat-closed");
        chatClosedEl.classList.remove("hide");
        this.close();
    };

    handleNotifyUsersCount(data) {
        const onlineUsersCount = data.users_online;
        this.sideMenuView.updateUsersCountOnline(onlineUsersCount);
    }

    handleSendMessage(data) {
        if (data.userId === userId) {
            this.chatView.updateCurrentUserBackgroundMessage(data.message);
        } else {
            this.chatView.displayOtherUserMessage(
                data.username,
                data.userId,
                data.message,
                data.groupChatName,
                this.createPrivateChatGroup.bind(this),
                this.sendMessage.bind(this),
            );
        }
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

    registerGroupUser(groupChatName) {
        this.send(
            JSON.stringify({
                "type": ChatSocket.ACTION_TYPES.REGISTER_GROUP,
                "group": groupChatName,
            })
        );
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
        this.send(
            JSON.stringify({
                "type": ChatSocket.ACTION_TYPES.SEND_MESSAGE,
                "group": groupName,
                "message": message
            })
        );
    }

    createPrivateChatGroup(userIdTarget, usernameTarget) {
        this.chatView.openPrivateChatModal(
            userIdTarget,
            usernameTarget,
            this.sendMessage.bind(this),
        );

        this.send(JSON.stringify({
            "type": ChatSocket.ACTION_TYPES.PRIVATE_INVITE,
            "target_user_id": userIdTarget
        }));
    }

    handle_error_socket_action(data) {
        this.handleClose()
    }

    handle_private_chats_restored(data) {
        this.chatView.restorePrivateChatsState(data.privateChats);
    }

    handle_private_chat_participant_online(data) {
        console.log("Handle Private CHAT ONLINE");
        this.sideMenuView.setPrivateChatOnline(data.privateGroupId);
        this.chatView.addPrivateChatUser(data.userId, data.privateGroupId);
        this.chatView.markPrivateChatAsOnline(data.privateGroupId);
    }

}

export default ChatSocket;