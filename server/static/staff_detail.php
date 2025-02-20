<?php 
$staffId = $_GET['id'] ?? '';
$datas = [
    [
        'staff_id'      => 'E001',
        'staff_name'    => 'Alice Chang',
        'username'      => 'alice',
        'role'          => 'Operator',
        'department'    => 'Manufacturing',
        'contact_info'  => 'alice@example.com / 0912-345-678',
        'status'        => 'Active',
        'hire_date'     => '2024-10-01',
        'password_hash' => 'some_hash_value',
        'schedule'      => 'Day Shift (08:00 - 17:00)'
    ],
    [
        'staff_id'      => 'E002',
        'staff_name'    => 'Bob Wang',
        'username'      => 'bobw',
        'role'          => 'Maintenance Engineer',
        'department'    => 'Maintenance',
        'contact_info'  => 'bob@example.com / 0987-654-321',
        'status'        => 'Active',
        'hire_date'     => '2023-06-15',
        'password_hash' => 'another_hash_value',
        'schedule'      => 'Night Shift (20:00 - 05:00)'
    ]
];
$data = null;
foreach ($datas as $d) {
    if ($d['staff_id'] === $staffId) {
        $data = $d;
        break;
    }
}
?>
<!DOCTYPE html>
<html lang="en">
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
            border: 1px;
        }
    </style>
</head>
<body>
    <div class="list">
    <?php if ($data): ?>
        <h1>人員詳細資料</h1>
        <table>
            <tr>
                <th>人員編號</th>
                <td><?php echo $data['staff_id']; ?></td>
            </tr>
            <tr>
                <th>姓名</th>
                <td><?php echo $data['staff_name']; ?></td>
            </tr>
            <tr>
                <th>帳號</th>
                <td><?php echo $data['username']; ?></td>
            </tr>
                <tr>
                <th>職位</th>
                <td><?php echo $data['role']; ?></td>
            </tr>
                <tr>
                <th>隸屬部門</th>
                <td><?php echo $data['department']; ?></td>
            </tr>
                <tr>
                <th>聯絡方式</th>
                <td><?php echo $data['contact_info']; ?></td>
            </tr>
                <tr>
                <th>狀態</th>
                <td><?php echo $data['status']; ?></td>
            </tr>
                <tr>
                <th>入職日期</th>
                <td><?php echo $data['hire_date']; ?></td>
            </tr>
                <tr>
                <th>密碼雜湊</th>
                <td><?php echo $data['password_hash']; ?></td>
            </tr>
                <tr>
                <th>排班資訊</th>
                <td><?php echo $data['schedule']; ?></td>
            </tr>
        </table>
        <?php else: ?>
            <div class="no-data">
                查無此人員資料，請確認網址參數是否正確。
            </div>
        <?php endif; ?>
    </div>
    <a href="staff.php">back</a>
</body>
</html>
