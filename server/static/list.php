<?php 
$datas = [
    [
        'id' => 'test001',
        'name' => 'mct001',
        'state' => 'online',
        'time' => '2025/02/14',
        'location' => 'ksu',
        'remark' => 'none',
        'ip' => 'mct001.local',
    ],
    [
        'id' => 'test002',
        'name' => 'mct002',
        'state' => 'unline',
        'time' => '2025/02/18',
        'location' => 'ksu',
        'remark' => 'none',
        'ip' => 'mct002.local',
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
                <th>機台編號</th>
                <th>機台名稱</th>
                <th>狀態</th>
                <th>狀態更新時間</th>
                <th>位置</th>
                <th>備註</th>
                <th>IP</th>
           </tr>
        </thead>
        <tbody>
        <?php foreach ($datas as $data) : ?>
            <tr>
                <td><?php echo $data['id']; ?></td>
                <td><?php echo $data['name']; ?></td>
                <td><?php echo $data['state']; ?></td>
                <td><?php echo $data['time']; ?></td>
                <td><?php echo $data['location']; ?></td>
                <td><?php echo $data['remark']; ?></td>
                <td><?php echo $data['ip']; ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
</body>
</html>