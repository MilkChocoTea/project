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
    <script>
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
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC&display=swap');
        * {
            margin: 0;
            padding: 0;
            list-style: none;
        }
        html, body {
            height: 100%;
            font-family: 'Noto Sans TC', sans-serif;
        }
        body {
            background-image: url('../photo/page1.jpg');
            background-repeat: no-repeat;
            background-size: cover;
            display: flex;
        }
        .side {
            height: 100%; width: 15%;
            backdrop-filter: invert(90%);
            color: white;
            display: flex;
        }
        .side a {
            text-decoration: none;
            margin-left: auto;
            margin-right: 10px;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="side">
        <div><?php echo "<h1>歡迎，" . $_SESSION['username'] . "！</h1>"; ?></div>
        <div><a href='logout.php'>登出</a></div>
    </div>
</body>
</html>
