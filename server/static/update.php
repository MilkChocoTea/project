<?php
session_start();
$dsn = "pgsql:host=localhost;port=5432;dbname=arm;";
$user = "mct";
$password = "00123";

try {
    $pdo = new PDO($dsn, $user, $password, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        $machine_id = trim($_POST["machine_id"] ?? '');
        $machine_state = $_POST["machine_state"] ?? '';

        // 基本欄位檢查
        if (empty($machine_id) || !is_numeric($machine_state)) {
            http_response_code(400);
            echo "缺少必要欄位";
            exit;
        }

        // 執行更新
        $stmt = $pdo->prepare("UPDATE machines SET machine_state = :state,machine_statetime = NOW() WHERE machine_id = :id");
        $stmt->execute([
            'state' => $machine_state,
            'id' => $machine_id
        ]);

        echo "更新成功 ✅";
    } else {
        http_response_code(405);
        echo "只允許 POST";
    }
} catch (PDOException $e) {
    http_response_code(500);
    echo "資料庫錯誤：" . $e->getMessage();
}
?>
