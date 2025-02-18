<?php 
$datas = [
    [
        'staff_id' => 'mct030',
        'staff_name' => 'mct',
        'username' => 'MCT',
        'position' => 'none',
        'department' => 'ksu',
        'contact_info' => 'line',
        'status' => 'none',
        'create_at' => '2025/01/18',
        'password_hash' => 'mct123',
        'schedule' => 'none'
    ]
]
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
    <div class="list"><table>
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
        <?php foreach ($datas as $data) : ?>
            <tr>
                <td><?php echo $data['staff_id']; ?></td>
                <td><?php echo $data['staff_name']; ?></td>
                <td><?php echo $data['username']; ?></td>
                <td><?php echo $data['position']; ?></td>
                <td><?php echo $data['department']; ?></td>
                <td><?php echo $data['contact_info']; ?></td>
                <td><?php echo $data['status']; ?></td>
                <td><?php echo $data['create_at']; ?></td>
                <td><?php echo $data['password_hash']; ?></td>
                <td><?php echo $data['schedule']; ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
</body>
</html>