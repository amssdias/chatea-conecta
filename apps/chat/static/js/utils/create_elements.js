export function convertLinksToAnchors(inputString) {
    const urlRegex = /((https?:\/\/|www\.)[^\s]+)/g;
    return inputString.replace(urlRegex, (url) => {
        const href = url.startsWith("http") ? url : `http://${url}`;
        return `<a href="${href}" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });
};
