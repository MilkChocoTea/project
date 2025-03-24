let timeout;
function logout() {
    window.location.href = 'logout.php';
}
function resetTimer() {
    clearTimeout(timeout);
    timeout = setTimeout(logout, 10 * 60 * 1000);
}
window.onload = resetTimer;
document.onmousemove = resetTimer;
document.onkeypress = resetTimer;
document.onclick = resetTimer;
document.onscroll = resetTimer;
let currentPage = 'machine.php';
function showpages(pageId) {
    currentPage = pageId;
    fetch(pageId).then(response => response.text()).then(html => {
            document.getElementById('content').innerHTML = html;
        }).catch(error => {
            console.error('載入失敗:', error);
        });
}
window.onload = () => {
    showpages(currentPage);
};
setInterval(() => {showpages(currentPage);}, 3000);