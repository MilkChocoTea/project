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