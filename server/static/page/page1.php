<?php
ini_set('session.gc_maxlifetime', 600);
session_set_cookie_params(600);
session_start();

if (!isset($_SESSION['username'])) {
    header("Location: ../../index.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" href="../photo/index.ico" type="image/x-icon"/>
        <title>機械手臂倉儲系統 - 監控系統</title>
	    <script type="text/javascript" language="JavaScript" src="../js/page1.js"></script>
        <script>
            let timeout;
            function logout() {
                window.location.href = 'logout.php';
            }
            function resetTimer() {
                clearTimeout(timeout);
                timeout = setTimeout(logout, 10 * 60 * 1000);  // 10 分鐘
            }
            window.onload = resetTimer;
            document.onmousemove = resetTimer;
            document.onkeypress = resetTimer;
            document.onclick = resetTimer;
            document.onscroll = resetTimer;
        </script>
    </head>
    <body>
        <?php echo "<h1>歡迎，" . $_SESSION['username'] . "！</h1>"; ?>
        <a href='logout.php'>登出</a>
    </body>
</html>
