class ChatGroupsView {

    _parentElement = document.getElementById("chat-groups");
    _groupsChats = "groupsChats";
    _groupsOnline = "groupsOnline";
    _groupTab = false;

    openGroupChatsList() {

        // Get all groups and make sure all of them visible
        const groups = document.getElementById("chat-app-groups");
        const allGroups = groups.querySelectorAll(":scope > li");
        allGroups.forEach(
            group => group.classList.contains("hide") ? group.classList.remove("hide") : null
        );

        // If groups tab is closed we open it
        if (!this._groupTab || this._groupTab !== this._groupsChats) {
            this._parentElement.classList.remove("hide");
            this._groupTab = this._groupsChats;
        } else {
            this._parentElement.classList.add("hide");
            this._groupTab = false;
        }

        if (window.innerWidth <= 600) {
            if (this._parentElement.classList.contains("hide")) {
                document.querySelector(".chat-container").classList.remove("hide");
            } else {
                document.querySelector(".chat-container").classList.add("hide");
            };

        };

    }

    openOnlineGroupsList() {

        // Get all groups and filter the ones that are online/active
        const groups = document.getElementById("chat-app-groups");
        const allGroups = groups.querySelectorAll(":scope > li");
        allGroups.forEach(group => {
            const isgroupOffline = group.querySelector("svg").classList.contains("offline");
            if (isgroupOffline) {
                group.classList.add("hide");
            }
        });

        // Check if the groups tab is close then we open it
        if (!this._groupTab || this._groupTab !== this._groupsOnline) {
            this._parentElement.classList.remove("hide");
            this._groupTab = this._groupsOnline;
        } else {
            this._parentElement.classList.add("hide");
            this._groupTab = false;
        }

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