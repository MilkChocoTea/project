<?php
$api_url = "http://localhost:3000/staff"; // PostgREST API
$response = file_get_contents($api_url);
$data = json_decode($response, true);
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" type="text/css" href="./pages.css">
</head>
<body>
    <h2>人員列表</h2>
    <table>
        <thead>
            <tr>
                <th>人員ID</th>
                <th>暱稱</th>
                <th>名稱</th>
                <th>職位</th>
                <th>部門</th>
                <th>日程表</th>
                <th>聯絡資訊</th>
                <th>密碼</th>
                <th>狀態</th>
                <th>創建於</th>
            </tr>
        </thead>
        <tbody>
        <?php foreach ($data as $machine) : ?>
            <tr>
                <td><?php echo htmlspecialchars($machine['staff_id']); ?></td>
                <td><?php echo htmlspecialchars($machine['staff_name']); ?></td>
                <td><?php echo htmlspecialchars($machine['username']); ?></td>
                <td><?php echo htmlspecialchars($machine['position']); ?></td>
                <td><?php echo htmlspecialchars($machine['department']); ?></td>
                <td><?php echo htmlspecialchars($machine['schedule']); ?></td>
                <td><?php echo htmlspecialchars($machine['contact_info']); ?></td>
                <td><?php echo htmlspecialchars($machine['password_hash']); ?></td>
                <td><?php echo htmlspecialchars($machine['status']); ?></td>
                <td><?php echo htmlspecialchars($machine['create_at']); ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
</body>
</html>