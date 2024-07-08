const protocol = window.location.protocol === "https:" ? "wss" : "ws";
export const SOCKET_URL = `${protocol}://${window.location.host}/ws/chat/`;
