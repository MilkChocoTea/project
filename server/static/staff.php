<?php 
$datas = [
    [
        'staff_id'      => 'E001',
        'staff_name'    => 'Alice Chang',
        'username'      => 'alice',
        'role'          => 'Operator'
    ],
    [
        'staff_id'      => 'E002',
        'staff_name'    => 'Bob Wang',
        'username'      => 'bobw',
        'role'          => 'Maintenance Engineer'
    ]
];
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
        <table>
            <thead>
                <tr>
                    <th>人員編號</th>
                    <th>姓名</th>
                    <th>帳號</th>
                    <th>職位</th>
                    <th>更多</th>
                </tr>
            </thead>
            <tbody>
            <?php foreach ($datas as $data) : ?>
                <tr>
                    <td><?php echo $data['staff_id']; ?></td>
                    <td><?php echo $data['staff_name']; ?></td>
                    <td><?php echo $data['username']; ?></td>
                    <td><?php echo $data['role']; ?></td>
                    <td><a href="staff_detail.php?id=<?php echo urlencode($data['staff_id']); ?>" class="btn-detail">go!</a></td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</body>
</html>
