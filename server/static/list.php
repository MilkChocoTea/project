<?php
$api_url = "http://localhost:3000/machines"; // PostgREST API
$response = file_get_contents($api_url);
$data = json_decode($response, true);
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC&display=swap');
        * {
            margin: 0;
            padding: 0;
            list-style: none;
        }
        html, body {
            height: 100%; width: 100%;
            font-family: 'Noto Sans TC', sans-serif;
        }
        .list{
            text-align: center;
            font-size: 24px;
        }
        .table{
            margin: 0 auto;
            border: 1px;
        }
    </style>
</head>
<body>
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
</body>
</html>