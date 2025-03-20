<?php
$input_password = "00123"; // 你輸入的密碼
$stored_hash = '$2y$10$qQJ0nlu/QNNjHsnaVLz8l./Se1lZYdYkC6d.Gfs2gNnLvtG46aFpK'; // 從資料庫查詢到的 `password_hash`

echo "<h3>🔹 測試 `password_verify()`:</h3>";
var_dump(password_verify($input_password, $stored_hash)); // 期待輸出 `true`
?>