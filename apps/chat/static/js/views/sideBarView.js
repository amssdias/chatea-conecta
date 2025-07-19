class SideBarView {

    _parentElement = document.getElementById("side-menu");

    constructor(username) {
        this._username = username;
    }

    updateUsersCountOnline(usersCountOnline) {
        const countUsers = this._parentElement.querySelector("#side-menu-header-count-users");
        countUsers.innerHTML = usersCountOnline;
    }

}

export default SideBarView;
