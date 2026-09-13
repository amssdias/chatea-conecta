import {MAX_FREE_PRIVATE_CHATS} from "../config.js";
import {avatarInitial, avatarVariant} from "../utils/avatar.js";

class SideBarView {

    _parentElement = document.getElementById("side-menu");
    _scrim = document.getElementById("side-menu-scrim");

    constructor(isPro = false, strings = {}) {
        this._isPro = isPro;
        this._strings = strings;
        // Set by the controller so the free-plan ceiling can be shown as a bar
        // inside the conversation instead of a browser alert.
        this.onLimitReached = null;
        // Also set by the controller: closing a row has to free the slot on the
        // server too, otherwise its ledger keeps counting the closed chat.
        this.onPrivateChatClosed = null;

        this._refreshPrivateChatsSummary();
    }

    // =========================
    // Drawer
    // =========================

    // On desktop the rail is a permanent column and .open-side-menu does
    // nothing; below 900px the same class is what slides it in. Both states
    // go through here so the scrim can never fall out of step with the rail.
    toggleSideBar() {
        this._setSideBarOpen(!this._parentElement.classList.contains("open-side-menu"));
    }

    openSideBar() {
        this._setSideBarOpen(true);
    }

    closeSideBar() {
        this._setSideBarOpen(false);
    }

    _setSideBarOpen(isOpen) {
        this._parentElement.classList.toggle("open-side-menu", isOpen);
        if (this._scrim) this._scrim.classList.toggle("open-side-menu", isOpen);
    }

    // =========================
    // Unread
    // =========================

    addIncomingMessageClass(el) {
        el.classList.add("incoming-message");
        this._bumpUnreadCount(el, 1);
    }

    removeIncomingMessageClass(el) {
        if (el.classList.contains("incoming-message")) el.classList.remove("incoming-message");
        this._resetUnreadCount(el);
    }

    // The socket has no unread counter, so the rail keeps its own: one per
    // message that arrived while the conversation was not the open one.
    _bumpUnreadCount(el, by) {
        const badge = el.querySelector(".side-menu__row-badge");
        if (!badge) return;

        const next = Number(el.dataset.unread || 0) + by;
        el.dataset.unread = String(next);
        badge.textContent = next > 99 ? "99+" : String(next);
        badge.classList.remove("hide");
    }

    _resetUnreadCount(el) {
        const badge = el.querySelector(".side-menu__row-badge");
        el.dataset.unread = "0";
        if (badge) {
            badge.textContent = "";
            badge.classList.add("hide");
        }
    }

    // =========================
    // Room / presence
    // =========================

    // Writes into every headcount on the page: the one under the nickname in
    // the rail and the pill in each conversation header.
    updateUsersCountOnline(usersCountOnline) {
        const counters = document.querySelectorAll(".js-online-count");
        if (!counters.length) {
            console.warn("Users count element not found");
            return;
        }
        counters.forEach((counter) => {
            counter.textContent = usersCountOnline;
        });
    }

    addGroupChat(groupChatName, displayChatCallback, {displayName, subtitle} = {}) {
        const sideMenuGroups = this._getGroupChatsContainer();

        const groupContainer = document.createElement("div");
        groupContainer.classList.add("side-menu__group-chat--item");
        groupContainer.dataset.groupName = groupChatName.toLowerCase();

        const btnGroup = document.createElement("button");
        btnGroup.type = "button";
        btnGroup.classList.add("side-menu__group-chat-btn");

        btnGroup.append(
            this._createRowText(
                displayName || groupChatName,
                subtitle || "",
                "side-menu__row-name--room"
            ),
            this._createLivePill(),
            this._createBadge()
        );

        btnGroup.addEventListener("click", () => {
            this.removeIncomingMessageClass(groupContainer);
            this.setActiveChat(groupContainer.dataset.groupName);
            this.closeSideBar();
            displayChatCallback();
        });

        groupContainer.appendChild(btnGroup);

        sideMenuGroups.appendChild(groupContainer);
        this.setActiveChat(groupContainer.dataset.groupName);
    }

    addIncomingMsgNotification(groupChatName) {
        const group = this._getChatByGroupName(groupChatName);
        if (!group) {
            console.warn(`Group chat not found: ${groupChatName}`);
            return;
        }

        this.addIncomingMessageClass(group);
    }

    // The rail row for whichever conversation is currently open. Without this
    // the rail gives no clue which of five rows you are actually reading.
    setActiveChat(groupChatName) {
        const rows = this._parentElement.querySelectorAll(
            ".side-menu__group-chat--item, .side-menu__private-chats__list-item"
        );

        rows.forEach((row) => {
            row.classList.toggle("is-active", row.dataset.groupName === groupChatName);
        });
    }

