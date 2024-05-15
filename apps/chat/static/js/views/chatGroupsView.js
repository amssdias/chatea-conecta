class ChatGroupsView {

    _parentElement = document.getElementById("chat-groups");

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