<?php
ini_set('session.gc_maxlifetime', 600);
session_set_cookie_params(600);
session_start();
if (!isset($_SESSION['username'])) {
    header("Location: logout.php");
    exit();
}
$pages = [
    [
        'id' => 'page1',
        'label' => '機台們',
        'src' => 'list.php'
    ],
    [
        'id' => 'page2',
        'label' => '人們',
        'src' => 'test.php'
    ]
];
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
            timeout = setTimeout(logout, 10 * 60 * 1000);
        }
        window.onload = resetTimer;
        document.onmousemove = resetTimer;
        document.onkeypress = resetTimer;
        document.onclick = resetTimer;
        document.onscroll = resetTimer;
        function showpages(pageId) {
            const contents = document.querySelectorAll('.content');
            contents.forEach((content) => {
                content.classList.remove('active');
            });
            const target = document.getElementById(pageId);
            if (target) {
                target.classList.add('active');
            }
        }
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
            backdrop-filter: blur(6px);
            background-size: cover;
            display: flex;
            justify-content: center;
        }
        .side {
            height: 100%; width: 12%;
            background: linear-gradient(0deg,rgba(0,234,249,1)55%,rgba(0,201,255,1)100%);
            border-radius: 0px 10px 20px 0px;
            color: white;
            text-shadow: black 0.1em 0.1em 0.2em;
            display: flex;
            flex-direction:column;
            text-align: left;
            gap: 20px;
        }
        .side-side {
            height: 100%; width: 100%;
            padding: 1em;
        }
        .side .wellcome {
            margin-bottom: 5px;
        }
        .side h1{
            font-size: 22px;
        }
        .side .logout {
            margin-top: 5px;
            margin-bottom: 5px;
        }
        .side a {
            text-decoration: none;
            color: white;
            background: linear-gradient(130deg,rgba(255, 52, 25,1)0%,rgba(255, 123, 0,1)55%,rgba(255, 51, 0,1)100%);
            border-radius: 8px;
            font-size: 20px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.5), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
        }
        .btn {
            width: 80%;
            color: white;
            background: linear-gradient(130deg,rgb(0, 162, 255)0%,rgba(0,234,249,1)55%,rgba(0,201,255,1)100%);
            margin-top: 5px;
            margin-bottom: 5px;
            border-radius: 8px;
            border: none;
            font-size: 20px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.5), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
        }
        .mid {
            height: 100%; width: 88%;
        }
        .content {
            display: none;
        }
        .content.active {
            display: block;
        }
        iframe {
            height: 100%; width: 95%;
            padding: 20px;
            border: none;
        }
    </style>
</head>
<body>
    <div class="side">
        <div class="side-side">
            <div class="wellcome"><?php echo "<h1>User：" . $_SESSION['username'] . "</h1>"; ?></div>
            <div class="side-page">
                <?php foreach ($pages as $page) : ?>
                    <button class="btn" onclick="showpages('<?php echo $page['id']; ?>')">
                        <?php echo $page['label']; ?>
                    </button>
                <?php endforeach; ?>
            </div>
            <div class="logout"><a href='logout.php'>Logout</a></div>
        </div>
    </div>
    <div class="mid">
        <?php foreach ($pages as $index => $page) : ?>
            <div id="<?php echo $page['id']; ?>" class="content <?php echo $index === 0 ? 'active' : ''; ?>">
                <iframe src="<?php echo $page['src']; ?>"></iframe>
            </div>
        <?php endforeach; ?>
    </div>
</body>
</html>
