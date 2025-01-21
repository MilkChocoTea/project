<?php
ini_set('session.gc_maxlifetime', 600);
session_set_cookie_params(600);
session_start();
if (!isset($_SESSION['username'])) {
    header("Location: logout.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="index.ico" type="image/x-icon"/>
    <title>機械手臂倉儲系統 - 監控系統</title>
    <script>
        let timeout;
        function logout() {
            window.location.href = 'logout.php';
        }
        function resetTimer() {
            clearTimeout(timeout);
            timeout = setTimeout(logout, 5 * 60 * 1000);
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
            background-image: url('page1.jpg');
            background-repeat: no-repeat;
            background-size: cover;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
        }
        .top {
            height: 10%; width: 75%;
            padding: 20px;
            backdrop-filter: invert(90%);
            color: white;
            text-shadow: black 0.1em 0.1em 0.2em;
            display: flex;
            text-align: left;
            gap: 20px;
            justify-content: flex-end;
        }
        .top h1{
            font-size: 48px;
        }
        .top a {
            text-decoration: none;
            color: white;
            font-size: 48px;
        }
        .list{
            padding: 20px;
            height: 90%; width: 75%;
            text-align: center;
            backdrop-filter: blur(6px);
            font-size: 24px;
        }
        .table{
            border: 1px;
        }
    </style>
</head>
<body>
    <div class="top">
        <div class="wellcome"><?php echo "<h1>Wellcome，" . $_SESSION['username'] . "！</h1>"; ?></div>
        <div class="logout"><a href='logout.php'>Logout</a></div>
    </div>
    <div class="list"><table>
        <thead>
            <tr>
                <th>001</th>
                <th>002</th>
                <th>003</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>010</td>
                <td>020</td>
                <td>030</td>
            </tr>
        </tbody>
    </table></div>
</body>
</html>
