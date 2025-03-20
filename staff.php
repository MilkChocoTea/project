<?php
$api_url = "http://localhost:3000/staff";
$response = file_get_contents($api_url);
$data = json_decode($response, true);
?>

<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>員工列表</title>
</head>
<body>
    <h2>員工列表</h2>
    <table border="1">
        <thead>
            <tr>
                <th>人員編號</th>
                <th>姓名</th>
                <th>帳號</th>
                <th>職務</th>
                <th>隸屬部門</th>
                <th>聯絡方式</th>
                <th>狀態</th>
                <th>建檔日期</th>
                <th>密碼</th>
                <th>排班資訊</th>
            </tr>
        </thead>
        <tbody>
        <?php foreach ($data as $staff) : ?>
            <tr>
                <td><?php echo htmlspecialchars($staff['staff_id']); ?></td>
                <td><?php echo htmlspecialchars($staff['staff_name']); ?></td>
                <td><?php echo htmlspecialchars($staff['username']); ?></td>
                <td><?php echo htmlspecialchars($staff['position']); ?></td>
                <td><?php echo htmlspecialchars($staff['department']); ?></td>
                <td><?php echo htmlspecialchars($staff['contact_info']); ?></td>
                <td><?php echo htmlspecialchars($staff['status']); ?></td>
                <td><?php echo htmlspecialchars($staff['create_at']); ?></td>
                <td>******</td>  <!-- 避免顯示密碼 -->
                <td><?php echo htmlspecialchars($staff['schedule']); ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
</body>
</html>