    // =========================
    // Private chats
    // =========================

    // Adds the row only. Unread state is owned by addIncomingMsgNotification,
    // which every incoming message goes through - including the one that
    // caused this row to be created.
    addPrivateChat(
        userIdTarget,
        usernameTarget,
        privateGroupId,
        openChatCallback,
        deleteChatCallback
    ) {
        const listItem = this._createListItem(userIdTarget, privateGroupId);
        const button = this._createChatButton(userIdTarget, usernameTarget);
        const closeBtn = this._createCloseBtn();

        this._bindPrivateChatEvents(
            listItem,
            button,
            closeBtn,
            openChatCallback,
            deleteChatCallback,
            usernameTarget
        );

        listItem.append(button, closeBtn);

        this._appendPrivateChat(listItem);
        this._refreshPrivateChatAvailability();
        this._refreshPrivateChatsSummary();
    }

    canOpenPrivateChat(privateGroupId) {
        const { isOpenable } = this._getPrivateChatAvailability(privateGroupId);
        return isOpenable;
    }

    showPrivateChatLimitMessage(usernameTarget = "", message = "") {
        if (typeof this.onLimitReached === "function") {
            this.onLimitReached(usernameTarget, message);
            return;
        }
        window.alert(message || privateChatLimitMessage);
    }

    removePrivateChat(privateGroupId) {
        const chat = this._getPrivateChatElement(privateGroupId);
        if (!chat) return;

        chat.remove();
        this._refreshPrivateChatAvailability();
        this._refreshPrivateChatsSummary();
    }

