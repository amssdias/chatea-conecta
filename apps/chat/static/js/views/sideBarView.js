class SideBarView {

    _parentElement = document.getElementById("side-menu");

    constructor(username) {
        this._username = username;
    }

    hideSideBar() {
        this._parentElement.classList.toggle("open-side-menu");
    }

    getPrivateChat(privateGroupId) {
        return this._parentElement.querySelector(
            `.side-menu__private-chats__list [data-group-name="${privateGroupId}"]`
        );
    }

    getStatusIcon(chatItem) {
        return chatItem.querySelector(".side-menu__connected-icon");
    }

    addIncomingMessageClass(el) {
        el.classList.add("incoming-message");
    }

    removeIncomingMessageClass(el) {
        if (el.classList.contains("incoming-message")) el.classList.remove("incoming-message");
    }

    updateUsersCountOnline(usersCountOnline) {
        const countUsers = this._parentElement.querySelector("#side-menu-header-count-users");
        countUsers.innerHTML = usersCountOnline;
    }

    addPrivateChat(userIdTarget, usernameTarget, privateChatMappgingId, openChatCallBack, deleteChatCallBack, incomingMessage=false) {
        const listItem = this._createListItem(incomingMessage, userIdTarget, privateChatMappgingId);
        const icon = this._createOnlineIcon();
        const button = this._createChatButton(userIdTarget, usernameTarget, openChatCallBack);
        const closeBtnEl = this._createCloseBtn();
        closeBtnEl.addEventListener("click", function(e) {
            e.stopPropagation();
            e.preventDefault();

            listItem.remove();

            deleteChatCallBack();
        })

        listItem.appendChild(icon);
        listItem.appendChild(button);
        listItem.appendChild(closeBtnEl);

        const container = this._parentElement.querySelector(".side-menu__private-chats .side-menu__private-chats__list");
        container.appendChild(listItem);
    }

    addGroupChat(groupChatName, displayChatCallBack) {
        const sideMenuGroups = this._parentElement.querySelector("#side-menu-groups");

        const groupContainer = document.createElement("div");
        groupContainer.classList.add("side-menu__group-chat--item", "margin-bottom-xxsmall");
        groupContainer.dataset.groupName = groupChatName.toLowerCase();

        const btnGroup = document.createElement("button");
        btnGroup.classList.add("side-menu__group-chat-btn");
        btnGroup.textContent = groupChatName;
        btnGroup.addEventListener("click", () => {
            this.removeIncomingMessageClass(groupContainer);
            this.hideSideBar();
            displayChatCallBack();
        })

        groupContainer.appendChild(btnGroup);

        sideMenuGroups.appendChild(groupContainer);
    }

    addIncomingMsgNotification(groupChatName) {
        let group = this._parentElement.querySelector(`[data-group-name=${groupChatName}]`);
        this.addIncomingMessageClass(group);
    }

    setPrivateChatOffline(privateGroupId) {
        this.setPrivateChatStatus(privateGroupId, "offline");
    }

    setPrivateChatOnline(privateGroupId) {
        this.setPrivateChatStatus(privateGroupId, "online");
    }

    setPrivateChatStatus(privateGroupId, status) {
        const chatItem = this.getPrivateChat(privateGroupId);

        if (!chatItem) {
            console.warn(`Private chat not found for group ID: ${privateGroupId}`);
            return;
        }

        const statusIcon = this.getStatusIcon(chatItem);

        if (!statusIcon) {
            console.warn(`Status icon not found for group ID: ${privateGroupId}`);
            return;
        }

        statusIcon.classList.toggle("online", status === "online");
        statusIcon.classList.toggle("offline", status === "offline");
    }

    _createListItem(incomingMessage, userIdTarget, privateChatMappgingId) {
        const li = document.createElement("li");
        li.className = "side-menu__private-chats__list-item margin-bottom-xxsmall";
        li.dataset.userIdTarget = userIdTarget;
        li.dataset.groupName = privateChatMappgingId;
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
        button.textContent = `🧑 ${usernameTarget}`;

        button.addEventListener("click", () => {
            openChatCallBack();
            this.hideSideBar();

            const li = button.parentElement;
            this.removeIncomingMessageClass(li);
        });

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

}

export default SideBarView;
