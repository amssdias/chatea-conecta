// Avatars are drawn from the nickname alone. The server never sends a colour,
// so both the rail (sideBarView) and the conversation (chatView) have to reach
// the same answer for the same person - otherwise the same nickname would be
// green in one place and blue in the other. Hence one helper, imported twice.

// Six tints, matching .chat__message-avatar--N / .side-menu__avatar--N in
// layout/_chat.scss. Change the count here and the SCSS loop together.
export const AVATAR_VARIANTS = 6;

export function avatarVariant(username) {
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = (hash * 31 + username.charCodeAt(i)) >>> 0;
    }
    return (hash % AVATAR_VARIANTS) + 1;
}

export function avatarInitial(username) {
    return (username || "?").charAt(0).toUpperCase();
}
