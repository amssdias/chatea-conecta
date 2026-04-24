class ChatSocket extends WebSocket {
    static ACTION_TYPES = {
        PRIVATE_INVITE: "private_invite",
        REGISTER_GROUP: "register_group",
        SEND_MESSAGE: "send_message",
    };

    constructor(url, chatView, sideBarView) {
        super(url);
        this.chatView = chatView;
        this.sideMenuView = sideBarView;
        this.onmessage = (event) => this.handleMessage(event);
        this.onclose = (event) => this.handleClose(event);

        this.messageHandlers = {
            notify_users_count: this.handleNotifyUsersCount.bind(this),
            send_message: this.handleSendMessage.bind(this),
            private_invite: this.handleChatInvite.bind(this),
            private_chat_participant_offline: this.handlePrivateChatOffline.bind(this),
            error_action: this.handle_error_socket_action.bind(this)
        };
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
        this.chatView.addPrivateChatUser(data);
    }

    handlePrivateChatOffline(data) {       
        // Change color of side bar private chat
        this.sideMenuView.setPrivateChatOffline(data.userId);

        // On user chat, make a way to target him as offline
        this.chatView.markPrivateChatAsOffline(data.userId);
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

}

export default ChatSocket;