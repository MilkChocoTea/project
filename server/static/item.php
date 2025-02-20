<?php 
$datas = [
    [
        'item_id' => 'mct030',
        'item_name' => 'mct',
        'category' => 'MCT',
        'quantity' => 'none',
        'unit' => 'ksu',
        'unit_cost' => 'line',
        'location' => 'none',
        'reorder_level' => '2025/01/18',
        'expiry_date' => 'mct123',
        'supplier' => 'none',
        'note' => 'none',
        'last_update' => 'none'
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
            margin: 0 auto;
            border: 1px;
        }
    </style>
</head>
<body>
    <div class="list"><table>
        <thead>
            <tr>
                <th>品項編號</th>
                <th>品項名稱</th>
                <th>品項類別</th>
                <th>數量</th>
                <th>單位</th>
                <th>單價</th>
                <th>存放位置</th>
                <th>安全庫存</th>
                <th>有效日期</th>
                <th>供應商資訊</th>
                <th>備註</th>
                <th>最後更新時間</th>
           </tr>
        </thead>
        <tbody>
        <?php foreach ($datas as $data) : ?>
            <tr>
                <td><?php echo $data['item_id']; ?></td>
                <td><?php echo $data['item_name']; ?></td>
                <td><?php echo $data['category']; ?></td>
                <td><?php echo $data['quantity']; ?></td>
                <td><?php echo $data['unit']; ?></td>
                <td><?php echo $data['unit_cost']; ?></td>
                <td><?php echo $data['location']; ?></td>
                <td><?php echo $data['reorder_level']; ?></td>
                <td><?php echo $data['expiry_date']; ?></td>
                <td><?php echo $data['supplier']; ?></td>
                <td><?php echo $data['note']; ?></td>
                <td><?php echo $data['last_update']; ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
</body>
</html>