class ChatGroupsView {

    _parentElement = document.getElementById("chat-groups");

    openGroupChatsList() {
        // Hide or show group chats
        this._parentElement.classList.toggle("hide");

        if (window.innerWidth <= 600) {
            if (this._parentElement.classList.contains("hide")) {
                document.querySelector(".chat-container").classList.remove("hide");
            } else {
                document.querySelector(".chat-container").classList.add("hide");
            };

        };
    }

    activateGroup(groupName) {
        const groupLi = this._parentElement.querySelector(`[data-group-name='${groupName}']`).parentElement;
        const svgIcon = groupLi.querySelector(".chat-app__group__connected");

        if (svgIcon.classList.contains("offline")) {
            svgIcon.classList.remove("offline");
        }
        svgIcon.classList.add("online");
    };

    selectedGroupChat(groupName) {
        const groupLi = this._parentElement.querySelector(`[data-group-name='${groupName}']`).parentElement;

        const previousSelectedChat = this._parentElement.querySelector(".selected");
        if (previousSelectedChat) {
            previousSelectedChat.classList.remove("selected");
        };

        groupLi.classList.add("selected");
    }

};