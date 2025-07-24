class SideBarView {

    _parentElement = document.getElementById("side-menu");

    constructor(username) {
        this._username = username;
    }

    hideSideBar() {
        this._parentElement.classList.toggle("open-side-menu");
    }

    updateUsersCountOnline(usersCountOnline) {
        const countUsers = this._parentElement.querySelector("#side-menu-header-count-users");
        countUsers.innerHTML = usersCountOnline;
    }

    addPrivateChat(username, openChatCallBack) {
        const listItem = this._createListItem();
        const icon = this._createOnlineIcon();
        const button = this._createChatButton(username, openChatCallBack);

        listItem.appendChild(icon);
        listItem.appendChild(button);

        const container = this._parentElement.querySelector(".side-menu__private-chats .side-menu__private-chats__list");
        container.appendChild(listItem);
    }

    _createListItem() {
        const li = document.createElement("li");
        li.className = "side-menu__private-chats__list-item margin-bottom-xsmall";
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

    _createChatButton(username, openChatCallBack) {
        const button = document.createElement("button");
        button.className = "side-menu__private-chats__list-item--link";
        button.dataset.username = username;
        button.textContent = `🧑 ${username}`;

        button.addEventListener("click", () => {
            openChatCallBack();
            this.hideSideBar();
        });

        return button;
    }



}

export default SideBarView;
