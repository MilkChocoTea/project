<?php
$api_url = "http://localhost:3000/item"; // PostgREST API
$response = file_get_contents($api_url);
$data = json_decode($response, true);
?>
<h2>貨物列表</h2>
    <table>
        <thead>
            <tr>
                <th>編號</th>
                <th>名稱</th>
                <th>類別</th>
                <th>數量</th>
                <th>存放位置</th>
                <th>單價</th>
                <th>供應商</th>
                <th>入庫時間</th>
                <th>出庫時間</th>
                <th>備註</th>
                <th>資料更新時間</th>
            </tr>
        </thead>
        <tbody id="item-table-body">
        <?php foreach ($data as $machine) : ?>
            <tr>
                <td><?php echo htmlspecialchars($machine['item_id']); ?></td>
                <td><?php echo htmlspecialchars($machine['item_name']); ?></td>
                <td><?php echo htmlspecialchars($machine['category']); ?></td>
                <td><?php echo htmlspecialchars($machine['quantity']); ?></td>
                <td><?php echo htmlspecialchars($machine['location']); ?></td>
                <td><?php echo htmlspecialchars($machine['unit_price']); ?></td>
                <td><?php echo htmlspecialchars($machine['supplier']); ?></td>
                <td><?php echo htmlspecialchars($machine['warehouse_time']); ?></td>
                <td><?php echo htmlspecialchars($machine['shipping_time']); ?></td>
                <td><?php echo htmlspecialchars($machine['remark']); ?></td>
                <td><?php echo htmlspecialchars($machine['last_update']); ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>