class SideBarView {

    _parentElement = document.getElementById("side-menu");

    toggleSideBar() {
        this._parentElement.classList.toggle("open-side-menu");
    }

    addIncomingMessageClass(el) {
        el.classList.add("incoming-message");
    }

    removeIncomingMessageClass(el) {
        if (el.classList.contains("incoming-message")) el.classList.remove("incoming-message");
    }

    updateUsersCountOnline(usersCountOnline) {
        const countUsers = this._getUsersCountElement();
        if (!countUsers) {
            console.warn("Users count element not found");
            return;
        }
        countUsers.textContent = usersCountOnline;
    }

    addPrivateChat(
        userIdTarget,
        usernameTarget,
        privateGroupId,
        openChatCallback,
        deleteChatCallback,
        incomingMessage = false
    ) {
        const listItem = this._createListItem(incomingMessage, userIdTarget, privateGroupId);
        const icon = this._createOnlineIcon();
        const button = this._createChatButton(userIdTarget, usernameTarget);
        const closeBtn = this._createCloseBtn();

        this._bindPrivateChatEvents(
            listItem,
            button,
            closeBtn,
            openChatCallback,
            deleteChatCallback
        );

        listItem.append(icon, button, closeBtn);

        this._appendPrivateChat(listItem);
    }

    addGroupChat(groupChatName, displayChatCallback) {
        const sideMenuGroups = this._getGroupChatsContainer();

        const groupContainer = document.createElement("div");
        groupContainer.classList.add("side-menu__group-chat--item", "margin-bottom-xxsmall");
        groupContainer.dataset.groupName = groupChatName.toLowerCase();

        const btnGroup = document.createElement("button");
        btnGroup.classList.add("side-menu__group-chat-btn");
        btnGroup.textContent = groupChatName;
        btnGroup.addEventListener("click", () => {
            this.removeIncomingMessageClass(groupContainer);
            this.toggleSideBar();
            displayChatCallback();
        })

        groupContainer.appendChild(btnGroup);

        sideMenuGroups.appendChild(groupContainer);
    }

    addIncomingMsgNotification(groupChatName) {
        const group = this._getChatByGroupName(groupChatName);
        if (!group) {
            console.warn(`Group chat not found: ${groupChatName}`);
            return;
        }

        this.addIncomingMessageClass(group);
    }

    setPrivateChatOffline(privateGroupId) {
        this.setPrivateChatStatus(privateGroupId, "offline");
    }

    setPrivateChatOnline(privateGroupId) {
        this.setPrivateChatStatus(privateGroupId, "online");
    }

    setPrivateChatStatus(privateGroupId, status) {
        const chatItem = this._getPrivateChatElement(privateGroupId);

        if (!chatItem) {
            console.warn(`Private chat not found for group ID: ${privateGroupId}`);
            return;
        }

        const statusIcon = this._getStatusIconElement(chatItem);

        if (!statusIcon) {
            console.warn(`Status icon not found for group ID: ${privateGroupId}`);
            return;
        }

        statusIcon.classList.toggle("online", status === "online");
        statusIcon.classList.toggle("offline", status === "offline");
    }

    _getUsersCountElement() {
        return this._parentElement.querySelector("#side-menu-header-count-users");
    }

    _getPrivateChatsContainer() {
        return this._parentElement.querySelector(
            ".side-menu__private-chats .side-menu__private-chats__list"
        );
    }

    _getGroupChatsContainer() {
        return this._parentElement.querySelector("#side-menu-groups");
    }

    _getPrivateChatElement(privateGroupId) {
        return this._parentElement.querySelector(
            `.side-menu__private-chats__list [data-group-name="${privateGroupId}"]`
        );
    }

    _getStatusIconElement(chatItem) {
        return chatItem.querySelector(".side-menu__connected-icon");
    }

    _getChatByGroupName(groupChatName) {
        return this._parentElement.querySelector(
            `[data-group-name="${groupChatName}"]`
        );
    }

    _createListItem(incomingMessage, userIdTarget, privateGroupId) {
        const li = document.createElement("li");
        li.className = "side-menu__private-chats__list-item margin-bottom-xxsmall";
        li.dataset.userIdTarget = userIdTarget;
        li.dataset.groupName = privateGroupId;
        if (incomingMessage) this.addIncomingMessageClass(li);

        return li;
    }

    _createOnlineIcon() {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("class", "side-menu__connected-icon margin-right-xxsmall online");
        svg.setAttribute("fill", "#000000");
        svg.setAttribute("viewBox", "0 0 32 32");

        const g1 = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g1.setAttribute("id", "SVGRepo_bgCarrier");
        g1.setAttribute("stroke-width", "0");

        const g2 = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g2.setAttribute("id", "SVGRepo_tracerCarrier");
        g2.setAttribute("stroke-linecap", "round");
        g2.setAttribute("stroke-linejoin", "round");

        const g3 = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g3.setAttribute("id", "SVGRepo_iconCarrier");

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", "16");
        circle.setAttribute("cy", "16");
        circle.setAttribute("r", "16");

        g3.appendChild(circle);
        svg.append(g1, g2, g3);

        return svg;
    }

    _createChatButton(userIdTarget, usernameTarget, openChatCallBack) {
        const button = document.createElement("button");
        button.className = "side-menu__private-chats__list-item--link";
        button.title = "online";
        button.textContent = `${usernameTarget}`;
        button.dataset.userIdTarget = userIdTarget;

        return button;
    }

    _createCloseBtn() {
        const svgNS = "http://www.w3.org/2000/svg";

        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("fill", "none");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("stroke", "#000000");

        const g1 = document.createElementNS(svgNS, "g");
        g1.setAttribute("id", "SVGRepo_bgCarrier");
        g1.setAttribute("stroke-width", "0");

        const g2 = document.createElementNS(svgNS, "g");
        g2.setAttribute("id", "SVGRepo_tracerCarrier");
        g2.setAttribute("stroke-linecap", "round");
        g2.setAttribute("stroke-linejoin", "round");

        const g3 = document.createElementNS(svgNS, "g");
        g3.setAttribute("id", "SVGRepo_iconCarrier");

        const circle = document.createElementNS(svgNS, "circle");
        circle.setAttribute("cx", "12");
        circle.setAttribute("cy", "12");
        circle.setAttribute("r", "10");
        circle.setAttribute("stroke", "#c21d03");
        circle.setAttribute("stroke-width", "1.5");

        const path = document.createElementNS(svgNS, "path");
        path.setAttribute("d", "M14.5 9.50002L9.5 14.5M9.49998 9.5L14.5 14.5");
        path.setAttribute("stroke", "#c21d03");
        path.setAttribute("stroke-width", "1.5");
        path.setAttribute("stroke-linecap", "round");

        g3.appendChild(circle);
        g3.appendChild(path);
        svg.append(g1, g2, g3);

        const btnEl = document.createElement("button");
        btnEl.className = "side-menu__private-chats__list-item--close";

        btnEl.appendChild(svg);

        return btnEl;
    }

    _bindPrivateChatEvents(
        listItem,
        button,
        closeBtn,
        openChatCallback,
        deleteChatCallback
    ) {
        button.addEventListener("click", () => {
            openChatCallback();
            this.toggleSideBar();
            this.removeIncomingMessageClass(listItem);
        });

        closeBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            event.preventDefault();

            listItem.remove();
            deleteChatCallback();
        });
    }

    _appendPrivateChat(listItem) {
        const container = this._getPrivateChatsContainer();

        if (!container) {
            console.warn("Private chats container not found");
            return;
        }

        container.appendChild(listItem);
    }

}

export default SideBarView;