    // The one line of the last message, under the nickname, so the rail says
    // what a conversation is about rather than only who it is with.
    setPrivateChatPreview(privateGroupId, message, isCurrentUser = false) {
        const chat = this._getPrivateChatElement(privateGroupId);
        if (!chat) return;

        const preview = chat.querySelector(".side-menu__row-preview");
        if (!preview) return;

        preview.textContent = isCurrentUser
            ? `${this._strings.youSaid || "You:"} ${message}`
            : message;
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

    // =========================
    // Private DOM selectors
    // =========================

    _getPrivateChatsContainer() {
        return this._parentElement.querySelector(
            ".side-menu__body .side-menu__private-chats__list"
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
        return chatItem.querySelector(".side-menu__row-dot");
    }

    _getChatByGroupName(groupChatName) {
        return this._parentElement.querySelector(
            `[data-group-name="${groupChatName}"]`
        );
    }

    // =========================
    // Private row construction
    // =========================

    _createListItem(userIdTarget, privateGroupId) {
        const li = document.createElement("li");
        li.className = "side-menu__private-chats__list-item";
        li.dataset.userIdTarget = userIdTarget;
        li.dataset.groupName = privateGroupId;
        li.dataset.unread = "0";

        return li;
    }

    // A tinted disc with the nickname's initial, plus the presence dot that
    // used to be a standalone SVG bullet next to the name.
    _createAvatar(usernameTarget) {
        const avatar = document.createElement("span");
        avatar.className = `side-menu__avatar side-menu__avatar--${avatarVariant(usernameTarget)}`;
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = avatarInitial(usernameTarget);

        const dot = document.createElement("span");
        dot.className = "side-menu__row-dot online";

        avatar.appendChild(dot);

        return avatar;
    }

    _createRowText(name, preview, nameModifier = "") {
        const text = document.createElement("span");
        text.className = "side-menu__row-text";

        const nameEl = document.createElement("span");
        nameEl.className = "side-menu__row-name";
        if (nameModifier) nameEl.classList.add(nameModifier);
        nameEl.textContent = name;

        const previewEl = document.createElement("span");
        previewEl.className = "side-menu__row-preview";
        previewEl.textContent = preview;

        text.append(nameEl, previewEl);

        return text;
    }

    _createBadge() {
        const badge = document.createElement("span");
        badge.className = "side-menu__row-badge hide";
        return badge;
    }

    _createLivePill() {
        const pill = document.createElement("span");
        pill.className = "side-menu__live";

        const dot = document.createElement("span");
        dot.className = "side-menu__dot online";

        pill.append(dot, document.createTextNode(this._strings.live || "live"));

        return pill;
    }

    _createChatButton(userIdTarget, usernameTarget) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "side-menu__private-chats__list-item--link";
        button.dataset.userIdTarget = userIdTarget;

        button.append(
            this._createAvatar(usernameTarget),
            this._createRowText(usernameTarget, this._strings.noMessagesYet || ""),
            this._createBadge()
        );

        return button;
    }

    _createCloseBtn() {
        const btnEl = document.createElement("button");
        btnEl.type = "button";
        btnEl.className = "side-menu__private-chats__list-item--close";
        btnEl.setAttribute("aria-label", this._strings.closeChat || "Close this private chat");
        btnEl.textContent = "×";

        return btnEl;
    }

    _bindPrivateChatEvents(
        listItem,
        button,
        closeBtn,
        openChatCallback,
        deleteChatCallback,
        usernameTarget
    ) {
        button.addEventListener("click", () => {
            if (!this.canOpenPrivateChat(listItem.dataset.groupName)) {
                this.showPrivateChatLimitMessage(usernameTarget);
                return;
            }
            openChatCallback();
            this.setActiveChat(listItem.dataset.groupName);
            this.closeSideBar();
            this.removeIncomingMessageClass(listItem);
        });

        closeBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            event.preventDefault();

            const {userIdTarget, groupName} = listItem.dataset;

            listItem.remove();
            this._refreshPrivateChatAvailability();
            this._refreshPrivateChatsSummary();
            deleteChatCallback();

            if (typeof this.onPrivateChatClosed === "function") {
                this.onPrivateChatClosed(userIdTarget, groupName);
            }
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

    // "2 of 3" on a free plan, "2 open" on PRO, and the dashed placeholder
    // while there are none at all.
    _refreshPrivateChatsSummary() {
        const container = this._getPrivateChatsContainer();
        if (!container) return;

        const count = container.querySelectorAll(".side-menu__private-chats__list-item").length;

        const counter = this._parentElement.querySelector("#side-menu-private-count");
        if (counter) {
            const template = this._isPro
                ? this._strings.privateCountPro
                : this._strings.privateCountFree;
            counter.textContent = (template || "%(count)s").replace("%(count)s", count);
        }

        const empty = this._parentElement.querySelector("#side-menu-private-empty");
        if (empty) empty.classList.toggle("hide", count > 0);
    }

    _refreshPrivateChatAvailability() {
        const container = this._getPrivateChatsContainer();
        if (!container) return;

        const chats = container.querySelectorAll(".side-menu__private-chats__list-item");
        chats.forEach((chat, index) => {
            const isLocked = !this._isPro && index >= MAX_FREE_PRIVATE_CHATS;
            chat.dataset.locked = isLocked ? "true" : "false";
            chat.classList.toggle("is-locked", isLocked);

            let lockIndicator = chat.querySelector(".side-menu__private-chats__list-item--lock");

            if (!lockIndicator) {
                lockIndicator = this._createLockIndicator();
                chat.insertBefore(lockIndicator, chat.lastElementChild);
            }

            lockIndicator.classList.toggle("hide", !isLocked);
        });
    }

    _createLockIndicator() {
        const svgNS = "http://www.w3.org/2000/svg";

        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("fill", "none");
        svg.setAttribute("aria-hidden", "true");

        const body = document.createElementNS(svgNS, "rect");
        body.setAttribute("x", "4");
        body.setAttribute("y", "10");
        body.setAttribute("width", "16");
        body.setAttribute("height", "10");
        body.setAttribute("rx", "2");
        body.setAttribute("stroke", "currentColor");
        body.setAttribute("stroke-width", "1.6");

        const shackle = document.createElementNS(svgNS, "path");
        shackle.setAttribute("d", "M8 10V7.5a4 4 0 1 1 8 0V10");
        shackle.setAttribute("stroke", "currentColor");
        shackle.setAttribute("stroke-width", "1.6");
        shackle.setAttribute("stroke-linecap", "round");

        svg.append(body, shackle);

        const span = document.createElement("span");
        span.className = "side-menu__private-chats__list-item--lock hide";
        span.appendChild(svg);

        return span;
    }

    _getPrivateChatAvailability(privateGroupId) {
        const container = this._getPrivateChatsContainer();
        if (!container) {
            return { isOpenable: false, isKnownChat: false };
        }

        const chats = Array.from(
            container.querySelectorAll(".side-menu__private-chats__list-item")
        );

        const chatIndex = chats.findIndex((chat) => chat.dataset.groupName === privateGroupId);
        const isKnownChat = chatIndex >= 0;

        if (isKnownChat) {
            return {
                isOpenable: this._isPro || chatIndex < MAX_FREE_PRIVATE_CHATS,
                isKnownChat: true,
            };
        }

        return {
            isOpenable: this._isPro || chats.length < MAX_FREE_PRIVATE_CHATS,
            isKnownChat: false,
        };
    }


}

export default SideBarView;
