export function appendTextWithLinks(parentElement, inputString) {
    const urlRegex = /((https?:\/\/|www\.)[^\s]+)/g;

    let lastIndex = 0;

    inputString.replace(urlRegex, (url, _match2, _match3, offset) => {
        // Add normal text before the URL
        if (offset > lastIndex) {
            parentElement.appendChild(
                document.createTextNode(inputString.slice(lastIndex, offset))
            );
        }

        const href = url.startsWith("http") ? url : `http://${url}`;

        const anchor = document.createElement("a");
        anchor.href = href;
        anchor.target = "_blank";
        anchor.rel = "noopener noreferrer";
        anchor.textContent = url;

        parentElement.appendChild(anchor);

        lastIndex = offset + url.length;

        return url;
    });

    // Add remaining normal text after the last URL
    if (lastIndex < inputString.length) {
        parentElement.appendChild(
            document.createTextNode(inputString.slice(lastIndex))
        );
    }
}
