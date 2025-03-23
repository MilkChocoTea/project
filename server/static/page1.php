<?php
session_start();
ini_set('session.gc_maxlifetime', 600);
session_set_cookie_params(600);
if (!isset($_SESSION['username'])) {
    header("Location: logout.php");
    exit();
}
$pages = [
    [
        'label' => '機台們',
        'src' => 'list.php'
    ],
    [
        'label' => '貨物們',
        'src' => 'item.php'
    ],
    [
        'label' => '人們',
        'src' => 'staff.php'
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
            background-repeat: repeat;
            background-size: auto;
            background-attachment: fixed;
            backdrop-filter: blur(6px);
            display: flex;
            justify-content: center;
        }
        .side {
            height: 95%; width: 12%;
            background: linear-gradient(0deg,rgba(0,234,249,1)55%,rgba(0,201,255,1)100%);
            border-radius: 0px 10px 20px 0px;
            color: white;
            text-shadow: black 0.1em 0.1em 0.2em;
            display: flex;
            flex-direction:column;
            text-align: left;
            gap: 20px;
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
            width: 100%;
            color: white;
            background: linear-gradient(130deg,rgb(0, 162, 255)0%,rgba(0,234,249,1)55%,rgba(0,201,255,1)100%);
            margin-top: 5px;
            margin-bottom: 5px;
            border-radius: 8px;
            border: none;
            font-size: 20px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.5), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
        }
        .list {
            height: 100%; width: 88%;
        }
        .content {
            display: none;
        }
        .content.active {
            display: block;
        }
        iframe {
            height: 870px;
            width: 1650px;
            padding: 20px;
            border: none;
        }
        table {
            margin: 0 auto;
            border-collapse: collapse;
            width: 90%;
}
        th, td {
            padding: 10px;
            text-align: center;
        }
        th {
            background-color: #ddd;
        }
    </style>
</head>
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
            fetch(pageId)                         // 對 page1.php 或 page2.php 發出 GET 請求
                .then(response => response.text()) // 以文字 (HTML) 形式接收回應
                .then(html => {
                // 將回傳的 HTML 塞進 #content 區塊
                    document.getElementById('content').innerHTML = html;
                })
                .catch(error => {
                    console.error('載入失敗:', error);
                });
        }
    </script>
<body>
    <div class="side">
        <div class="wellcome"><?php echo "<h1>User：" . $_SESSION['username'] . "</h1>"; ?></div>
        <div class="side-page">
            <?php foreach ($pages as $page) : ?>
                <button class="btn" onclick="showpages('<?php echo $page['src']; ?>')"><?php echo $page['label']; ?></button>
            <?php endforeach; ?>
        </div>
        <div class="logout"><a href='logout.php'>Logout</a></div>
    </div>
    <div class="list" id="content">
    <?php
        $api_url = "http://localhost:3000/machines"; // PostgREST API
        $response = file_get_contents($api_url);
        $data = json_decode($response, true);
    ?>
    <h2>機器列表</h2>
    <table>
        <thead>
            <tr>
                <th>設備編號</th>
                <th>名稱</th>
                <th>位置</th>
                <th>IP</th>
                <th>狀態</th>
                <th>新增時間</th>
                <th>狀態時間</th>
                <th>備註</th>
            </tr>
        </thead>
        <tbody>
        <?php foreach ($data as $machine) : ?>
            <tr>
                <td><?php echo htmlspecialchars($machine['machine_id']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_name']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_location']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_ip']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_state']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_addtime']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_statetime']); ?></td>
                <td><?php echo htmlspecialchars($machine['machine_remark']); ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    </div>
</body>
</html>
